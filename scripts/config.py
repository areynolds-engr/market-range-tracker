from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DOCS_DATA_DIR = PROJECT_ROOT / "docs" / "data"
CSV_PATH = DATA_DIR / "daily_ranges.csv"
JSON_PATH = DATA_DIR / "daily_ranges.json"
DOCS_JSON_PATH = DOCS_DATA_DIR / "daily_ranges.json"
NY_TIMEZONE = "America/New_York"
WINDOW_START = "08:00:00"
WINDOW_END = "08:30:00"
EXPECTED_BARS = 30
MIN_COMPLETE_BARS = 28


@dataclass(frozen=True)
class Instrument:
    display: str
    storage_symbol: str
    provider_symbol: str
    asset_type: str


INSTRUMENTS = (
    Instrument("NZD/USD", "NZDUSD", "NZD/USD", "forex"),
    Instrument("GBP/USD", "GBPUSD", "GBP/USD", "forex"),
    Instrument("AUD/USD", "AUDUSD", "AUD/USD", "forex"),
    Instrument("BTC/USD", "BTCUSD", "BTC/USD", "crypto"),
)


COLUMNS = [
    "date",
    "symbol",
    "window_start",
    "window_end",
    "open",
    "high",
    "low",
    "close",
    "range",
    "range_percent",
    "high_time",
    "low_time",
    "high_before_low",
    "bar_count",
    "status",
    "provider",
    "updated_at",
]
