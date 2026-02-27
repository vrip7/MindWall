"""
MindWall — Employee Repository
Developed by Pradyumn Tandon (https://pradyumntandon.com) at VRIP7 (https://vrip7.com)

Database repository for employee management and risk tracking.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, desc, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..models import Employee, Analysis


class EmployeeRepository:
    """Repository for managing employee records and risk profiles."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def get_or_create(self, email: str, display_name: Optional[str] = None) -> Employee:
        """Get an employee by email, or create if not exists."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Employee).where(Employee.email == email)
            )
            employee = result.scalar_one_or_none()

            if employee is None:
                employee = Employee(
                    email=email,
                    display_name=display_name,
                )
                session.add(employee)
                await session.commit()
                await session.refresh(employee)

            return employee

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        sort_by_risk: bool = True,
    ) -> Dict[str, Any]:
        """Get paginated employee list."""
        async with self.session_factory() as session:
            count_result = await session.execute(select(func.count(Employee.id)))
            total = count_result.scalar() or 0

            query = select(Employee)
            if sort_by_risk:
                query = query.order_by(desc(Employee.risk_score))
            else:
                query = query.order_by(Employee.display_name)
            query = query.limit(limit).offset(offset)

            result = await session.execute(query)
            employees = list(result.scalars().all())

            return {
                "items": employees,
                "total": total,
                "limit": limit,
                "offset": offset,
            }

    async def update_risk_score(self, email: str, risk_score: float) -> None:
        """Update an employee's rolling risk score."""
        async with self.session_factory() as session:
            await session.execute(
                update(Employee)
                .where(Employee.email == email)
                .values(risk_score=round(risk_score, 2), updated_at=datetime.utcnow())
            )
            await session.commit()

    async def get_risk_profile(self, email: str) -> Optional[Dict[str, Any]]:
        """Get full risk profile for an employee including recent analyses."""
        async with self.session_factory() as session:
            # Get employee
            emp_result = await session.execute(
                select(Employee).where(Employee.email == email)
            )
            employee = emp_result.scalar_one_or_none()
            if not employee:
                return None

            # Get recent analyses targeting this employee
            analyses_result = await session.execute(
                select(Analysis)
                .where(Analysis.recipient_email == email)
                .order_by(desc(Analysis.analyzed_at))
                .limit(50)
            )
            recent_analyses = list(analyses_result.scalars().all())

            # Compute rolling 30-day risk score
            import json
            from datetime import timedelta
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_scores = [
                a.manipulation_score
                for a in recent_analyses
                if a.manipulation_score is not None and a.analyzed_at and a.analyzed_at >= thirty_days_ago
            ]

            rolling_risk = 0.0
            if recent_scores:
                # Weighted: higher scores have more influence
                rolling_risk = sum(s ** 1.5 for s in recent_scores) / (len(recent_scores) * (100 ** 0.5))
                rolling_risk = min(100.0, rolling_risk)

            # Update employee risk score
            employee.risk_score = round(rolling_risk, 2)
            employee.updated_at = datetime.utcnow()
            await session.commit()

            # Get top senders by threat level
            top_senders_result = await session.execute(
                select(
                    Analysis.sender_email,
                    func.avg(Analysis.manipulation_score).label("avg_score"),
                    func.count(Analysis.id).label("count"),
                )
                .where(Analysis.recipient_email == email)
                .group_by(Analysis.sender_email)
                .order_by(desc("avg_score"))
                .limit(10)
            )
            top_senders = [
                {
                    "sender_email": row.sender_email,
                    "avg_score": round(float(row.avg_score), 2),
                    "count": row.count,
                }
                for row in top_senders_result.all()
            ]

            return {
                "employee": employee,
                "rolling_risk_score": round(rolling_risk, 2),
                "total_analyses": len(recent_analyses),
                "recent_analyses": recent_analyses[:10],
                "top_threat_senders": top_senders,
            }

    async def create_employee(
        self,
        email: str,
        display_name: Optional[str] = None,
        department: Optional[str] = None,
    ) -> Employee:
        """Create a new employee record."""
        async with self.session_factory() as session:
            employee = Employee(
                email=email,
                display_name=display_name,
                department=department,
            )
            session.add(employee)
            await session.commit()
            await session.refresh(employee)
            return employee
