"""Minimal async-friendly shim for aiosqlite using the standard sqlite3 library."""
from __future__ import annotations

import asyncio
import sqlite3
from typing import Any, Iterable, Optional, Sequence

Row = sqlite3.Row
Error = sqlite3.Error


class Cursor:
    """Asynchronous wrapper around :class:`sqlite3.Cursor`."""

    def __init__(self, cursor: sqlite3.Cursor) -> None:
        self._cursor = cursor

    @property
    def lastrowid(self) -> int:
        return self._cursor.lastrowid

    async def fetchone(self) -> Optional[Row]:
        return await asyncio.to_thread(self._cursor.fetchone)

    async def fetchall(self) -> list[Row]:
        return await asyncio.to_thread(self._cursor.fetchall)

    async def close(self) -> None:
        await asyncio.to_thread(self._cursor.close)


class Connection:
    """Async context manager providing sqlite3 operations via threads."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection
        self._lock = asyncio.Lock()

    async def __aenter__(self) -> "Connection":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self.close()

    @property
    def row_factory(self):  # type: ignore[override]
        return self._connection.row_factory

    @row_factory.setter
    def row_factory(self, value: Any) -> None:
        self._connection.row_factory = value

    async def execute(self, sql: str, parameters: Sequence[Any] | None = None) -> Cursor:
        params: Iterable[Any] = parameters if parameters is not None else ()
        async with self._lock:
            cursor = await asyncio.to_thread(self._connection.execute, sql, params)
        return Cursor(cursor)

    async def commit(self) -> None:
        async with self._lock:
            await asyncio.to_thread(self._connection.commit)

    async def close(self) -> None:
        async with self._lock:
            await asyncio.to_thread(self._connection.close)


async def _open_connection(path: str, **kwargs: Any) -> Connection:
    def _connect() -> sqlite3.Connection:
        return sqlite3.connect(path, check_same_thread=False, **kwargs)

    connection = await asyncio.to_thread(_connect)
    return Connection(connection)


class _ConnectionManager:
    def __init__(self, path: str, kwargs: dict[str, Any]) -> None:
        self._path = path
        self._kwargs = kwargs
        self._connection: Connection | None = None

    def __await__(self):
        return self._get_connection().__await__()

    async def _get_connection(self) -> Connection:
        if self._connection is None:
            self._connection = await _open_connection(self._path, **self._kwargs)
        return self._connection

    async def __aenter__(self) -> Connection:
        return await self._get_connection()

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        if self._connection is not None:
            await self._connection.close()
            self._connection = None


def connect(path: str, **kwargs: Any) -> _ConnectionManager:
    """Mimic :func:`aiosqlite.connect` with async context management support."""

    return _ConnectionManager(path, kwargs)


__all__ = ["connect", "Row", "Error", "Connection", "Cursor"]
