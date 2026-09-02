from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd

from scripts.config import COLUMNS, CSV_PATH, DOCS_JSON_PATH, JSON_PATH


def load_records(csv_path: Path = CSV_PATH) -> pd.DataFrame:
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return pd.DataFrame(columns=COLUMNS)
    frame = pd.read_csv(csv_path)
    for column in COLUMNS:
        if column not in frame.columns:
            frame[column] = None
    return frame[COLUMNS]


def merge_records(new_records: list[dict], csv_path: Path = CSV_PATH) -> pd.DataFrame:
    existing = load_records(csv_path)
    incoming = pd.DataFrame(new_records, columns=COLUMNS)
    if incoming.empty:
        return existing.sort_values(["date", "symbol"]).reset_index(drop=True)
    if existing.empty:
        merged = incoming
    else:
        merged = pd.concat([existing, incoming], ignore_index=True)
    merged = merged.drop_duplicates(subset=["date", "symbol"], keep="last")
    return merged.sort_values(["date", "symbol"]).reset_index(drop=True)


def save_records(frame: pd.DataFrame, csv_path: Path = CSV_PATH, json_path: Path = JSON_PATH) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    docs_json_path = DOCS_JSON_PATH if json_path == JSON_PATH else json_path.parent / "docs_daily_ranges.json"
    frame = frame.reindex(columns=COLUMNS).sort_values(["date", "symbol"]).reset_index(drop=True)
    frame.to_csv(csv_path, index=False)
    records = json.loads(frame.to_json(orient="records"))
    payload = {
        "schema_version": 1,
        "unique_key": ["date", "symbol"],
        "records": records,
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if json_path == JSON_PATH:
        docs_json_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(json_path, docs_json_path)
