"""Minimal admin API router exposing analysis listings."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.services.repository import AnalysisRepository

try:  # pragma: no cover - optional dependency
    from sqlalchemy.ext.asyncio import AsyncEngine
except ModuleNotFoundError:  # pragma: no cover - offline fallback
    AsyncEngine = Any  # type: ignore[assignment]

router = APIRouter(prefix="/admin", tags=["admin"])


def get_repository(engine: AsyncEngine | None = None) -> AnalysisRepository:  # pragma: no cover - simple wiring
    if engine is not None:
        return AnalysisRepository(engine)
    return AnalysisRepository()


@router.get("/analysis")
async def list_analysis(
    snapshot_id: int | None = None,
    repo: AnalysisRepository = Depends(get_repository),
):
    return await repo.list_analysis(snapshot_id=snapshot_id)
