"""Database schema helpers for analysis persistence."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.engine import Row, RowMapping

metadata = MetaData()

analysis_table = Table(
    "analysis",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("snapshot_id", Integer, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("author", String(length=255), nullable=False),
    Column("title", String(length=255), nullable=False),
    Column("notes", Text, nullable=True),
)

analysis_item_table = Table(
    "analysis_item",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("analysis_id", ForeignKey("analysis.id", ondelete="CASCADE"), nullable=False),
    Column("label", String(length=255), nullable=False),
    Column("score", Integer, nullable=False),
    Column("payload", JSON, nullable=True),
)

Index("ix_analysis_snapshot_id", analysis_table.c.snapshot_id)
Index("ix_analysis_item_analysis_id", analysis_item_table.c.analysis_id)


def _coerce_mapping(row: Mapping[str, Any] | RowMapping | Row | Any) -> Mapping[str, Any]:
    if isinstance(row, Row):
        return row._mapping
    if isinstance(row, RowMapping):
        return row
    if isinstance(row, Mapping):
        return row
    if hasattr(row, "_mapping"):
        return row._mapping  # type: ignore[return-value]
    return dict(row)


def _normalize_datetime(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def serialize_analysis(row: Mapping[str, Any] | RowMapping | Row | Any) -> dict[str, Any]:
    mapping = _coerce_mapping(row)
    return {
        "id": mapping.get("id"),
        "snapshot_id": mapping.get("snapshot_id"),
        "created_at": _normalize_datetime(mapping.get("created_at")),
        "author": mapping.get("author"),
        "title": mapping.get("title"),
        "notes": mapping.get("notes"),
    }


def serialize_analysis_item(row: Mapping[str, Any] | RowMapping | Row | Any) -> dict[str, Any]:
    mapping = _coerce_mapping(row)
    return {
        "id": mapping.get("id"),
        "analysis_id": mapping.get("analysis_id"),
        "label": mapping.get("label"),
        "score": mapping.get("score"),
        "payload": mapping.get("payload"),
    }
