"""
MindWall — Analysis Repository
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Database repository for analysis records.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, desc, and_, case
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..models import Analysis


class AnalysisRepository:
    """Repository for managing analysis records in the database."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def insert(
        self,
        message_uid: str,
        recipient_email: str,
        sender_email: str,
        sender_display_name: Optional[str],
        subject: Optional[str],
        received_at: Optional[datetime],
        channel: str,
        prefilter_triggered: bool,
        prefilter_signals: List[str],
        manipulation_score: float,
        dimension_scores: Dict[str, float],
        explanation: str,
        recommended_action: str,
        llm_raw_response: str,
        processing_time_ms: int,
    ) -> int:
        """Insert a new analysis record and return its ID."""
        async with self.session_factory() as session:
            analysis = Analysis(
                message_uid=message_uid,
                recipient_email=recipient_email,
                sender_email=sender_email,
                sender_display_name=sender_display_name,
                subject=subject,
                received_at=received_at,
                channel=channel,
                prefilter_triggered=prefilter_triggered,
                prefilter_signals=json.dumps(prefilter_signals),
                manipulation_score=manipulation_score,
                dimension_scores=json.dumps(dimension_scores),
                explanation=explanation,
                recommended_action=recommended_action,
                llm_raw_response=llm_raw_response,
                processing_time_ms=processing_time_ms,
            )
            session.add(analysis)
            await session.commit()
            await session.refresh(analysis)
            return analysis.id

    async def get_by_id(self, analysis_id: int) -> Optional[Analysis]:
        """Get an analysis by its ID."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Analysis).where(Analysis.id == analysis_id)
            )
            return result.scalar_one_or_none()

    async def get_recent_by_sender_recipient(
        self,
        recipient_email: str,
        sender_email: str,
        since: datetime,
    ) -> List[Analysis]:
        """Get recent analyses from a specific sender to a specific recipient."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Analysis)
                .where(
                    and_(
                        Analysis.recipient_email == recipient_email,
                        Analysis.sender_email == sender_email,
                        Analysis.analyzed_at >= since,
                    )
                )
                .order_by(Analysis.analyzed_at.asc())
            )
            return list(result.scalars().all())

    async def get_timeline(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Analysis]:
        """Get analysis timeline within a date range."""
        async with self.session_factory() as session:
            query = select(Analysis)
            conditions = []
            if start_date:
                conditions.append(Analysis.analyzed_at >= start_date)
            if end_date:
                conditions.append(Analysis.analyzed_at <= end_date)
            if conditions:
                query = query.where(and_(*conditions))
            query = query.order_by(desc(Analysis.analyzed_at)).limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def get_summary_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics for the dashboard."""
        async with self.session_factory() as session:
            # Total analyses
            total_result = await session.execute(
                select(func.count(Analysis.id))
            )
            total_count = total_result.scalar() or 0

            # Average score
            avg_result = await session.execute(
                select(func.avg(Analysis.manipulation_score))
            )
            avg_score = avg_result.scalar() or 0.0

            # High risk count (score >= 60)
            high_risk_result = await session.execute(
                select(func.count(Analysis.id)).where(Analysis.manipulation_score >= 60)
            )
            high_risk_count = high_risk_result.scalar() or 0

            # Critical count (score >= 80)
            critical_result = await session.execute(
                select(func.count(Analysis.id)).where(Analysis.manipulation_score >= 80)
            )
            critical_count = critical_result.scalar() or 0

            # Average processing time
            avg_time_result = await session.execute(
                select(func.avg(Analysis.processing_time_ms))
            )
            avg_processing_ms = avg_time_result.scalar() or 0

            return {
                "total_analyses": total_count,
                "average_score": round(float(avg_score), 2),
                "high_risk_count": high_risk_count,
                "critical_count": critical_count,
                "average_processing_ms": round(float(avg_processing_ms), 0),
            }

    async def get_email_counts_by_recipients(
        self,
        emails: List[str],
    ) -> Dict[str, Dict[str, int]]:
        """Get total and flagged analysis counts grouped by recipient email."""
        if not emails:
            return {}

        async with self.session_factory() as session:
            result = await session.execute(
                select(
                    Analysis.recipient_email,
                    func.count(Analysis.id).label("total"),
                    func.sum(
                        case(
                            (Analysis.manipulation_score >= 35, 1),
                            else_=0,
                        )
                    ).label("flagged"),
                )
                .where(Analysis.recipient_email.in_(emails))
                .group_by(Analysis.recipient_email)
            )
            return {
                row.recipient_email: {
                    "total": row.total,
                    "flagged": int(row.flagged or 0),
                }
                for row in result.all()
            }

    async def get_by_recipient(
        self,
        recipient_email: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Analysis]:
        """Get analyses for a specific recipient."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Analysis)
                .where(Analysis.recipient_email == recipient_email)
                .order_by(desc(Analysis.analyzed_at))
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())

    async def get_avg_dimension_scores(self) -> Dict[str, float]:
        """Compute average dimension scores across all analyses."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Analysis.dimension_scores)
                .where(Analysis.dimension_scores.isnot(None))
                .order_by(desc(Analysis.analyzed_at))
                .limit(500)
            )
            rows = result.scalars().all()

        if not rows:
            return {}

        totals: Dict[str, float] = {}
        counts: Dict[str, int] = {}
        for raw in rows:
            try:
                scores = json.loads(raw) if isinstance(raw, str) else raw
            except (json.JSONDecodeError, TypeError):
                continue
            if not isinstance(scores, dict):
                continue
            for key, val in scores.items():
                if isinstance(val, (int, float)):
                    totals[key] = totals.get(key, 0.0) + float(val)
                    counts[key] = counts.get(key, 0) + 1

        return {k: round(totals[k] / counts[k], 2) for k in totals if counts.get(k, 0) > 0}

    async def get_heatmap_data(
        self,
        days: int = 7,
        max_employees: int = 10,
    ) -> Dict[str, Any]:
        """Build employee × day heatmap of average manipulation scores."""
        since = datetime.utcnow() - timedelta(days=days)
        async with self.session_factory() as session:
            # Top recipients by volume
            top_result = await session.execute(
                select(
                    Analysis.recipient_email,
                    func.count(Analysis.id).label("cnt"),
                )
                .where(Analysis.analyzed_at >= since)
                .group_by(Analysis.recipient_email)
                .order_by(desc("cnt"))
                .limit(max_employees)
            )
            top_emails = [row.recipient_email for row in top_result.all()]

            if not top_emails:
                return {"data": [], "row_labels": [], "col_labels": []}

            result = await session.execute(
                select(Analysis)
                .where(
                    and_(
                        Analysis.analyzed_at >= since,
                        Analysis.recipient_email.in_(top_emails),
                    )
                )
            )
            analyses = list(result.scalars().all())

        # Build day labels
        col_labels = []
        for i in range(days):
            d = datetime.utcnow() - timedelta(days=days - 1 - i)
            col_labels.append(d.strftime("%b %d"))

        # Build grid
        row_labels = top_emails
        grid: List[List[Optional[float]]] = []
        for email in row_labels:
            row: List[Optional[float]] = []
            for i in range(days):
                day_start = (datetime.utcnow() - timedelta(days=days - 1 - i)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                day_end = day_start + timedelta(days=1)
                scores = [
                    a.manipulation_score
                    for a in analyses
                    if a.recipient_email == email
                    and a.manipulation_score is not None
                    and a.analyzed_at
                    and day_start <= a.analyzed_at < day_end
                ]
                row.append(round(sum(scores) / len(scores), 1) if scores else None)
            grid.append(row)

        return {"data": grid, "row_labels": row_labels, "col_labels": col_labels}

    async def get_timeline_aggregated(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        bucket_count: int = 20,
    ) -> List[Dict[str, Any]]:
        """Return aggregated time-bucket entries for the threat timeline chart."""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=7)
        if not end_date:
            end_date = datetime.utcnow()

        async with self.session_factory() as session:
            result = await session.execute(
                select(Analysis)
                .where(
                    and_(
                        Analysis.analyzed_at >= start_date,
                        Analysis.analyzed_at <= end_date,
                        Analysis.manipulation_score.isnot(None),
                    )
                )
                .order_by(Analysis.analyzed_at)
            )
            analyses = list(result.scalars().all())

        if not analyses:
            return []

        # Compute bucket boundaries
        total_seconds = (end_date - start_date).total_seconds()
        bucket_seconds = max(total_seconds / bucket_count, 1)

        buckets: Dict[int, List[float]] = {}
        for a in analyses:
            idx = int((a.analyzed_at - start_date).total_seconds() / bucket_seconds)
            idx = min(idx, bucket_count - 1)
            buckets.setdefault(idx, []).append(a.manipulation_score)

        entries = []
        for i in range(bucket_count):
            bucket_time = start_date + timedelta(seconds=i * bucket_seconds)
            scores = buckets.get(i, [])
            entries.append({
                "bucket": bucket_time,
                "avg_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
                "count": len(scores),
            })

        return entries
