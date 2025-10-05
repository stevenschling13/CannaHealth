"""Tests for the in-memory analysis repository."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.repository import AnalysisRepository


class AnalysisRepositoryTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.repository = AnalysisRepository()

    async def test_create_and_fetch_analysis(self) -> None:
        created = await self.repository.create_analysis(
            snapshot_id=1,
            author="tester",
            title="Daily QA",
            notes="Sample notes",
            items=[{"label": "positive", "score": 1, "payload": {"details": "ok"}}],
        )

        self.assertEqual(created["snapshot_id"], 1)
        self.assertEqual(created["author"], "tester")
        self.assertEqual(created["items"][0]["label"], "positive")
        self.assertEqual(created["items"][0]["payload"], {"details": "ok"})

        fetched = await self.repository.get_analysis(created["id"])
        self.assertEqual(fetched["id"], created["id"])
        self.assertEqual(fetched["title"], "Daily QA")

    async def test_list_filters_by_snapshot(self) -> None:
        await self.repository.create_analysis(
            snapshot_id=1,
            author="tester",
            title="First",
            notes=None,
            items=[],
        )
        await self.repository.create_analysis(
            snapshot_id=2,
            author="tester",
            title="Second",
            notes=None,
            items=[],
        )

        all_rows = await self.repository.list_analysis()
        self.assertEqual(len(all_rows), 2)

        filtered = await self.repository.list_analysis(snapshot_id=2)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["snapshot_id"], 2)


if __name__ == "__main__":
    unittest.main()
