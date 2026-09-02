# Market Range Tracker

A GitHub-hosted project that tracks the 08:00-08:30 America/New_York market range for:

- NZD/USD
- GBP/USD
- AUD/USD
- BTC/USD

Python downloads and processes market data. GitHub Actions runs the daily update. GitHub Pages hosts a static dashboard from generated JSON, so no Python web server is needed.

## Project layout

```text
.
├── .github/workflows/update-market-data.yml
├── data/
│   ├── daily_ranges.csv
│   ├── daily_ranges.json
│   └── raw/
├── docs/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── data/daily_ranges.json
├── scripts/
│   ├── backfill.py
│   ├── update_daily.py
│   ├── data_provider.py
│   ├── ranges.py
│   └── storage.py
└── tests/
```

## Data provider

Version 1 uses Twelve Data through `scripts/data_provider.py`.

The provider requests 1-minute candles with `timezone=America/New_York`, `start_date`, and `end_date`. Symbols are configured as:

| Display | Stored symbol | Twelve Data symbol |
| --- | --- | --- |
| NZD/USD | NZDUSD | NZD/USD |
| GBP/USD | GBPUSD | GBP/USD |
| AUD/USD | AUDUSD | AUD/USD |
| BTC/USD | BTCUSD | BTC/USD |

Important plan note: Twelve Data plan limits vary by account, including API credits, rate limits, and historical intraday depth. A free or entry-level plan may not provide one full year of 1-minute history for every symbol. The code is restart-safe, skips missing sessions, and marks short windows as `incomplete` instead of inventing data.

## Local setup

1. Create a Twelve Data API key.
2. Copy `.env.example` values into your shell:

```sh
export TWELVE_DATA_API_KEY="your_key_here"
```

3. Install dependencies:

```sh
python3 -m pip install -r requirements.txt
```

4. Run tests:

```sh
python3 -m unittest discover -s tests
```

## Backfill roughly one year

```sh
python3 scripts/backfill.py --days 365
```

The backfill:

- processes dates from about 365 calendar days ago through today
- skips forex weekends
- attempts BTC/USD every day
- updates existing date/symbol rows instead of duplicating them
- writes `data/daily_ranges.csv`, `data/daily_ranges.json`, and `docs/data/daily_ranges.json`

## Daily update

```sh
python3 scripts/update_daily.py
```

The daily script uses today in America/New_York and refuses to save before 08:45 New York time. This gives the provider a little time to finalize the 08:00-08:30 window.

## GitHub secret

In your GitHub repository:

1. Open Settings.
2. Open Secrets and variables.
3. Open Actions.
4. Add a repository secret named `TWELVE_DATA_API_KEY`.
5. Paste your Twelve Data API key as the value.

Never commit API keys to the repository.

## GitHub Pages

The dashboard lives in `docs/`.

In GitHub:

1. Open Settings.
2. Open Pages.
3. Set the source to deploy from a branch.
4. Select your main branch and the `/docs` folder.

The dashboard reads `docs/data/daily_ranges.json`, which is copied from the canonical `data/daily_ranges.json` whenever the scripts save.

## Automation

`.github/workflows/update-market-data.yml` runs daily at 09:00 America/New_York and can also be run manually with `workflow_dispatch`.

The workflow:

- checks out the repository
- installs Python dependencies
- reads `TWELVE_DATA_API_KEY` from GitHub Secrets
- runs the daily update
- runs tests
- commits only if the generated data files changed

## Stored fields

Each date/symbol row contains:

`date`, `symbol`, `window_start`, `window_end`, `open`, `high`, `low`, `close`, `range`, `range_percent`, `high_time`, `low_time`, `high_before_low`, `bar_count`, `status`, `provider`, `updated_at`.

The unique logical key is `date + symbol`.
