"""Unit tests for the analysis repository."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.models.analysis_schema import metadata
from app.services.repository import AnalysisRepository


@pytest_asyncio.fixture
async def engine() -> AsyncEngine:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def repository(session_factory: async_sessionmaker[AsyncSession]) -> AnalysisRepository:
    return AnalysisRepository(session_factory)


@pytest.mark.asyncio
async def test_create_and_fetch_analysis(repository: AnalysisRepository) -> None:
    created = await repository.create_analysis(
        snapshot_id=1,
        author="tester",
        title="Daily QA",
        notes="Sample notes",
        items=[{"label": "positive", "score": 1, "payload": {"details": "ok"}}],
    )

    assert created["snapshot_id"] == 1
    assert created["author"] == "tester"
    assert created["items"][0]["label"] == "positive"
    assert created["items"][0]["payload"] == {"details": "ok"}

    listed = await repository.list_analysis(snapshot_id=1)
    assert len(listed) == 1
    assert listed[0]["id"] == created["id"]
    assert listed[0]["title"] == "Daily QA"
