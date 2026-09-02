from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import date, datetime, time as dt_time
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import requests

from scripts.config import NY_TIMEZONE


class ProviderError(RuntimeError):
    """Raised when the market-data provider cannot return usable data."""


@dataclass
class TwelveDataProvider:
    """Small Twelve Data adapter.

    Twelve Data symbol names used here are the documented slash format, such as
    GBP/USD and BTC/USD. The timezone parameter is set explicitly for intraday
    requests so date boundaries follow New York daylight-saving changes.
    """

    api_key: str | None = None
    base_url: str = "https://api.twelvedata.com/time_series"
    timeout: int = 30
    max_retries: int = int(os.getenv("TWELVE_DATA_MAX_RETRIES", "3"))
    sleep_seconds: float = float(os.getenv("TWELVE_DATA_SLEEP_SECONDS", "0.8"))
    provider_name: str = "Twelve Data"

    def __post_init__(self) -> None:
        if self.api_key is None:
            self.api_key = os.getenv("TWELVE_DATA_API_KEY")
        if not self.api_key:
            raise ProviderError(
                "TWELVE_DATA_API_KEY is not set. Add it locally or as a GitHub repository secret."
            )

    def fetch_intraday_window(self, symbol: str, session_date: date) -> pd.DataFrame:
        ny = ZoneInfo(NY_TIMEZONE)
        start = datetime.combine(session_date, dt_time(8, 0), tzinfo=ny)
        end = datetime.combine(session_date, dt_time(8, 30), tzinfo=ny)
        params = {
            "symbol": symbol,
            "interval": "1min",
            "start_date": start.strftime("%Y-%m-%dT%H:%M:%S"),
            "end_date": end.strftime("%Y-%m-%dT%H:%M:%S"),
            "timezone": NY_TIMEZONE,
            "outputsize": 500,
            "order": "ASC",
            "apikey": self.api_key,
        }
        payload = self._get(params)
        values = payload.get("values") or []
        if not values:
            return self._empty_frame()

        frame = pd.DataFrame(values)
        if "datetime" not in frame.columns:
            return self._empty_frame()

        frame["datetime"] = pd.to_datetime(frame["datetime"], errors="coerce")
        frame = frame.dropna(subset=["datetime"])
        if frame["datetime"].dt.tz is None:
            frame["datetime"] = frame["datetime"].dt.tz_localize(ny, nonexistent="shift_forward", ambiguous="NaT")
        else:
            frame["datetime"] = frame["datetime"].dt.tz_convert(ny)
        frame = frame.dropna(subset=["datetime"])

        for column in ("open", "high", "low", "close"):
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame = frame.dropna(subset=["open", "high", "low", "close"])
        return frame[["datetime", "open", "high", "low", "close"]].sort_values("datetime")

    def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(self.base_url, params=params, timeout=self.timeout)
                response.raise_for_status()
                payload = response.json()
                if payload.get("status") == "error":
                    message = payload.get("message", "Twelve Data returned an error")
                    if "limit" in message.lower() and attempt < self.max_retries:
                        time.sleep(self.sleep_seconds * attempt)
                        continue
                    raise ProviderError(message)
                return payload
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt == self.max_retries:
                    break
                time.sleep(self.sleep_seconds * attempt)
        raise ProviderError(f"Provider request failed after {self.max_retries} attempts: {last_error}")

    @staticmethod
    def _empty_frame() -> pd.DataFrame:
        return pd.DataFrame(columns=["datetime", "open", "high", "low", "close"])
