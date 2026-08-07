# Financial Risk Data ETL Pipeline

A production-inspired ETL pipeline that extracts daily equity price data, validates and
transforms it into return/risk metrics, loads it into PostgreSQL, and surfaces it through
a monitoring dashboard. Built to demonstrate an end-to-end data engineering workflow —
extraction, validation, transformation, incremental loading, cross-source reconciliation,
automated testing, CI, and visualization.

## Overview

- **Data source:** [yfinance](https://pypi.org/project/yfinance/) (primary), with
  [Alpha Vantage](https://www.alphavantage.co/) used as an independent second source for
  cross-source reconciliation.
- **Tickers:** AAPL, MSFT, GOOGL, AMZN, NVDA
- **History:** 2 years of daily OHLCV data per ticker
- **Storage:** PostgreSQL, loaded incrementally (watermark-based upserts)
- **Orchestration:** a single-command pipeline runner, with GitHub Actions CI running tests
  on every push
- **Visualization:** a modular Streamlit dashboard for pipeline monitoring, data quality,
  and risk metrics

## Architecture

```
                extract.py
                    |
                    v
              validate.py  --> quarantined rows (failed checks)
                    |
                    v
              transform.py  (daily returns, moving averages, volatility, VaR)
                    |
                    v
                load.py  --> PostgreSQL (incremental / watermark-based)
                    |
                    v
            reconcile_sources.py  (yfinance vs Alpha Vantage cross-check)
                    |
                    v
              Streamlit dashboard  (dashboard/app.py)
```

All stages are wired together by `run_pipeline.py`, which also writes a row to
`pipeline_runs` for every execution (status, duration, row counts, reconciliation result) —
this is what the dashboard's Pipeline Monitoring panel reads from.

## Project Structure

```
finance-risk-etl-pipeline/
│
├── .github/
│   └── workflows/
│       └── ci.yml                  # Runs tests on push
│
├── src/
│   ├── extract.py                  # Pulls OHLCV data from yfinance per ticker
│   ├── validate.py                 # Schema, null, range, duplicate checks + quarantine
│   ├── transform.py                # Daily returns, moving averages, volatility, VaR
│   ├── load.py                     # Incremental/watermark load into PostgreSQL
│   ├── reconcile_sources.py        # yfinance vs Alpha Vantage cross-source reconciliation
│   └── run_pipeline.py             # End-to-end orchestrator
│
├── dashboard/
│   ├── app.py                      # Streamlit entry point
│   ├── components/                 # One file per dashboard section
│   │   ├── sidebar.py
│   │   ├── monitoring.py
│   │   ├── quality_panel.py
│   │   ├── kpi_cards.py
│   │   ├── price_chart.py
│   │   ├── returns_chart.py
│   │   ├── moving_average.py
│   │   ├── volatility_chart.py
│   │   ├── var_chart.py
│   │   ├── risk_table.py
│   │   └── database_summary.py
│   └── utils/
│       ├── db_utils.py             # Cached DB query + filter helpers
│       └── quality.py              # Data quality scoring
│
├── tests/
│   └── test_transform.py           # Pytest unit tests for transform logic
│
├── sql/
│   └── schema.sql                  # Table definitions
│
├── docs/
│   ├── data_mapping_doc.xlsx       # Source-to-target field mapping reference
│   ├── reconciliation_report.csv   # Extract-vs-load reconciliation output
│   └── cross_source_reconciliation_report.csv
│
├── data/
│   └── raw/                        # Timestamped raw CSV extracts
│
├── requirements.txt
├── .env                            # DATABASE_URL, ALPHA_VANTAGE_API_KEY (not committed)
└── README.md
```

## Setup

**1. Clone and enter the project**

```bash
git clone <your-repo-url>
cd finance-risk-etl-pipeline
```

**2. Create a virtual environment and install dependencies**

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configure environment variables**

Create a `.env` file in the project root:

```
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<database>
ALPHA_VANTAGE_API_KEY=<your_free_alpha_vantage_api_key>
```

**4. Create the database schema**

```powershell
psql -U <user> -d <database> -f sql/schema.sql
```

## Running the Pipeline

Run the full pipeline end to end:

```powershell
cd src
python run_pipeline.py
```

This will extract the latest data, validate it (quarantining anything that fails checks),
transform it into returns and risk metrics, and load it into PostgreSQL using incremental
upserts. A summary row is written to `pipeline_runs` on every execution.

Run cross-source reconciliation independently:

```powershell
python reconcile_sources.py
```

## Running Tests

```powershell
pytest tests/
```

5 unit tests cover daily return calculation, cross-ticker isolation, first-day-per-ticker
handling, historical VaR sign, and duplicate row removal.

## Running the Dashboard

```powershell
cd dashboard
streamlit run app.py
```

The dashboard includes:

- **Pipeline Monitoring** — latest run status, duration, rows loaded, validation errors, and
  an expandable run history
- **Data Quality** — a quality score with duplicate/null/missing-day/freshness breakdowns for
  the current filter selection
- **Key Metrics** — latest close price, daily return, 30-day volatility, and 95% VaR
- **Price & Returns charts** — closing price trend and daily percentage returns, all tickers
- **Risk charts** — moving averages, volatility, and VaR, per selected ticker
- **Risk Metrics table** and **Database Summary** — raw tabular views

## Data Quality & Reconciliation

- **Validation** (`validate.py`): schema, completeness, null, and range checks, plus
  duplicate detection. Rows failing any check are quarantined rather than loaded.
- **Internal reconciliation**: extracted row count vs. trusted row count, checked against a
  ±10 row tolerance band per run.
- **Cross-source reconciliation** (`reconcile_sources.py`): yfinance close prices are
  compared against Alpha Vantage close prices for overlapping dates, within a 0.5%
  tolerance, to catch source-level discrepancies that per-source validation can't detect.

See `docs/data_mapping_doc.xlsx` for the full source-to-target field mapping, derived-field
calculation logic, and the complete list of data quality rules.

## Design Notes

- **Incremental loading**: `load.py` uses a per-ticker watermark on `trade_date` for each of
  `raw_prices`, `daily_returns`, and `risk_metrics`, so re-running the pipeline only loads
  new rows instead of reprocessing the full history.
- **CI**: GitHub Actions runs the pytest suite on every push (`.github/workflows/ci.yml`).
- **Airflow was intentionally not used** for this project — CI plus the incremental/watermark
  loading logic cover the orchestration needs at this scale without the added operational
  overhead of a scheduler and metadata database.

## Tech Stack

Python · Pandas · SQLAlchemy · PostgreSQL · yfinance · Alpha Vantage API · Pytest ·
GitHub Actions · Streamlit · Plotly