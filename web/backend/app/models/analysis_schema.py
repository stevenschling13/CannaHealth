"""Schema helpers for analysis-related persistence."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

try:  # pragma: no cover - optional dependency branch
    from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, MetaData, String, Table, Text
except ModuleNotFoundError:  # pragma: no cover - offline fallback
    JSON = Column = DateTime = ForeignKey = Integer = MetaData = String = Table = Text = None  # type: ignore[assignment]
    metadata = None
    analysis_table = None
    analysis_item_table = None
else:
    metadata = MetaData()

    analysis_table = Table(
        "analysis",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("snapshot_id", Integer, nullable=False, index=True),
        Column("created_at", DateTime, default=datetime.utcnow, nullable=False),
        Column("author", String(length=255), nullable=False),
        Column("title", String(length=255), nullable=False),
        Column("notes", Text, nullable=True),
    )

    analysis_item_table = Table(
        "analysis_item",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("analysis_id", ForeignKey("analysis.id", ondelete="CASCADE"), nullable=False, index=True),
        Column("label", String(length=255), nullable=False),
        Column("score", Integer, nullable=False),
        Column("payload", JSON, nullable=True),
    )


def _normalize_row(row: Dict[str, Any] | Any, *, item: bool = False) -> Dict[str, Any]:
    if isinstance(row, dict):
        source = row
    else:  # sqlite3.Row or other mapping like objects
        source = dict(row)
    if item:
        return {
            "id": source.get("id"),
            "analysis_id": source.get("analysis_id"),
            "label": source.get("label"),
            "score": source.get("score"),
            "payload": source.get("payload"),
        }
    return {
        "id": source.get("id"),
        "snapshot_id": source.get("snapshot_id"),
        "created_at": source.get("created_at"),
        "author": source.get("author"),
        "title": source.get("title"),
        "notes": source.get("notes"),
    }


def serialize_analysis(row: Dict[str, Any] | Any) -> Dict[str, Any]:
    """Serialize an analysis row into a JSON compatible dictionary."""
    return _normalize_row(row)


def serialize_analysis_item(row: Dict[str, Any] | Any) -> Dict[str, Any]:
    """Serialize an analysis item row into a JSON compatible dictionary."""
    return _normalize_row(row, item=True)
