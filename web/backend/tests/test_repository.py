"""Unit tests for the analysis repository."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "web/backend"))

import asyncio

import pytest

from app.services.repository import AnalysisRepository, HAS_SQLALCHEMY

if HAS_SQLALCHEMY:  # pragma: no cover - exercised only when dependency installed
    pytest.skip("SQLAlchemy backend covered in environments with dependency", allow_module_level=True)


@pytest.fixture(name="repository")
def fixture_repository(tmp_path: Path) -> AnalysisRepository:
    db_path = tmp_path / "analysis.db"
    repo = AnalysisRepository(db_path)
    return repo


def test_create_and_fetch_analysis(repository: AnalysisRepository) -> None:
    async def _run() -> None:
        created = await repository.create_analysis(
            snapshot_id=1,
            author="tester",
            title="Daily QA",
            notes="Sample notes",
            items=[{"label": "positive", "score": 1, "payload": {"details": "ok"}}],
        )

        assert created["snapshot_id"] == 1
        assert created["author"] == "tester"
        assert len(created["items"]) == 1
        assert created["items"][0]["payload"] == {"details": "ok"}

        listed = await repository.list_analysis(snapshot_id=1)
        assert len(listed) == 1
        assert listed[0]["title"] == "Daily QA"

    asyncio.run(_run())
