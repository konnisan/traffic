from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.postgres.models_business import DifyWorkflowRun


class DifyWorkflowRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, run: DifyWorkflowRun) -> DifyWorkflowRun:
        self.db.add(run)
        await self.db.flush()
        return run

    async def get(self, run_id: str, department_id: int | None = None) -> DifyWorkflowRun | None:
        stmt = select(DifyWorkflowRun).where(DifyWorkflowRun.id == run_id)
        if department_id is not None:
            stmt = stmt.where(DifyWorkflowRun.department_id == department_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_case(self, case_id: str, department_id: int | None = None) -> list[DifyWorkflowRun]:
        stmt = select(DifyWorkflowRun).where(DifyWorkflowRun.case_id == case_id)
        if department_id is not None:
            stmt = stmt.where(DifyWorkflowRun.department_id == department_id)
        result = await self.db.execute(stmt.order_by(DifyWorkflowRun.created_at.desc()))
        return list(result.scalars().all())

    async def save(self, run: DifyWorkflowRun) -> DifyWorkflowRun:
        await self.db.flush()
        return run
