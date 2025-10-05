"""Minimal FastAPI stub for offline testing."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

__all__ = ["APIRouter", "Depends"]


@dataclass
class Depends:  # pragma: no cover - simple container
    dependency: Optional[Callable[..., Any]] = None


class APIRouter:
    """Collects route metadata for documentation/testing purposes."""

    def __init__(self, prefix: str = "", tags: Optional[list[str]] = None) -> None:
        self.prefix = prefix
        self.tags = tags or []
        self.routes: list[tuple[str, str, Callable[..., Any]]] = []

    def get(self, path: str, *, name: Optional[str] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.routes.append(("GET", f"{self.prefix}{path}", func))
            return func

        return decorator
