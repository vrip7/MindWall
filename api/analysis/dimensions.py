"""
MindWall — 12 Manipulation Dimensions
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Defines the 12-dimensional manipulation scoring framework used by the analysis engine.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class Dimension(Enum):
    """Enumeration of the 12 psychological manipulation dimensions."""
    ARTIFICIAL_URGENCY = "artificial_urgency"
    AUTHORITY_IMPERSONATION = "authority_impersonation"
    FEAR_THREAT_INDUCTION = "fear_threat_induction"
    RECIPROCITY_EXPLOITATION = "reciprocity_exploitation"
    SCARCITY_TACTICS = "scarcity_tactics"
    SOCIAL_PROOF_MANIPULATION = "social_proof_manipulation"
    SENDER_BEHAVIORAL_DEVIATION = "sender_behavioral_deviation"
    CROSS_CHANNEL_COORDINATION = "cross_channel_coordination"
    EMOTIONAL_ESCALATION = "emotional_escalation"
    REQUEST_CONTEXT_MISMATCH = "request_context_mismatch"
    UNUSUAL_ACTION_REQUESTED = "unusual_action_requested"
    TIMING_ANOMALY = "timing_anomaly"


DIMENSION_WEIGHTS: Dict[Dimension, float] = {
    Dimension.ARTIFICIAL_URGENCY: 0.12,
    Dimension.AUTHORITY_IMPERSONATION: 0.15,
    Dimension.FEAR_THREAT_INDUCTION: 0.12,
    Dimension.RECIPROCITY_EXPLOITATION: 0.07,
    Dimension.SCARCITY_TACTICS: 0.07,
    Dimension.SOCIAL_PROOF_MANIPULATION: 0.06,
    Dimension.SENDER_BEHAVIORAL_DEVIATION: 0.12,
    Dimension.CROSS_CHANNEL_COORDINATION: 0.08,
    Dimension.EMOTIONAL_ESCALATION: 0.07,
    Dimension.REQUEST_CONTEXT_MISMATCH: 0.06,
    Dimension.UNUSUAL_ACTION_REQUESTED: 0.05,
    Dimension.TIMING_ANOMALY: 0.03,
}


@dataclass
class DimensionInfo:
    """Metadata about a manipulation dimension."""
    dimension: Dimension
    name: str
    description: str
    weight: float


DIMENSION_REGISTRY: list[DimensionInfo] = [
    DimensionInfo(
        dimension=Dimension.ARTIFICIAL_URGENCY,
        name="Artificial Urgency",
        description="Manufactured time pressure or deadline designed to rush decision-making",
        weight=DIMENSION_WEIGHTS[Dimension.ARTIFICIAL_URGENCY],
    ),
    DimensionInfo(
        dimension=Dimension.AUTHORITY_IMPERSONATION,
        name="Authority Impersonation",
        description="Falsely claiming or implying authority, rank, or official capacity",
        weight=DIMENSION_WEIGHTS[Dimension.AUTHORITY_IMPERSONATION],
    ),
    DimensionInfo(
        dimension=Dimension.FEAR_THREAT_INDUCTION,
        name="Fear/Threat Induction",
        description="Using threats, consequences, or fear to compel action",
        weight=DIMENSION_WEIGHTS[Dimension.FEAR_THREAT_INDUCTION],
    ),
    DimensionInfo(
        dimension=Dimension.RECIPROCITY_EXPLOITATION,
        name="Reciprocity Exploitation",
        description="Leveraging past favors, gifts, or obligations to compel compliance",
        weight=DIMENSION_WEIGHTS[Dimension.RECIPROCITY_EXPLOITATION],
    ),
    DimensionInfo(
        dimension=Dimension.SCARCITY_TACTICS,
        name="Scarcity Tactics",
        description="Creating false scarcity of time, resource, or opportunity",
        weight=DIMENSION_WEIGHTS[Dimension.SCARCITY_TACTICS],
    ),
    DimensionInfo(
        dimension=Dimension.SOCIAL_PROOF_MANIPULATION,
        name="Social Proof Manipulation",
        description="Fabricating consensus, peer behavior, or social validation",
        weight=DIMENSION_WEIGHTS[Dimension.SOCIAL_PROOF_MANIPULATION],
    ),
    DimensionInfo(
        dimension=Dimension.SENDER_BEHAVIORAL_DEVIATION,
        name="Sender Behavioral Deviation",
        description="Deviation from this sender's typical communication patterns",
        weight=DIMENSION_WEIGHTS[Dimension.SENDER_BEHAVIORAL_DEVIATION],
    ),
    DimensionInfo(
        dimension=Dimension.CROSS_CHANNEL_COORDINATION,
        name="Cross-Channel Coordination",
        description="Evidence of coordinated multi-channel social engineering attack",
        weight=DIMENSION_WEIGHTS[Dimension.CROSS_CHANNEL_COORDINATION],
    ),
    DimensionInfo(
        dimension=Dimension.EMOTIONAL_ESCALATION,
        name="Emotional Escalation",
        description="Escalating emotional intensity to override rational thinking",
        weight=DIMENSION_WEIGHTS[Dimension.EMOTIONAL_ESCALATION],
    ),
    DimensionInfo(
        dimension=Dimension.REQUEST_CONTEXT_MISMATCH,
        name="Request/Context Mismatch",
        description="The request is inconsistent with the stated context or relationship",
        weight=DIMENSION_WEIGHTS[Dimension.REQUEST_CONTEXT_MISMATCH],
    ),
    DimensionInfo(
        dimension=Dimension.UNUSUAL_ACTION_REQUESTED,
        name="Unusual Action Requested",
        description="Requesting actions atypical for legitimate business communication",
        weight=DIMENSION_WEIGHTS[Dimension.UNUSUAL_ACTION_REQUESTED],
    ),
    DimensionInfo(
        dimension=Dimension.TIMING_ANOMALY,
        name="Timing Anomaly",
        description="Suspicious timing relative to sender's typical communication patterns",
        weight=DIMENSION_WEIGHTS[Dimension.TIMING_ANOMALY],
    ),
]
