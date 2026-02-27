"""
MindWall — Analysis Repository
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Database repository for analysis records.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, desc, and_
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
