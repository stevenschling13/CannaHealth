"""aiohttp application exposing admin analysis endpoints."""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from aiohttp import ContentTypeError, web
import aiohttp_cors

from app.api.admin import AdminService, AnalysisPayload, AnalysisItemPayload


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


logger = logging.getLogger(__name__)


@web.middleware
async def request_logging_middleware(
    request: web.Request, handler: web.Handler
) -> web.StreamResponse:
    start_time = time.perf_counter()
    try:
        response = await handler(request)
    except KeyError as exc:
        message = exc.args[0] if exc.args else "Not found"
        response = web.json_response({"error": str(message)}, status=404)
    except web.HTTPException as exc:
        if exc.status < 400:
            raise
        message = exc.text or exc.reason or "Bad Request"
        response = web.json_response({"error": message}, status=exc.status, headers=exc.headers)
    except Exception:  # pylint: disable=broad-except
        logger.exception("Unhandled server error")
        response = web.json_response({"error": "Internal Server Error"}, status=500)
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        status = response.status if 'response' in locals() else "-"
        logger.info("%s %s -> %s (%.2f ms)", request.method, request.path_qs, status, duration_ms)
    return response


def create_app() -> web.Application:
    app = web.Application(middlewares=[request_logging_middleware])
    app["admin_service"] = AdminService()

    app.router.add_get("/admin/analysis", list_analysis)
    app.router.add_post("/admin/analysis", create_analysis)
    app.router.add_get("/health", health_check)

    cors = aiohttp_cors.setup(
        app,
        defaults={
            "http://localhost:3000": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                allow_headers=("Content-Type", "Accept"),
                allow_methods=("GET", "POST", "OPTIONS"),
            ),
            "http://127.0.0.1:3000": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                allow_headers=("Content-Type", "Accept"),
                allow_methods=("GET", "POST", "OPTIONS"),
            ),
        },
    )

    for route in list(app.router.routes()):
        cors.add(route)

    return app


async def list_analysis(request: web.Request) -> web.Response:
    service: AdminService = request.app["admin_service"]
    snapshot_id_param = request.rel_url.query.get("snapshot_id")
    snapshot_id = None
    if snapshot_id_param is not None:
        try:
            snapshot_id = int(snapshot_id_param)
        except (TypeError, ValueError):
            raise web.HTTPBadRequest(text="snapshot_id must be an integer")

    analysis = await service.list_analysis(snapshot_id=snapshot_id)
    return web.json_response(analysis)


async def create_analysis(request: web.Request) -> web.Response:
    service: AdminService = request.app["admin_service"]

    try:
        data = await request.json()
    except (json.JSONDecodeError, ContentTypeError):
        raise web.HTTPBadRequest(text="Invalid JSON body")

    if not isinstance(data, dict):
        raise web.HTTPBadRequest(text="Request body must be a JSON object")

    payload = _parse_analysis_payload(data)
    record = await service.create_analysis(payload)
    return web.json_response(record, status=201)


def _parse_analysis_payload(data: dict[str, Any]) -> AnalysisPayload:
    if "snapshot_id" not in data:
        raise web.HTTPBadRequest(text="snapshot_id is required")
    snapshot_id = _ensure_int(data.get("snapshot_id"), "snapshot_id")

    author = data.get("author")
    if not isinstance(author, str) or not author.strip():
        raise web.HTTPBadRequest(text="author must be a non-empty string")

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        raise web.HTTPBadRequest(text="title must be a non-empty string")

    notes = data.get("notes")
    if notes is not None and not isinstance(notes, str):
        raise web.HTTPBadRequest(text="notes must be a string or null")

    if "items" not in data:
        raise web.HTTPBadRequest(text="items is required")
    items = data.get("items")
    if not isinstance(items, list):
        raise web.HTTPBadRequest(text="items must be a list")

    parsed_items: list[AnalysisItemPayload] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise web.HTTPBadRequest(text=f"items[{index}] must be an object")

        label = item.get("label")
        if not isinstance(label, str) or not label.strip():
            raise web.HTTPBadRequest(text=f"items[{index}].label must be a non-empty string")

        score = _ensure_int(item.get("score"), f"items[{index}].score")

        payload = item.get("payload")
        if payload is not None and not isinstance(payload, dict):
            raise web.HTTPBadRequest(text=f"items[{index}].payload must be an object or null")

        parsed_items.append(
            AnalysisItemPayload(label=label, score=score, payload=payload),
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
        raise web.HTTPBadRequest(text=f"{field_name} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise web.HTTPBadRequest(text=f"{field_name} must be an integer")


async def health_check(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=8000)
