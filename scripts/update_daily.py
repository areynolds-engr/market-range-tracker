from __future__ import annotations

from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo

from scripts.config import INSTRUMENTS, NY_TIMEZONE
from scripts.data_provider import ProviderError, TwelveDataProvider
from scripts.ranges import calculate_daily_range
from scripts.storage import merge_records, save_records


def target_date(now: datetime) -> datetime.date:
    window_ready = dt_time(8, 45)
    if now.time() < window_ready:
        raise SystemExit(
            f"It is {now.strftime('%Y-%m-%d %H:%M %Z')} in New York. "
            "The 08:00-08:30 window is not ready yet, so no data was saved."
        )
    return now.date()


def main() -> None:
    now = datetime.now(ZoneInfo(NY_TIMEZONE))
    session_date = target_date(now)
    provider = TwelveDataProvider()
    records = []

    print(session_date.isoformat())
    for instrument in INSTRUMENTS:
        if instrument.asset_type == "forex" and session_date.weekday() >= 5:
            print(f"\n{instrument.storage_symbol}\nSkipped: forex weekend.")
            continue
        try:
            candles = provider.fetch_intraday_window(instrument.provider_symbol, session_date)
        except ProviderError as exc:
            print(f"\n{instrument.storage_symbol}\nProvider error: {exc}")
            continue
        record = calculate_daily_range(candles, session_date, instrument.storage_symbol, provider.provider_name)
        if record is None:
            print(f"\n{instrument.storage_symbol}\nSkipped: no market data.")
            continue
        records.append(record)
        print(
            f"\n{instrument.storage_symbol}\n"
            f"High: {record['high']}\n"
            f"Low: {record['low']}\n"
            f"Range: {record['range']}\n"
            f"Status: {record['status']} ({record['bar_count']} bars)"
        )

    if not records:
        print("\nNo records to save.")
        return
    frame = merge_records(records)
    save_records(frame)
    print(f"\nSaved {len(records)} updated rows. Historical row count: {len(frame)}.")


if __name__ == "__main__":
    main()
