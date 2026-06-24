from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.postgres.models_business import TrafficAuditCase


class TrafficAuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, case: TrafficAuditCase) -> TrafficAuditCase:
        self.db.add(case)
        await self.db.flush()
        return case

    async def get(self, case_id: str, department_id: int | None = None) -> TrafficAuditCase | None:
        stmt = select(TrafficAuditCase).where(TrafficAuditCase.id == case_id)
        if department_id is not None:
            stmt = stmt.where(TrafficAuditCase.department_id == department_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, department_id: int | None = None) -> list[TrafficAuditCase]:
        stmt = select(TrafficAuditCase)
        if department_id is not None:
            stmt = stmt.where(TrafficAuditCase.department_id == department_id)
        result = await self.db.execute(stmt.order_by(TrafficAuditCase.created_at.desc()))
        return list(result.scalars().all())

    async def save(self, case: TrafficAuditCase) -> TrafficAuditCase:
        await self.db.flush()
        return case
