"""
MindWall — Baseline Repository
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Database repository for sender behavioral baselines.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..models import SenderBaseline


class BaselineRepository:
    """Repository for managing sender behavioral baselines."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def get_baseline(
        self,
        recipient_email: str,
        sender_email: str,
    ) -> Optional[SenderBaseline]:
        """Get the behavioral baseline for a sender-recipient pair."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(SenderBaseline).where(
                    and_(
                        SenderBaseline.recipient_email == recipient_email,
                        SenderBaseline.sender_email == sender_email,
                    )
                )
            )
            return result.scalar_one_or_none()

    async def upsert_baseline(
        self,
        recipient_email: str,
        sender_email: str,
        avg_word_count: float,
        avg_sentence_length: float,
        typical_hours: str,
        formality_score: float,
        sample_count: int,
    ) -> None:
        """Insert or update a sender behavioral baseline."""
        async with self.session_factory() as session:
            existing = await session.execute(
                select(SenderBaseline).where(
                    and_(
                        SenderBaseline.recipient_email == recipient_email,
                        SenderBaseline.sender_email == sender_email,
                    )
                )
            )
            baseline = existing.scalar_one_or_none()

            if baseline:
                baseline.avg_word_count = avg_word_count
                baseline.avg_sentence_length = avg_sentence_length
                baseline.typical_hours = typical_hours
                baseline.formality_score = formality_score
                baseline.sample_count = sample_count
                baseline.last_updated = datetime.utcnow()
            else:
                baseline = SenderBaseline(
                    recipient_email=recipient_email,
                    sender_email=sender_email,
                    avg_word_count=avg_word_count,
                    avg_sentence_length=avg_sentence_length,
                    typical_hours=typical_hours,
                    formality_score=formality_score,
                    sample_count=sample_count,
                )
                session.add(baseline)

            await session.commit()

    async def get_baselines_for_recipient(
        self,
        recipient_email: str,
    ) -> List[SenderBaseline]:
        """Get all sender baselines for a specific recipient."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(SenderBaseline)
                .where(SenderBaseline.recipient_email == recipient_email)
                .order_by(SenderBaseline.last_updated.desc())
            )
            return list(result.scalars().all())
