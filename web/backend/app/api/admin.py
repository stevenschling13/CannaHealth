"""Lightweight admin service exposing analysis helpers."""
from __future__ import annotations

"""Lightweight admin service exposing analysis helpers."""

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from app.services.repository import AnalysisRepository


@dataclass
class AnalysisItemPayload:
    label: str
    score: int
    payload: Optional[dict[str, Any]] = None

    def to_record(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "score": int(self.score),
            "payload": self.payload,
        }


@dataclass
class AnalysisPayload:
    snapshot_id: int
    author: str
    title: str
    notes: Optional[str] = None
    items: list[AnalysisItemPayload] = field(default_factory=list)

    def to_records(self) -> Iterable[dict[str, Any]]:
        for item in self.items:
            yield item.to_record()


class AdminService:
    """Facade used by HTTP layers or scripts to interact with the repository."""

    def __init__(self, repository: AnalysisRepository | None = None) -> None:
        self._repository = repository or AnalysisRepository()

    async def list_analysis(self, snapshot_id: Optional[int] = None) -> list[dict[str, Any]]:
        return await self._repository.list_analysis(snapshot_id)

    async def create_analysis(self, payload: AnalysisPayload) -> dict[str, Any]:
        return await self._repository.create_analysis(
            snapshot_id=payload.snapshot_id,
            author=payload.author,
            title=payload.title,
            notes=payload.notes,
            items=list(payload.to_records()),
        )

    @property
    def repository(self) -> AnalysisRepository:
        return self._repository


__all__ = [
    "AdminService",
    "AnalysisPayload",
    "AnalysisItemPayload",
]
