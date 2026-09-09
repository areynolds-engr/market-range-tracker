from __future__ import annotations

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from scripts.update_daily import target_date


class UpdateDailyTests(unittest.TestCase):
    def test_targets_previous_completed_session_after_morning_close(self) -> None:
        now = datetime(2026, 9, 10, 9, 0, tzinfo=ZoneInfo("America/New_York"))
        self.assertEqual(target_date(now).isoformat(), "2026-09-09")

    def test_refuses_before_session_close(self) -> None:
        now = datetime(2026, 9, 10, 7, 30, tzinfo=ZoneInfo("America/New_York"))
        with self.assertRaises(SystemExit):
            target_date(now)


if __name__ == "__main__":
    unittest.main()
