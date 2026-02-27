"""
MindWall — Analysis Pipeline Orchestrator
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Orchestrates the full email analysis pipeline: pre-filter → baseline lookup →
deviation scoring → LLM analysis → score aggregation → alert generation.
"""

import time
import json
import asyncio
from datetime import datetime, timezone

import structlog

from .prefilter import PreFilter
from .llm_client import OllamaClient, OllamaClientError
from .prompt_builder import build_analysis_prompt, SYSTEM_PROMPT
from .scorer import ScoreAggregator
from .behavioral.baseline import BaselineEngine
from .behavioral.deviation import DeviationScorer
from ..db.repositories.analysis_repo import AnalysisRepository
from ..db.repositories.alert_repo import AlertRepository
from ..db.repositories.baseline_repo import BaselineRepository
from ..websocket.manager import WebSocketManager
from ..schemas.analyze import AnalyzeRequest, AnalyzeResponse

logger = structlog.get_logger(__name__)


class AnalysisPipeline:
    """
    Full 10-stage analysis pipeline orchestrator.
    Processes incoming emails through rule-based pre-filtering, behavioral
    baseline comparison, LLM inference, and score aggregation.
    """

    def __init__(
        self,
        llm: OllamaClient,
        analysis_repo: AnalysisRepository,
        alert_repo: AlertRepository,
        baseline_repo: BaselineRepository,
        ws_manager: WebSocketManager,
    ):
        self.prefilter = PreFilter()
        self.llm = llm
        self.aggregator = ScoreAggregator()
        self.baseline_engine = BaselineEngine(baseline_repo)
        self.deviation_scorer = DeviationScorer()
        self.analysis_repo = analysis_repo
        self.alert_repo = alert_repo
        self.ws_manager = ws_manager

    async def run(self, request: AnalyzeRequest) -> AnalyzeResponse:
        """
        Execute the full analysis pipeline on an incoming email.

        Args:
            request: AnalyzeRequest containing email content and metadata.

        Returns:
            AnalyzeResponse with scores, explanation, and recommended action.
        """
        start_time = time.monotonic()
        logger.info(
            "pipeline.start",
            message_uid=request.message_uid,
            sender=request.sender_email,
            recipient=request.recipient_email,
            channel=request.channel,
        )

        # Stage 1: Rule-based prefilter (no GPU, <5ms)
        prefilter_result = self.prefilter.evaluate(
            subject=request.subject,
            body=request.body,
            sender_email=request.sender_email,
            received_at=request.received_at,
        )

        # Stage 2: Load sender behavioral baseline
        baseline = await self.baseline_engine.get_baseline(
            recipient_email=request.recipient_email,
            sender_email=request.sender_email,
        )

        # Stage 3: Compute behavioral deviation scores
        deviation_context = self.deviation_scorer.score(
            body=request.body,
            received_at=request.received_at,
            baseline=baseline,
        )

        # Add word count deviation info to baseline for prompt context
        if baseline is not None:
            current_wc = len(request.body.split())
            baseline_wc = baseline.get("avg_word_count", 0)
            if baseline_wc > 0:
                deviation_pct = ((current_wc - baseline_wc) / baseline_wc) * 100
                baseline["word_count_deviation"] = f"{deviation_pct:+.0f}%"

        # Stage 4: Build prompt and call LLM
        received_hour = (
            request.received_at.hour
            if request.received_at
            else datetime.now(timezone.utc).hour
        )

        prompt = build_analysis_prompt(
            email_body=request.body,
            sender_email=request.sender_email,
            sender_display_name=request.sender_display_name,
            subject=request.subject,
            received_hour=received_hour,
            baseline=baseline,
            prefilter_signals=prefilter_result.signals,
        )

        try:
            llm_response_raw = await self.llm.generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=prompt,
            )
            llm_data = json.loads(llm_response_raw)
        except (OllamaClientError, json.JSONDecodeError) as e:
            logger.error("pipeline.llm_error", error=str(e), message_uid=request.message_uid)
            # Fallback: use prefilter scores only
            llm_data = self._fallback_scores(prefilter_result)
            llm_response_raw = json.dumps(llm_data)

        # Validate LLM response structure
        llm_data = self._validate_llm_response(llm_data)

        # Stage 5: Merge LLM scores with behavioral deviation scores
        final_scores = self.aggregator.merge(
            llm_dimension_scores=llm_data["dimension_scores"],
            behavioral_deviation_score=deviation_context.deviation_score,
        )
        aggregate_score = self.aggregator.compute_aggregate(final_scores)

        # Apply prefilter score boost
        if prefilter_result.score_boost > 0:
            aggregate_score = min(100.0, aggregate_score + prefilter_result.score_boost)
            aggregate_score = round(aggregate_score, 2)

        # Stage 6: Determine severity
        severity = self._severity(aggregate_score)

        processing_ms = int((time.monotonic() - start_time) * 1000)

        # Stage 7: Persist analysis record
        analysis_id = await self.analysis_repo.insert(
            message_uid=request.message_uid,
            recipient_email=request.recipient_email,
            sender_email=request.sender_email,
            sender_display_name=request.sender_display_name,
            subject=request.subject,
            received_at=request.received_at,
            channel=request.channel,
            prefilter_triggered=prefilter_result.triggered,
            prefilter_signals=prefilter_result.signals,
            manipulation_score=aggregate_score,
            dimension_scores=final_scores,
            explanation=llm_data.get("explanation", ""),
            recommended_action=llm_data.get("recommended_action", "proceed"),
            llm_raw_response=llm_response_raw,
            processing_time_ms=processing_ms,
        )

        # Stage 8: Create alert if above threshold
        if aggregate_score >= 35:
            alert_id = await self.alert_repo.insert(
                analysis_id=analysis_id,
                severity=severity,
            )
            # Stage 9: Push real-time alert to dashboard
            await self.ws_manager.broadcast({
                "event": "new_alert",
                "alert_id": alert_id,
                "analysis_id": analysis_id,
                "recipient_email": request.recipient_email,
                "sender_email": request.sender_email,
                "subject": request.subject,
                "manipulation_score": aggregate_score,
                "severity": severity,
                "explanation": llm_data.get("explanation", ""),
                "recommended_action": llm_data.get("recommended_action", "proceed"),
                "dimension_scores": final_scores,
            })

        # Stage 10: Update sender baseline asynchronously
        asyncio.create_task(
            self.baseline_engine.update_baseline(
                recipient_email=request.recipient_email,
                sender_email=request.sender_email,
                body=request.body,
                received_at=request.received_at,
            )
        )

        logger.info(
            "pipeline.complete",
            message_uid=request.message_uid,
            aggregate_score=aggregate_score,
            severity=severity,
            processing_ms=processing_ms,
            prefilter_triggered=prefilter_result.triggered,
        )

        return AnalyzeResponse(
            analysis_id=analysis_id,
            manipulation_score=aggregate_score,
            severity=severity,
            explanation=llm_data.get("explanation", ""),
            recommended_action=llm_data.get("recommended_action", "proceed"),
            dimension_scores=final_scores,
            processing_time_ms=processing_ms,
        )

    @staticmethod
    def _severity(score: float) -> str:
        """Determine alert severity from aggregate manipulation score."""
        if score >= 80:
            return "critical"
        if score >= 60:
            return "high"
        if score >= 35:
            return "medium"
        return "low"

    @staticmethod
    def _validate_llm_response(llm_data: dict) -> dict:
        """Validate and sanitize LLM response structure."""
        if "dimension_scores" not in llm_data:
            llm_data["dimension_scores"] = {}

        # Ensure all dimension keys exist
        expected_dims = [
            "artificial_urgency", "authority_impersonation", "fear_threat_induction",
            "reciprocity_exploitation", "scarcity_tactics", "social_proof_manipulation",
            "sender_behavioral_deviation", "cross_channel_coordination",
            "emotional_escalation", "request_context_mismatch",
            "unusual_action_requested", "timing_anomaly",
        ]
        for dim in expected_dims:
            if dim not in llm_data["dimension_scores"]:
                llm_data["dimension_scores"][dim] = 0.0
            else:
                try:
                    llm_data["dimension_scores"][dim] = float(llm_data["dimension_scores"][dim])
                except (ValueError, TypeError):
                    llm_data["dimension_scores"][dim] = 0.0

        # Validate other fields
        if "explanation" not in llm_data:
            llm_data["explanation"] = "Analysis completed."
        if "recommended_action" not in llm_data:
            llm_data["recommended_action"] = "proceed"
        if llm_data["recommended_action"] not in ("proceed", "verify", "block"):
            llm_data["recommended_action"] = "verify"

        return llm_data

    @staticmethod
    def _fallback_scores(prefilter_result) -> dict:
        """Generate fallback scores when LLM is unavailable."""
        scores = {
            "artificial_urgency": 0,
            "authority_impersonation": 0,
            "fear_threat_induction": 0,
            "reciprocity_exploitation": 0,
            "scarcity_tactics": 0,
            "social_proof_manipulation": 0,
            "sender_behavioral_deviation": 0,
            "cross_channel_coordination": 0,
            "emotional_escalation": 0,
            "request_context_mismatch": 0,
            "unusual_action_requested": 0,
            "timing_anomaly": 0,
        }

        # Map prefilter signals to dimension scores
        signal_mapping = {
            "urgency_language_detected": ("artificial_urgency", 40),
            "authority_reference_detected": ("authority_impersonation", 45),
            "fear_threat_language_detected": ("fear_threat_induction", 40),
            "emotional_manipulation_detected": ("emotional_escalation", 35),
            "spoofed_sender_pattern": ("authority_impersonation", 60),
            "all_caps_subject": ("emotional_escalation", 20),
        }

        for signal in prefilter_result.signals:
            # Handle parameterized signals
            base_signal = signal.split("(")[0]
            if base_signal in signal_mapping:
                dim, value = signal_mapping[base_signal]
                scores[dim] = max(scores[dim], value)
            elif base_signal == "suspicious_request_detected":
                scores["unusual_action_requested"] = 50

        return {
            "dimension_scores": scores,
            "explanation": "Analysis based on rule-based pre-filter (LLM unavailable).",
            "recommended_action": "verify" if prefilter_result.triggered else "proceed",
            "confidence": 30,
        }
