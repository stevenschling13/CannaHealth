"""Repository helpers for persisting analysis snapshots using SQLAlchemy."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.models.analysis_schema import analysis_item_table, analysis_table, serialize_analysis, serialize_analysis_item


class AnalysisRepository:
    """Provide CRUD helpers for analysis entities."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @classmethod
    def from_engine(cls, engine: AsyncEngine) -> "AnalysisRepository":
        return cls(async_sessionmaker(engine, expire_on_commit=False))

    async def create_analysis(
        self,
        snapshot_id: int,
        author: str,
        title: str,
        notes: Optional[str],
        items: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    analysis_table.insert().values(
                        snapshot_id=snapshot_id,
                        author=author,
                        title=title,
                        notes=notes,
                    )
                )
                analysis_id = int(result.inserted_primary_key[0])
                item_payload = [
                    {
                        "analysis_id": analysis_id,
                        "label": item["label"],
                        "score": item["score"],
                        "payload": item.get("payload"),
                    }
                    for item in items
                ]
                if item_payload:
                    await session.execute(analysis_item_table.insert(), item_payload)
        return await self.get_analysis(analysis_id)

    async def get_analysis(self, analysis_id: int) -> Dict[str, Any]:
        async with self._session_factory() as session:
            analysis_stmt: Select[Any] = select(analysis_table).where(analysis_table.c.id == analysis_id)
            result = await session.execute(analysis_stmt)
            row = result.mappings().first()
            if row is None:
                raise KeyError(f"Analysis {analysis_id} not found")

            item_stmt: Select[Any] = select(analysis_item_table).where(
                analysis_item_table.c.analysis_id == analysis_id
            )
            item_result = await session.execute(item_stmt)
            items = [serialize_analysis_item(item) for item in item_result.mappings().all()]

        data = serialize_analysis(row)
        data["items"] = items
        return data

    async def list_analysis(self, snapshot_id: Optional[int] = None) -> List[Dict[str, Any]]:
        async with self._session_factory() as session:
            stmt: Select[Any] = select(analysis_table)
            if snapshot_id is not None:
                stmt = stmt.where(analysis_table.c.snapshot_id == snapshot_id)
            stmt = stmt.order_by(analysis_table.c.created_at.desc(), analysis_table.c.id.desc())
            result = await session.execute(stmt)
            rows = result.mappings().all()
        return [serialize_analysis(row) for row in rows]
