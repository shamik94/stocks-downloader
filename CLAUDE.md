# Stan Beans Unloader

Stock market data downloader. Fetches historical OHLCV data for stocks across multiple countries and stores it in PostgreSQL. Runs on a weekday schedule via APScheduler.

## Architecture

```
src/
├── scheduler.py              # Entry point — schedules and triggers runs
├── service/
│   └── unloader_service.py  # All business logic: fetch, normalize, persist
├── mapper/
│   └── country_columns.py   # Column name mapping per data source
└── resources/stock_list/    # One file per country, one symbol per line
    ├── usa
    ├── india
    ├── crypto
    └── germany
```

**Data sources:**
- India → `jugaad_data` (NSE)
- USA / Crypto / Germany → `yfinance`

**Data flow:** `scheduler` → `unload_all(country)` → reads stock list → `unload(stock)` → `fetch_data` → `_normalize_columns` → `_save_stock_data` → PostgreSQL

Runs are incremental: each stock's latest stored date is queried first; only newer data is fetched.

## Running

```bash
# Docker (recommended)
docker-compose up --build

# Local dev
pip install -r requirements.txt
python src/scheduler.py
```

Database is auto-initialized on startup.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | Full Postgres URL (takes precedence over individual vars) |
| `DB_HOST` | `localhost` | Postgres host |
| `DB_PORT` | `5432` | Postgres port |
| `DB_NAME` | `stockdata` | Database name |
| `DB_USER` | `user` | Database user |
| `DB_PASSWORD` | `password` | Database password |
| `COUNTRIES` | `india,usa` | Comma-separated list of countries to process |
| `HISTORY_START_DATE` | `2020-01-01` | Earliest date for initial data load |
| `STOCK_START_ENABLED` | `false` | Set `true` to resume from a specific symbol |
| `STOCK_START_SYMBOL` | — | Symbol to resume from (skips everything before it) |

## Adding a New Country

1. Add a stock symbol file at `src/resources/stock_list/<country>` (one symbol per line).
2. Add a column mapping in `src/mapper/country_columns.py`. Countries using yfinance can reuse `_YFINANCE_COLUMNS`.
3. If the country uses a different data source, add a branch in `fetch_data()` in `unloader_service.py`.
4. Include the country in the `COUNTRIES` env var.

## Database Schema

Table `stock_data` (OHLCV, one row per symbol per trading day):

| Column | Type | Notes |
|---|---|---|
| `id` | integer | PK |
| `symbol` | string | Ticker symbol |
| `date` | date | Trading day |
| `open/high/low/close` | float | OHLC prices |
| `volume` | integer | Trading volume |
| `country` | string | Source country |

Table `stock_info` (metadata, one row per symbol; unique on `symbol` + `country`):

| Column | Type | Notes |
|---|---|---|
| `id` | integer | PK |
| `symbol` | string | Ticker symbol |
| `country` | string | Source country |
| `company_name` | string | Full company name |
| `sector` | string | Broad sector |
| `industry` | string | Specific industry |
| `market_cap` | float | Market capitalisation |
| `currency` | string | Trading currency |
| `exchange` | string | Exchange code |

Populated by running `python src/populate_stock_info.py` (not part of the scheduler or docker-compose up). For India stocks, yfinance is queried with a `.NS` suffix to retrieve metadata.

Table `stock_earnings` (one row per symbol per earnings date; unique on `symbol` + `country` + `earnings_date`):

| Column | Type | Notes |
|---|---|---|
| `id` | integer | PK |
| `symbol` | string | Ticker symbol |
| `country` | string | Source country |
| `earnings_date` | date | Earnings announcement date |
| `eps_estimate` | float | Analyst EPS estimate |
| `reported_eps` | float | Actual reported EPS (null for future dates) |
| `surprise_percent` | float | Surprise % vs estimate |

Sourced from yfinance's `Ticker.earnings_dates` (India uses `.NS` suffix). Runs alongside the daily OHLCV unload; upserts on conflict. Skipped for `crypto`.
