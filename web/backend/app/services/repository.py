"""SQLite-backed repository helpers for analysis persistence."""
from __future__ import annotations

import asyncio
import json
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import aiosqlite

from app.models.analysis_schema import AnalysisItemRecord, AnalysisRecord, build_analysis


class AnalysisRepository:
    """Store analysis records using SQLite with async-safe helpers."""

    def __init__(self, db_path: str = "data/cannahealth.db") -> None:
        self._lock = asyncio.Lock()
        self._init_lock = asyncio.Lock()
        self._init_task: asyncio.Task[None] | None = None
        self._db_path = db_path
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)

    async def _ensure_initialized(self) -> None:
        async with self._init_lock:
            if self._init_task is None:
                self._init_task = asyncio.create_task(self._create_tables())
            task = self._init_task
        try:
            await task
        except Exception:
            async with self._init_lock:
                if self._init_task is task:
                    self._init_task = None
            raise

    @asynccontextmanager
    async def _connect(self) -> aiosqlite.Connection:
        try:
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute("PRAGMA foreign_keys = ON")
                db.row_factory = aiosqlite.Row
                yield db
        except sqlite3.Error as exc:
            raise RuntimeError(f"Database error: {exc}") from exc

    async def _create_tables(self) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL,
                    author TEXT NOT NULL,
                    title TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS analysis_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER NOT NULL,
                    label TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    payload TEXT,
                    FOREIGN KEY(analysis_id) REFERENCES analysis(id) ON DELETE CASCADE
                )
                """
            )
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_analysis_snapshot_id
                ON analysis(snapshot_id)
                """
            )
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_analysis_created_at
                ON analysis(created_at DESC)
                """
            )
            await db.commit()

    def _deserialize_payload(self, value: Optional[str]) -> Any:
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    def _build_item_record(self, row: aiosqlite.Row) -> AnalysisItemRecord:
        return AnalysisItemRecord(
            id=int(row["id"]),
            analysis_id=int(row["analysis_id"]),
            label=str(row["label"]),
            score=int(row["score"]),
            payload=self._deserialize_payload(row["payload"]),
        )

    def _build_analysis_record(
        self, row: aiosqlite.Row, items: List[AnalysisItemRecord]
    ) -> AnalysisRecord:
        record = build_analysis(
            analysis_id=int(row["id"]),
            snapshot_id=int(row["snapshot_id"]),
            author=str(row["author"]),
            title=str(row["title"]),
            notes=row["notes"],
            created_at=datetime.fromisoformat(str(row["created_at"]))
            if isinstance(row["created_at"], str)
            else row["created_at"],
        )
        record.items.extend(items)
        return record

    async def _fetch_items(
        self, db: aiosqlite.Connection, analysis_ids: List[int]
    ) -> Dict[int, List[AnalysisItemRecord]]:
        if not analysis_ids:
            return {}
        placeholders = ",".join("?" for _ in analysis_ids)
        cursor = await db.execute(
            f"""
            SELECT id, analysis_id, label, score, payload
            FROM analysis_items
            WHERE analysis_id IN ({placeholders})
            ORDER BY id ASC
            """,
            analysis_ids,
        )
        rows = await cursor.fetchall()
        await cursor.close()
        grouped: Dict[int, List[AnalysisItemRecord]] = {analysis_id: [] for analysis_id in analysis_ids}
        for row in rows:
            grouped.setdefault(int(row["analysis_id"]), []).append(self._build_item_record(row))
        return grouped

    async def _get_next_id(self, db: aiosqlite.Connection, table: str) -> int:
        cursor = await db.execute(
            "SELECT seq FROM sqlite_sequence WHERE name = ?", (table,)
        )
        row = await cursor.fetchone()
        await cursor.close()
        if row is None:
            return 1
        return int(row["seq"]) + 1

    async def create_analysis(
        self,
        snapshot_id: int,
        author: str,
        title: str,
        notes: Optional[str],
        items: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        await self._ensure_initialized()
        async with self._lock:
            created_at = datetime.now(timezone.utc)
            created_at_str = created_at.isoformat()
            try:
                async with self._connect() as db:
                    cursor = await db.execute(
                        """
                        INSERT INTO analysis (snapshot_id, author, title, notes, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (snapshot_id, author, title, notes, created_at_str),
                    )
                    analysis_id = int(cursor.lastrowid)
                    await cursor.close()

                    item_records: List[AnalysisItemRecord] = []
                    for item in items:
                        payload = item.get("payload")
                        payload_json = json.dumps(payload) if payload is not None else None
                        cursor = await db.execute(
                            """
                            INSERT INTO analysis_items (analysis_id, label, score, payload)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                analysis_id,
                                item["label"],
                                int(item["score"]),
                                payload_json,
                            ),
                        )
                        item_id = int(cursor.lastrowid)
                        await cursor.close()
                        item_records.append(
                            AnalysisItemRecord(
                                id=item_id,
                                analysis_id=analysis_id,
                                label=str(item["label"]),
                                score=int(item["score"]),
                                payload=payload,
                            )
                        )

                    await db.commit()
            except sqlite3.Error as exc:
                raise RuntimeError(f"Database error: {exc}") from exc

            record = build_analysis(
                analysis_id=analysis_id,
                snapshot_id=snapshot_id,
                author=author,
                title=title,
                notes=notes,
                created_at=created_at,
            )
            record.items.extend(item_records)
            return record.serialize()

    async def get_analysis(self, analysis_id: int) -> Dict[str, Any]:
        await self._ensure_initialized()
        async with self._connect() as db:
            cursor = await db.execute(
                """
                SELECT id, snapshot_id, author, title, notes, created_at
                FROM analysis
                WHERE id = ?
                """,
                (analysis_id,),
            )
            row = await cursor.fetchone()
            await cursor.close()
            if row is None:
                raise KeyError(f"Analysis {analysis_id} not found")

            items_map = await self._fetch_items(db, [int(row["id"])])
            record = self._build_analysis_record(row, items_map.get(int(row["id"]), []))
            return record.serialize()

    async def list_analysis(self, snapshot_id: Optional[int] = None) -> List[Dict[str, Any]]:
        await self._ensure_initialized()
        query = (
            "SELECT id, snapshot_id, author, title, notes, created_at FROM analysis"
        )
        params: List[Any] = []
        if snapshot_id is not None:
            query += " WHERE snapshot_id = ?"
            params.append(snapshot_id)
        query += " ORDER BY created_at DESC, id DESC"

        async with self._connect() as db:
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            await cursor.close()
            analysis_ids = [int(row["id"]) for row in rows]
            items_map = await self._fetch_items(db, analysis_ids)
            records = [
                self._build_analysis_record(row, items_map.get(int(row["id"]), []))
                for row in rows
            ]
            return [record.serialize() for record in records]

    async def clear(self) -> None:
        await self._ensure_initialized()
        async with self._lock:
            async with self._connect() as db:
                await db.execute("DELETE FROM analysis_items")
                await db.execute("DELETE FROM analysis")
                await db.execute(
                    "DELETE FROM sqlite_sequence WHERE name IN ('analysis', 'analysis_items')"
                )
                await db.commit()

    async def export_state(self) -> Dict[str, Any]:
        await self._ensure_initialized()
        async with self._lock:
            async with self._connect() as db:
                cursor = await db.execute(
                    """
                    SELECT id, snapshot_id, author, title, notes, created_at
                    FROM analysis
                    ORDER BY id ASC
                    """
                )
                analysis_rows = await cursor.fetchall()
                await cursor.close()
                analysis_ids = [int(row["id"]) for row in analysis_rows]
                items_map = await self._fetch_items(db, analysis_ids)

                records = [
                    self._build_analysis_record(row, items_map.get(int(row["id"]), []))
                    for row in analysis_rows
                ]

                next_analysis_id = await self._get_next_id(db, "analysis")
                next_item_id = await self._get_next_id(db, "analysis_items")

                return {
                    "next_analysis_id": next_analysis_id,
                    "next_item_id": next_item_id,
                    "analysis": [record.serialize() for record in records],
                }

    async def import_state(self, state: Dict[str, Any]) -> None:
        await self._ensure_initialized()
        async with self._lock:
            async with self._connect() as db:
                await db.execute("DELETE FROM analysis_items")
                await db.execute("DELETE FROM analysis")
                await db.execute(
                    "DELETE FROM sqlite_sequence WHERE name IN ('analysis', 'analysis_items')"
                )

                for data in state.get("analysis", []):
                    created_at = data.get("created_at")
                    if isinstance(created_at, str):
                        created_at_str = created_at
                    elif created_at is None:
                        created_at_str = datetime.now(timezone.utc).isoformat()
                    else:
                        created_at_str = created_at.isoformat()
                    await db.execute(
                        """
                        INSERT INTO analysis (id, snapshot_id, author, title, notes, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            int(data["id"]),
                            int(data["snapshot_id"]),
                            str(data["author"]),
                            str(data["title"]),
                            data.get("notes"),
                            created_at_str,
                        ),
                    )
                    for item in data.get("items", []):
                        payload = item.get("payload")
                        payload_json = json.dumps(payload) if payload is not None else None
                        await db.execute(
                            """
                            INSERT INTO analysis_items (id, analysis_id, label, score, payload)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                int(item["id"]),
                                int(item["analysis_id"]),
                                str(item["label"]),
                                int(item["score"]),
                                payload_json,
                            ),
                        )

                next_analysis_id = int(state.get("next_analysis_id", 1))
                next_item_id = int(state.get("next_item_id", 1))

                await db.execute(
                    "DELETE FROM sqlite_sequence WHERE name IN ('analysis', 'analysis_items')"
                )
                if next_analysis_id > 1:
                    await db.execute(
                        "INSERT INTO sqlite_sequence(name, seq) VALUES ('analysis', ?)",
                        (next_analysis_id - 1,),
                    )
                if next_item_id > 1:
                    await db.execute(
                        "INSERT INTO sqlite_sequence(name, seq) VALUES ('analysis_items', ?)",
                        (next_item_id - 1,),
                    )

                await db.commit()
