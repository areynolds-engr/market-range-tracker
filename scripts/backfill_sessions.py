from __future__ import annotations

import argparse
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.config import INSTRUMENTS
from scripts.data_provider import ProviderError, TwelveDataProvider
from scripts.ranges import calculate_daily_range
from scripts.storage import merge_records, save_intraday_candles, save_records


def session_dates(start: date, end: date) -> list[date]:
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill full 08:00 to next-day 07:59 session files.")
    parser.add_argument("--start", required=True, type=parse_date, help="First session date, YYYY-MM-DD.")
    parser.add_argument("--end", required=True, type=parse_date, help="Last session date, YYYY-MM-DD.")
    parser.add_argument("--sleep", type=float, default=0.8, help="Seconds to pause between API calls.")
    args = parser.parse_args()

    if args.end < args.start:
        raise SystemExit("--end must be on or after --start")

    provider = TwelveDataProvider(sleep_seconds=args.sleep)
    records = []
    for instrument in INSTRUMENTS:
        for session_date in session_dates(args.start, args.end):
            if instrument.asset_type == "forex" and session_date.weekday() >= 5:
                print(f"Skipping {instrument.storage_symbol} {session_date}: forex weekend.")
                continue
            print(f"Backfilling {instrument.storage_symbol} {session_date}...")
            try:
                candles = provider.fetch_intraday_day(instrument.provider_symbol, session_date)
            except ProviderError as exc:
                print(f"Provider error for {instrument.storage_symbol} {session_date}: {exc}")
                continue

            record = calculate_daily_range(
                candles,
                session_date,
                instrument.storage_symbol,
                provider.provider_name,
            )
            if record is None:
                print(f"Skipping {instrument.storage_symbol} {session_date}: no market data.")
                continue
            save_intraday_candles(candles, instrument.storage_symbol, session_date)
            records.append(record)
            print(
                f"{instrument.storage_symbol} {session_date}: "
                f"{record['status']} ({record['bar_count']} range bars, {len(candles)} session bars)."
            )
            time.sleep(args.sleep)

    frame = merge_records(records)
    save_records(frame)
    print(f"Saved {len(records)} session rows. Historical row count: {len(frame)}.")


if __name__ == "__main__":
    main()
