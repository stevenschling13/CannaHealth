"""FastAPI application exposing admin analysis endpoints."""
from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.api.admin import (  # noqa: E402
    AdminService,
    AnalysisItemPayload,
    AnalysisPayload,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

_admin_service = AdminService()


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):  # type: ignore[override]
    """Log every request and normalize errors to JSON responses."""
    start_time = time.perf_counter()
    try:
        response = await call_next(request)
    except KeyError as exc:
        message = exc.args[0] if exc.args else "Not found"
        response = JSONResponse(status_code=404, content={"error": message})
    except HTTPException as exc:
        response = JSONResponse(
            status_code=exc.status_code,
            headers=exc.headers,
            content={"error": _format_error_detail(exc.detail)},
        )
    except Exception:  # pylint: disable=broad-except
        logger.exception("Unhandled server error")
        response = JSONResponse(status_code=500, content={"error": "Internal Server Error"})
    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "%s %s -> %s (%.2f ms)",
        request.method,
        request.url.path,
        getattr(response, "status_code", "-"),
        duration_ms,
    )
    return response


@app.exception_handler(json.JSONDecodeError)
async def json_decode_exception_handler(_: Request, exc: json.JSONDecodeError):
    del exc
    return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})


@app.get("/admin/analysis")
async def list_analysis(snapshot_id: str | None = None) -> list[dict[str, Any]]:
    parsed_snapshot: int | None = None
    if snapshot_id is not None:
        parsed_snapshot = _ensure_int(snapshot_id, "snapshot_id")
    return await _admin_service.list_analysis(snapshot_id=parsed_snapshot)


@app.post("/admin/analysis", status_code=201)
async def create_analysis(request: Request) -> dict[str, Any]:
    try:
        data = await request.json()
    except json.JSONDecodeError as exc:  # pragma: no cover - handled by FastAPI handler
        raise exc

    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")

    payload = _parse_analysis_payload(data)
    return await _admin_service.create_analysis(payload)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


def _parse_analysis_payload(data: dict[str, Any]) -> AnalysisPayload:
    if "snapshot_id" not in data:
        raise HTTPException(status_code=400, detail="snapshot_id is required")
    snapshot_id = _ensure_int(data.get("snapshot_id"), "snapshot_id")

    author = data.get("author")
    if not isinstance(author, str) or not author.strip():
        raise HTTPException(status_code=400, detail="author must be a non-empty string")

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        raise HTTPException(status_code=400, detail="title must be a non-empty string")

    notes = data.get("notes")
    if notes is not None and not isinstance(notes, str):
        raise HTTPException(status_code=400, detail="notes must be a string or null")

    if "items" not in data:
        raise HTTPException(status_code=400, detail="items is required")
    items = data.get("items")
    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="items must be a list")

    parsed_items: list[AnalysisItemPayload] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise HTTPException(status_code=400, detail=f"items[{index}] must be an object")

        label = item.get("label")
        if not isinstance(label, str) or not label.strip():
            raise HTTPException(
                status_code=400,
                detail=f"items[{index}].label must be a non-empty string",
            )

        score = _ensure_int(item.get("score"), f"items[{index}].score")

        payload = item.get("payload")
        if payload is not None and not isinstance(payload, dict):
            raise HTTPException(
                status_code=400,
                detail=f"items[{index}].payload must be an object or null",
            )

        parsed_items.append(
            AnalysisItemPayload(label=label.strip(), score=score, payload=payload),
        )

    return AnalysisPayload(
        snapshot_id=snapshot_id,
        author=author.strip(),
        title=title.strip(),
        notes=notes.strip() if isinstance(notes, str) else notes,
        items=parsed_items,
    )


def _ensure_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise HTTPException(status_code=400, detail=f"{field_name} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"{field_name} must be an integer")


def _format_error_detail(detail: Any) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        return detail[0] if detail else "Error"
    if isinstance(detail, dict) and "error" in detail:
        return str(detail["error"])
    return "Error"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
