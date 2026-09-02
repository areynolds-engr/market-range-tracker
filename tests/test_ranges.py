from __future__ import annotations

import unittest
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd

from scripts.ranges import calculate_daily_range


class RangeCalculationTests(unittest.TestCase):
    def test_calculates_complete_new_york_window(self) -> None:
        ny = ZoneInfo("America/New_York")
        rows = []
        start = datetime(2026, 9, 1, 8, 0, tzinfo=ny)
        for minute in range(30):
            value = 1.30 + minute / 10000
            rows.append(
                {
                    "datetime": start + timedelta(minutes=minute),
                    "open": value,
                    "high": value + 0.001,
                    "low": value - 0.001,
                    "close": value + 0.0003,
                }
            )
        result = calculate_daily_range(
            pd.DataFrame(rows),
            date(2026, 9, 1),
            "GBPUSD",
            "test",
            datetime(2026, 9, 1, 13, 0, tzinfo=timezone.utc),
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["bar_count"], 30)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["open"], 1.3)
        self.assertFalse(result["high_before_low"])

    def test_marks_short_window_incomplete(self) -> None:
        ny = ZoneInfo("America/New_York")
        rows = [
            {"datetime": datetime(2026, 9, 1, 8, minute, tzinfo=ny), "open": 10, "high": 11, "low": 9, "close": 10}
            for minute in range(10)
        ]
        result = calculate_daily_range(pd.DataFrame(rows), date(2026, 9, 1), "BTCUSD", "test")
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["bar_count"], 10)


if __name__ == "__main__":
    unittest.main()
