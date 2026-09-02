from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.storage import merge_records, save_records


class StorageTests(unittest.TestCase):
    def test_merge_updates_existing_date_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "daily_ranges.csv"
            json_path = Path(directory) / "daily_ranges.json"
            first = self._record("2026-09-01", "GBPUSD", 1.0)
            save_records(merge_records([first], csv_path), csv_path, json_path)

            replacement = self._record("2026-09-01", "GBPUSD", 2.0)
            frame = merge_records([replacement], csv_path)

            self.assertEqual(len(frame), 1)
            self.assertEqual(float(frame.iloc[0]["high"]), 2.0)

    @staticmethod
    def _record(session_date: str, symbol: str, high: float) -> dict:
        return {
            "date": session_date,
            "symbol": symbol,
            "window_start": f"{session_date}T08:00:00-America/New_York",
            "window_end": f"{session_date}T08:30:00-America/New_York",
            "open": 1.0,
            "high": high,
            "low": 0.5,
            "close": 0.8,
            "range": high - 0.5,
            "range_percent": 10.0,
            "high_time": f"{session_date}T08:10:00-04:00",
            "low_time": f"{session_date}T08:20:00-04:00",
            "high_before_low": True,
            "bar_count": 30,
            "status": "complete",
            "provider": "test",
            "updated_at": f"{session_date}T13:00:00+00:00",
        }


if __name__ == "__main__":
    unittest.main()
