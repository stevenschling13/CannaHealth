"""Snapshot manager integration with the analysis repository."""
from __future__ import annotations

from typing import Any, Dict, Iterable

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from .repository import AnalysisRepository


class SnapshotManager:
    """High level entry point for analysis persistence."""

    def __init__(self, repository: AnalysisRepository) -> None:
        self._repository = repository

    @classmethod
    def from_engine(cls, engine: AsyncEngine) -> "SnapshotManager":
        return cls(AnalysisRepository.from_engine(engine))

    @classmethod
    def from_session_factory(
        cls, session_factory: async_sessionmaker[AsyncSession]
    ) -> "SnapshotManager":
        return cls(AnalysisRepository(session_factory))

    async def save_analysis(
        self,
        snapshot_id: int,
        author: str,
        title: str,
        notes: str | None,
        items: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return await self._repository.create_analysis(snapshot_id, author, title, notes, items)

    async def list_snapshot_analysis(self, snapshot_id: int | None = None) -> list[Dict[str, Any]]:
        return await self._repository.list_analysis(snapshot_id)
