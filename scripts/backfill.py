from __future__ import annotations

import argparse
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from scripts.config import INSTRUMENTS, NY_TIMEZONE
from scripts.data_provider import ProviderError, TwelveDataProvider
from scripts.ranges import calculate_daily_range
from scripts.storage import merge_records, save_records


def date_range(days: int) -> list:
    today = datetime.now(ZoneInfo(NY_TIMEZONE)).date()
    start = today - timedelta(days=days)
    return [start + timedelta(days=offset) for offset in range((today - start).days + 1)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill market range history.")
    parser.add_argument("--days", type=int, default=365, help="Calendar days to backfill.")
    parser.add_argument("--sleep", type=float, default=0.8, help="Seconds to pause between API calls.")
    args = parser.parse_args()

    provider = TwelveDataProvider(sleep_seconds=args.sleep)
    records = []
    for instrument in INSTRUMENTS:
        for session_date in date_range(args.days):
            if instrument.asset_type == "forex" and session_date.weekday() >= 5:
                print(f"Skipping {session_date}: no forex market data for {instrument.storage_symbol}.")
                continue
            print(f"Processing {instrument.storage_symbol} {session_date}...")
            try:
                candles = provider.fetch_intraday_window(instrument.provider_symbol, session_date)
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
                print(f"Skipping {session_date}: no market data for {instrument.storage_symbol}.")
            else:
                if record["bar_count"] != 30:
                    print(
                        f"{instrument.storage_symbol} {session_date}: "
                        f"{record['status']} ({record['bar_count']} bars)."
                    )
                records.append(record)
            time.sleep(args.sleep)

    frame = merge_records(records)
    save_records(frame)
    print(f"Saved {len(frame)} total historical rows.")


if __name__ == "__main__":
    main()
