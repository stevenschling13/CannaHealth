"""Simple data helpers for analysis persistence."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, List, Mapping, MutableMapping


@dataclass(slots=True)
class AnalysisItemRecord:
    """Lightweight representation of an analysis item."""

    id: int
    analysis_id: int
    label: str
    score: int
    payload: Mapping[str, Any] | None = None

    def serialize(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "analysis_id": self.analysis_id,
            "label": self.label,
            "score": self.score,
            "payload": dict(self.payload) if self.payload is not None else None,
        }


@dataclass(slots=True)
class AnalysisRecord:
    """In-memory analysis representation."""

    id: int
    snapshot_id: int
    author: str
    title: str
    notes: str | None
    created_at: datetime
    items: List[AnalysisItemRecord] = field(default_factory=list)

    def serialize(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "snapshot_id": self.snapshot_id,
            "author": self.author,
            "title": self.title,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "items": [item.serialize() for item in self.items],
        }


def build_analysis(
    *,
    analysis_id: int,
    snapshot_id: int,
    author: str,
    title: str,
    notes: str | None,
    created_at: datetime | None = None,
    items: Iterable[AnalysisItemRecord] | None = None,
) -> AnalysisRecord:
    """Create a new :class:`AnalysisRecord` with sane defaults."""

    record = AnalysisRecord(
        id=analysis_id,
        snapshot_id=snapshot_id,
        author=author,
        title=title,
        notes=notes,
        created_at=created_at or datetime.now(timezone.utc),
    )
    if items:
        record.items.extend(items)
    return record


def serialize_analysis(row: Mapping[str, Any] | AnalysisRecord) -> dict[str, Any]:
    if isinstance(row, AnalysisRecord):
        return row.serialize()
    data: MutableMapping[str, Any] = dict(row)
    created_at = data.get("created_at")
    if isinstance(created_at, datetime):
        data = dict(data)
        data["created_at"] = created_at.isoformat()
    if "items" in data:
        data["items"] = [serialize_analysis_item(item) for item in data["items"]]
    return dict(data)


def serialize_analysis_item(row: Mapping[str, Any] | AnalysisItemRecord) -> dict[str, Any]:
    if isinstance(row, AnalysisItemRecord):
        return row.serialize()
    payload = row.get("payload") if isinstance(row, Mapping) else None
    return {
        "id": row.get("id") if isinstance(row, Mapping) else None,
        "analysis_id": row.get("analysis_id") if isinstance(row, Mapping) else None,
        "label": row.get("label") if isinstance(row, Mapping) else None,
        "score": row.get("score") if isinstance(row, Mapping) else None,
        "payload": dict(payload) if isinstance(payload, Mapping) else payload,
    }
