"""
MindWall — Settings Repository
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Database repository for persistent system settings.
"""

from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..models import SystemSetting


class SettingsRepository:
    """Repository for managing system settings in the database."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def get_all(self) -> Dict[str, str]:
        """Return all settings as a key-value dict."""
        async with self.session_factory() as session:
            result = await session.execute(select(SystemSetting))
            rows = result.scalars().all()
            return {row.key: row.value for row in rows}

    async def get(self, key: str) -> Optional[str]:
        """Get a single setting by key."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(SystemSetting).where(SystemSetting.key == key)
            )
            row = result.scalar_one_or_none()
            return row.value if row else None

    async def set(self, key: str, value: str) -> None:
        """Upsert a single setting."""
        async with self.session_factory() as session:
            existing = await session.execute(
                select(SystemSetting).where(SystemSetting.key == key)
            )
            row = existing.scalar_one_or_none()
            if row:
                row.value = value
                row.updated_at = datetime.utcnow()
            else:
                session.add(SystemSetting(key=key, value=value))
            await session.commit()

    async def set_many(self, settings: Dict[str, str]) -> None:
        """Upsert multiple settings at once."""
        async with self.session_factory() as session:
            for key, value in settings.items():
                existing = await session.execute(
                    select(SystemSetting).where(SystemSetting.key == key)
                )
                row = existing.scalar_one_or_none()
                if row:
                    row.value = value
                    row.updated_at = datetime.utcnow()
                else:
                    session.add(SystemSetting(key=key, value=value))
            await session.commit()
