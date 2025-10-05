"""In-memory repository helpers for analysis persistence."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from app.models.analysis_schema import AnalysisItemRecord, AnalysisRecord, build_analysis


class AnalysisRepository:
    """Store analysis records in memory with async-safe helpers."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._next_analysis_id = 1
        self._next_item_id = 1
        self._analysis: Dict[int, AnalysisRecord] = {}

    async def create_analysis(
        self,
        snapshot_id: int,
        author: str,
        title: str,
        notes: Optional[str],
        items: Iterable[Dict[str, Any]],
    ) -> Dict[str, Any]:
        async with self._lock:
            analysis_id = self._next_analysis_id
            self._next_analysis_id += 1
            created_at = datetime.now(timezone.utc)
            record = build_analysis(
                analysis_id=analysis_id,
                snapshot_id=snapshot_id,
                author=author,
                title=title,
                notes=notes,
                created_at=created_at,
            )

            for item in items:
                item_id = self._next_item_id
                self._next_item_id += 1
                record.items.append(
                    AnalysisItemRecord(
                        id=item_id,
                        analysis_id=analysis_id,
                        label=item["label"],
                        score=int(item["score"]),
                        payload=item.get("payload") if isinstance(item.get("payload"), dict) else item.get("payload"),
                    )
                )

            self._analysis[analysis_id] = record
            return record.serialize()

    async def get_analysis(self, analysis_id: int) -> Dict[str, Any]:
        async with self._lock:
            record = self._analysis.get(analysis_id)
            if record is None:
                raise KeyError(f"Analysis {analysis_id} not found")
            return record.serialize()

    async def list_analysis(self, snapshot_id: Optional[int] = None) -> List[Dict[str, Any]]:
        async with self._lock:
            records = list(self._analysis.values())
        if snapshot_id is not None:
            records = [record for record in records if record.snapshot_id == snapshot_id]
        records.sort(key=lambda record: (record.created_at, record.id), reverse=True)
        return [record.serialize() for record in records]

    async def clear(self) -> None:
        async with self._lock:
            self._analysis.clear()
            self._next_analysis_id = 1
            self._next_item_id = 1

    async def export_state(self) -> Dict[str, Any]:
        async with self._lock:
            return {
                "next_analysis_id": self._next_analysis_id,
                "next_item_id": self._next_item_id,
                "analysis": [record.serialize() for record in self._analysis.values()],
            }

    async def import_state(self, state: Dict[str, Any]) -> None:
        async with self._lock:
            self._analysis.clear()
            self._next_analysis_id = int(state.get("next_analysis_id", 1))
            self._next_item_id = int(state.get("next_item_id", 1))
            for data in state.get("analysis", []):
                record = AnalysisRecord(
                    id=int(data["id"]),
                    snapshot_id=int(data["snapshot_id"]),
                    author=str(data["author"]),
                    title=str(data["title"]),
                    notes=data.get("notes"),
                    created_at=datetime.fromisoformat(data["created_at"]),
                )
                for item in data.get("items", []):
                    record.items.append(
                        AnalysisItemRecord(
                            id=int(item["id"]),
                            analysis_id=int(item["analysis_id"]),
                            label=str(item["label"]),
                            score=int(item["score"]),
                            payload=item.get("payload"),
                        )
                    )
                self._analysis[record.id] = record
