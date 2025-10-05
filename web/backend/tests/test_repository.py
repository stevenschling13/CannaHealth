"""Unit tests for the analysis repository."""
from __future__ import annotations

import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.services.repository import AnalysisRepository


@pytest.fixture(name="engine")
async def fixture_engine() -> AsyncEngine:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: sync_conn.exec_driver_sql(
            """
            CREATE TABLE analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                author TEXT NOT NULL,
                title TEXT NOT NULL,
                notes TEXT
            );
            """
        ))
        await conn.run_sync(lambda sync_conn: sync_conn.exec_driver_sql(
            """
            CREATE TABLE analysis_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                score INTEGER NOT NULL,
                payload TEXT,
                FOREIGN KEY(analysis_id) REFERENCES analysis(id) ON DELETE CASCADE
            );
            """
        ))
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_create_and_fetch_analysis(engine: AsyncEngine) -> None:
    repo = AnalysisRepository(engine)
    created = await repo.create_analysis(
        snapshot_id=1,
        author="tester",
        title="Daily QA",
        notes="Sample notes",
        items=[{"label": "positive", "score": 1, "payload": {"details": "ok"}}],
    )

    assert created["snapshot_id"] == 1
    assert created["author"] == "tester"
    assert len(created["items"]) == 1

    listed = await repo.list_analysis(snapshot_id=1)
    assert len(listed) == 1
    assert listed[0]["title"] == "Daily QA"
