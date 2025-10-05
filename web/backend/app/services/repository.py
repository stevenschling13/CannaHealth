"""Repository helpers for persisting analysis snapshots."""
from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

__all__ = ["AnalysisRepository", "HAS_SQLALCHEMY"]

from app.models.analysis_schema import (
    analysis_item_table,
    analysis_table,
    serialize_analysis,
    serialize_analysis_item,
)

try:  # pragma: no cover - optional dependency branch
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
except ModuleNotFoundError:  # pragma: no cover - offline fallback
    AsyncEngine = AsyncSession = async_sessionmaker = None  # type: ignore[assignment]
    HAS_SQLALCHEMY = False
else:
    HAS_SQLALCHEMY = True


if HAS_SQLALCHEMY and analysis_table is not None:

    class AnalysisRepository:
        """SQLAlchemy-powered repository when dependency is available."""

        def __init__(self, engine: AsyncEngine) -> None:  # type: ignore[override]
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

else:

    class AnalysisRepository:
        """SQLite-backed repository usable without SQLAlchemy."""

        def __init__(self, database: str | Path | None = None) -> None:  # type: ignore[override]
            self._database_path = str(database or ":memory:")
            self._lock = asyncio.Lock()
            self._ensure_schema()

        def _connect(self) -> sqlite3.Connection:
            conn = sqlite3.connect(self._database_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn

        def _ensure_schema(self) -> None:
            with self._connect() as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        snapshot_id INTEGER NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        author TEXT NOT NULL,
                        title TEXT NOT NULL,
                        notes TEXT
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS analysis_item (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        analysis_id INTEGER NOT NULL,
                        label TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        payload TEXT,
                        FOREIGN KEY(analysis_id) REFERENCES analysis(id) ON DELETE CASCADE
                    )
                    """
                )

        async def create_analysis(
            self,
            snapshot_id: int,
            author: str,
            title: str,
            notes: Optional[str],
            items: Iterable[Dict[str, Any]],
        ) -> Dict[str, Any]:
            async with self._lock:
                def _insert() -> int:
                    with self._connect() as conn:
                        cursor = conn.execute(
                            """
                            INSERT INTO analysis (snapshot_id, author, title, notes)
                            VALUES (?, ?, ?, ?)
                            """,
                            (snapshot_id, author, title, notes),
                        )
                        analysis_id = cursor.lastrowid
                        if items:
                            conn.executemany(
                                """
                                INSERT INTO analysis_item (analysis_id, label, score, payload)
                                VALUES (?, ?, ?, ?)
                                """,
                                [
                                    (
                                        analysis_id,
                                        item["label"],
                                        item["score"],
                                        json.dumps(item.get("payload")) if item.get("payload") is not None else None,
                                    )
                                    for item in items
                                ],
                            )
                    return analysis_id

                analysis_id = await asyncio.to_thread(_insert)
            return await self.get_analysis(analysis_id)

        async def get_analysis(self, analysis_id: int) -> Dict[str, Any]:
            async with self._lock:
                def _fetch() -> Dict[str, Any]:
                    with self._connect() as conn:
                        row = conn.execute(
                            "SELECT * FROM analysis WHERE id = ?", (analysis_id,)
                        ).fetchone()
                        if row is None:
                            raise KeyError(f"Analysis {analysis_id} not found")
                        items = conn.execute(
                            "SELECT * FROM analysis_item WHERE analysis_id = ?", (analysis_id,)
                        ).fetchall()
                    data = serialize_analysis(row)
                    data["items"] = [
                        serialize_analysis_item({**dict(item), "payload": json.loads(item["payload"]) if item["payload"] else None})
                        for item in items
                    ]
                    return data

                return await asyncio.to_thread(_fetch)

        async def list_analysis(self, snapshot_id: Optional[int] = None) -> List[Dict[str, Any]]:
            async with self._lock:
                def _list() -> List[Dict[str, Any]]:
                    with self._connect() as conn:
                        if snapshot_id is None:
                            rows = conn.execute(
                                "SELECT * FROM analysis ORDER BY datetime(created_at) DESC"
                            ).fetchall()
                        else:
                            rows = conn.execute(
                                "SELECT * FROM analysis WHERE snapshot_id = ? ORDER BY datetime(created_at) DESC",
                                (snapshot_id,),
                            ).fetchall()
                    return [serialize_analysis(row) for row in rows]

                return await asyncio.to_thread(_list)
