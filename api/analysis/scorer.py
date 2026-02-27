"""
MindWall — 12-Dimension Score Aggregator
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Parses LLM dimension scores, merges with behavioral deviation data,
and computes a weighted aggregate manipulation score.
"""

import structlog
from typing import Dict

from .dimensions import Dimension, DIMENSION_WEIGHTS

logger = structlog.get_logger(__name__)


class ScoreAggregator:
    """
    Aggregates 12-dimension manipulation scores from the LLM with
    behavioral deviation data into a single weighted risk score.
    """

    VALID_DIMENSIONS = {d.value for d in Dimension}

    def merge(
        self,
        llm_dimension_scores: Dict[str, float],
        behavioral_deviation_score: float,
    ) -> Dict[str, float]:
        """
        Merge LLM-generated dimension scores with behavioral deviation score.

        Args:
            llm_dimension_scores: Raw dimension scores from LLM (0-100 each).
            behavioral_deviation_score: Deviation score computed from baseline engine.

        Returns:
            Final merged dimension scores dictionary.
        """
        final_scores: Dict[str, float] = {}

        for dim_name in self.VALID_DIMENSIONS:
            raw_score = llm_dimension_scores.get(dim_name, 0.0)
            # Clamp to valid range
            final_scores[dim_name] = max(0.0, min(100.0, float(raw_score)))

        # Override sender_behavioral_deviation with computed value if available
        if behavioral_deviation_score is not None and behavioral_deviation_score > 0:
            # Weighted blend: 60% behavioral engine, 40% LLM assessment
            llm_deviation = final_scores.get(Dimension.SENDER_BEHAVIORAL_DEVIATION.value, 0.0)
            blended = (behavioral_deviation_score * 0.6) + (llm_deviation * 0.4)
            final_scores[Dimension.SENDER_BEHAVIORAL_DEVIATION.value] = min(100.0, blended)

        return final_scores

    def compute_aggregate(self, dimension_scores: Dict[str, float]) -> float:
        """
        Compute the weighted aggregate manipulation score (0-100).

        Uses the dimension weights defined in dimensions.py to produce
        a single overall risk score.

        Args:
            dimension_scores: Dictionary of dimension name -> score (0-100).

        Returns:
            Weighted aggregate score (0-100).
        """
        aggregate = 0.0

        for dimension in Dimension:
            score = dimension_scores.get(dimension.value, 0.0)
            weight = DIMENSION_WEIGHTS.get(dimension, 0.0)
            aggregate += score * weight

        # Clamp to 0-100
        aggregate = max(0.0, min(100.0, aggregate))

        logger.debug(
            "scorer.aggregate",
            aggregate_score=round(aggregate, 2),
            dimension_count=len(dimension_scores),
        )

        return round(aggregate, 2)
