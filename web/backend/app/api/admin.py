"""Admin API router exposing analysis endpoints."""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncEngine

from app.services.repository import AnalysisRepository

router = APIRouter(prefix="/admin", tags=["admin"])


class AnalysisItemPayload(BaseModel):
    label: str
    score: int
    payload: Optional[dict[str, Any]] = None


class AnalysisPayload(BaseModel):
    snapshot_id: int = Field(..., ge=1)
    author: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    notes: Optional[str] = None
    items: list[AnalysisItemPayload] = Field(default_factory=list)


async def get_repository(request: Request) -> AnalysisRepository:
    repo: AnalysisRepository | None = getattr(request.app.state, "analysis_repository", None)
    if repo is not None:
        return repo

    engine = getattr(request.app.state, "db_engine", None)
    if engine is None or not isinstance(engine, AsyncEngine):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database engine not configured")

    repo = AnalysisRepository.from_engine(engine)
    request.app.state.analysis_repository = repo
    return repo


@router.get("/analysis")
async def list_analysis(snapshot_id: int | None = None, repo: AnalysisRepository = Depends(get_repository)):
    return await repo.list_analysis(snapshot_id=snapshot_id)


@router.post("/analysis", status_code=status.HTTP_201_CREATED)
async def create_analysis(payload: AnalysisPayload, repo: AnalysisRepository = Depends(get_repository)):
    created = await repo.create_analysis(
        snapshot_id=payload.snapshot_id,
        author=payload.author,
        title=payload.title,
        notes=payload.notes,
        items=[item.dict() for item in payload.items],
    )
    return created
