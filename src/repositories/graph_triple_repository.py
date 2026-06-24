from __future__ import annotations

from typing import Any

from sqlalchemy import select

from src.storage.postgres.manager import pg_manager
from src.storage.postgres.models_knowledge import GraphTripleDraft
from src.utils.datetime_utils import utc_now_naive


class GraphTripleRepository:
    async def create_many(self, items: list[dict[str, Any]]) -> list[GraphTripleDraft]:
        async with pg_manager.get_async_session_context() as session:
            rows = [GraphTripleDraft(**item) for item in items]
            session.add_all(rows)
            await session.flush()
            return rows

    async def list(
        self, status: str | None = None, source_kind: str | None = None, limit: int = 100
    ) -> list[GraphTripleDraft]:
        async with pg_manager.get_async_session_context() as session:
            stmt = select(GraphTripleDraft).order_by(GraphTripleDraft.created_at.desc()).limit(limit)
            if status:
                stmt = stmt.where(GraphTripleDraft.status == status)
            if source_kind:
                stmt = stmt.where(GraphTripleDraft.source_kind == source_kind)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get(self, triple_id: str) -> GraphTripleDraft | None:
        async with pg_manager.get_async_session_context() as session:
            result = await session.execute(select(GraphTripleDraft).where(GraphTripleDraft.triple_id == triple_id))
            return result.scalar_one_or_none()

    async def update_status(
        self, triple_id: str, status: str, reviewed_by: str, review_comment: str | None = None
    ) -> GraphTripleDraft | None:
        async with pg_manager.get_async_session_context() as session:
            result = await session.execute(select(GraphTripleDraft).where(GraphTripleDraft.triple_id == triple_id))
            row = result.scalar_one_or_none()
            if not row:
                return None
            row.status = status
            row.reviewed_by = reviewed_by
            row.review_comment = review_comment
            row.updated_at = utc_now_naive()
            if status == "approved":
                row.approved_at = utc_now_naive()
            await session.flush()
            return row
