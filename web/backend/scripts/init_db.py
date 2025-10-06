#!/usr/bin/env python3
"""Initialize the analysis database schema."""
import asyncio
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.services.repository import AnalysisRepository  # noqa: E402


async def main() -> None:
    """Create the SQLite schema for the analysis repository."""
    repo = AnalysisRepository(db_path="data/cannahealth.db")
    await repo._create_tables()  # pylint: disable=protected-access
    print("Database initialized successfully")
    print(f"Database file: {Path(repo._db_path).resolve()}")  # pylint: disable=protected-access


if __name__ == "__main__":
    asyncio.run(main())
