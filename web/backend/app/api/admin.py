"""Minimal admin API router exposing analysis listings."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncEngine

from app.services.repository import AnalysisRepository

router = APIRouter(prefix="/admin", tags=["admin"])


def get_repository(engine: AsyncEngine = Depends()) -> AnalysisRepository:  # pragma: no cover
    return AnalysisRepository(engine)


@router.get("/analysis")
async def list_analysis(snapshot_id: int | None = None, repo: AnalysisRepository = Depends(get_repository)):
    return await repo.list_analysis(snapshot_id=snapshot_id)
