"""Repository helpers for persisting analysis snapshots."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.models.analysis_schema import (
    analysis_item_table,
    analysis_table,
    serialize_analysis,
    serialize_analysis_item,
)


class AnalysisRepository:
    """Simple repository wrapper around SQLAlchemy for analysis entities."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine
        self._session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            engine, expire_on_commit=False
        )

    async def create_analysis(
        self,
        snapshot_id: int,
        author: str,
        title: str,
        notes: Optional[str],
        items: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        async with self._session_factory() as session:
            result = await session.execute(
                analysis_table.insert().values(
                    snapshot_id=snapshot_id,
                    author=author,
                    title=title,
                    notes=notes,
                )
            )
            analysis_id = result.inserted_primary_key[0]
            if items:
                await session.execute(
                    analysis_item_table.insert(),
                    [
                        {
                            "analysis_id": analysis_id,
                            "label": item["label"],
                            "score": item["score"],
                            "payload": item.get("payload"),
                        }
                        for item in items
                    ],
                )
            await session.commit()

        return await self.get_analysis(analysis_id)

    async def get_analysis(self, analysis_id: int) -> Dict[str, Any]:
        async with self._session_factory() as session:
            analysis_row = await session.execute(
                select(analysis_table).where(analysis_table.c.id == analysis_id)
            )
            row = analysis_row.mappings().first()
            if row is None:
                raise KeyError(f"Analysis {analysis_id} not found")

            item_rows = await session.execute(
                select(analysis_item_table).where(analysis_item_table.c.analysis_id == analysis_id)
            )
            items = [serialize_analysis_item(item) for item in item_rows.mappings()]

        data = serialize_analysis(row)
        data["items"] = items
        return data

    async def list_analysis(self, snapshot_id: Optional[int] = None) -> List[Dict[str, Any]]:
        async with self._session_factory() as session:
            stmt = select(analysis_table)
            if snapshot_id is not None:
                stmt = stmt.where(analysis_table.c.snapshot_id == snapshot_id)
            rows = await session.execute(stmt.order_by(analysis_table.c.created_at.desc()))
        return [serialize_analysis(row) for row in rows.mappings()]
