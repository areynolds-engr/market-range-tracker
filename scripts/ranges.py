from __future__ import annotations

from datetime import date, datetime, time as dt_time, timezone
from zoneinfo import ZoneInfo

import pandas as pd

from scripts.config import EXPECTED_BARS, MIN_COMPLETE_BARS, NY_TIMEZONE, WINDOW_END, WINDOW_START


def calculate_daily_range(
    candles: pd.DataFrame,
    session_date: date,
    symbol: str,
    provider: str,
    updated_at: datetime | None = None,
) -> dict | None:
    """Calculate the 08:00 inclusive to 08:30 exclusive New York range."""

    if candles.empty:
        return None

    ny = ZoneInfo(NY_TIMEZONE)
    start = datetime.combine(session_date, dt_time(8, 0), tzinfo=ny)
    end = datetime.combine(session_date, dt_time(8, 30), tzinfo=ny)

    frame = candles.copy()
    frame["datetime"] = pd.to_datetime(frame["datetime"], errors="coerce")
    if frame["datetime"].dt.tz is None:
        frame["datetime"] = frame["datetime"].dt.tz_localize(ny)
    else:
        frame["datetime"] = frame["datetime"].dt.tz_convert(ny)
    frame = frame[(frame["datetime"] >= start) & (frame["datetime"] < end)].sort_values("datetime")

    for column in ("open", "high", "low", "close"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["open", "high", "low", "close"])
    if frame.empty:
        return None

    opening = float(frame.iloc[0]["open"])
    high = float(frame["high"].max())
    low = float(frame["low"].min())
    close = float(frame.iloc[-1]["close"])
    high_time = frame.loc[frame["high"].idxmax(), "datetime"]
    low_time = frame.loc[frame["low"].idxmin(), "datetime"]
    bar_count = int(len(frame))
    status = "complete" if bar_count >= MIN_COMPLETE_BARS else "incomplete"

    if not _prices_are_consistent(opening, high, low, close):
        status = "incomplete"

    generated_at = updated_at or datetime.now(timezone.utc)
    return {
        "date": session_date.isoformat(),
        "symbol": symbol,
        "window_start": f"{session_date.isoformat()}T{WINDOW_START}-America/New_York",
        "window_end": f"{session_date.isoformat()}T{WINDOW_END}-America/New_York",
        "open": round(opening, 8),
        "high": round(high, 8),
        "low": round(low, 8),
        "close": round(close, 8),
        "range": round(high - low, 8),
        "range_percent": round(((high - low) / opening) * 100, 6) if opening else None,
        "high_time": high_time.isoformat(),
        "low_time": low_time.isoformat(),
        "high_before_low": bool(high_time < low_time),
        "bar_count": bar_count,
        "status": status,
        "provider": provider,
        "updated_at": generated_at.astimezone(timezone.utc).replace(microsecond=0).isoformat(),
    }


def _prices_are_consistent(opening: float, high: float, low: float, close: float) -> bool:
    return high >= low and high >= opening and high >= close and low <= opening and low <= close


def expected_bar_count() -> int:
    return EXPECTED_BARS
