"""Snapshot manager integration with the analysis repository."""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from .repository import AnalysisRepository


class SnapshotManager:
    """High level entry point for analysis persistence."""

    def __init__(self, repository: AnalysisRepository | None = None) -> None:
        self._repository = repository or AnalysisRepository()

    async def save_analysis(
        self,
        snapshot_id: int,
        author: str,
        title: str,
        notes: str | None,
        items: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return await self._repository.create_analysis(snapshot_id, author, title, notes, items)

    async def list_snapshot_analysis(self, snapshot_id: Optional[int] = None) -> list[Dict[str, Any]]:
        return await self._repository.list_analysis(snapshot_id)

    @property
    def repository(self) -> AnalysisRepository:
        return self._repository
