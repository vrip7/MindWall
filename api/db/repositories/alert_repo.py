"""
MindWall — Alert Repository
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Database repository for alert management.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, desc, and_, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from ..models import Alert, Analysis


class AlertRepository:
    """Repository for managing alerts in the database."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def insert(self, analysis_id: int, severity: str) -> int:
        """Create a new alert and return its ID."""
        async with self.session_factory() as session:
            alert = Alert(
                analysis_id=analysis_id,
                severity=severity,
            )
            session.add(alert)
            await session.commit()
            await session.refresh(alert)
            return alert.id

    async def get_by_id(self, alert_id: int) -> Optional[Alert]:
        """Get an alert by ID with its associated analysis."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Alert)
                .options(selectinload(Alert.analysis))
                .where(Alert.id == alert_id)
            )
            return result.scalar_one_or_none()

    async def get_paginated(
        self,
        severity: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get paginated alerts with optional filters."""
        async with self.session_factory() as session:
            query = select(Alert).options(selectinload(Alert.analysis))
            count_query = select(func.count(Alert.id))

            conditions = []
            if severity:
                conditions.append(Alert.severity == severity)
            if acknowledged is not None:
                conditions.append(Alert.acknowledged == acknowledged)

            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))

            # Get total count
            total_result = await session.execute(count_query)
            total = total_result.scalar() or 0

            # Get page
            query = query.order_by(desc(Alert.created_at)).limit(limit).offset(offset)
            result = await session.execute(query)
            alerts = list(result.scalars().all())

            return {
                "items": alerts,
                "total": total,
                "limit": limit,
                "offset": offset,
            }

    async def acknowledge(
        self,
        alert_id: int,
        acknowledged_by: str,
    ) -> Optional[Alert]:
        """Mark an alert as acknowledged."""
        async with self.session_factory() as session:
            result = await session.execute(
                update(Alert)
                .where(Alert.id == alert_id)
                .values(
                    acknowledged=True,
                    acknowledged_by=acknowledged_by,
                    acknowledged_at=datetime.utcnow(),
                )
                .returning(Alert)
            )
            await session.commit()
            row = result.scalar_one_or_none()
            if row:
                await session.refresh(row)
            return row

    async def get_unacknowledged_count(self) -> Dict[str, int]:
        """Get count of unacknowledged alerts by severity."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Alert.severity, func.count(Alert.id))
                .where(Alert.acknowledged == False)
                .group_by(Alert.severity)
            )
            counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
            for severity, count in result.all():
                counts[severity] = count
            return counts
