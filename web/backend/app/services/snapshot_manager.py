"""Snapshot manager integration with the analysis repository."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable

from .repository import AnalysisRepository


class SnapshotManager:
    """High level entry point for analysis persistence."""

    def __init__(
        self,
        repository: AnalysisRepository | None = None,
        *,
        database: str | Path | None = None,
    ) -> None:
        self._repository = repository or AnalysisRepository(database)

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
