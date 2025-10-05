"""SQLAlchemy schema definitions for analysis-related tables."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, MetaData, String, Table, Text

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


def serialize_analysis(row: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize an analysis row into a JSON compatible dictionary."""
    return {
        "id": row.get("id"),
        "snapshot_id": row.get("snapshot_id"),
        "created_at": row.get("created_at"),
        "author": row.get("author"),
        "title": row.get("title"),
        "notes": row.get("notes"),
    }


def serialize_analysis_item(row: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize an analysis item row into a JSON compatible dictionary."""
    return {
        "id": row.get("id"),
        "analysis_id": row.get("analysis_id"),
        "label": row.get("label"),
        "score": row.get("score"),
        "payload": row.get("payload"),
    }
