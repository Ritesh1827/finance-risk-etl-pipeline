"""
reconcile_sources.py
Cross-source reconciliation: compares trusted yfinance closing prices
against an independent Alpha Vantage pull for the same tickers/dates.
This is what "reconciliation" means in a real risk/finance ETL context —
row-count checks (validate.py) confirm completeness, this confirms accuracy.
"""

import logging
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(PROJECT_ROOT / ".env")
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
TOLERANCE_PCT = 0.5  # allowed % difference between sources before flagging a mismatch
RATE_LIMIT_SLEEP = 13  # free tier: 5 calls/min -> ~12s between calls, +1s buffer


def fetch_alpha_vantage(ticker: str) -> pd.DataFrame | None:
    """Pull daily close prices for one ticker from Alpha Vantage (free tier: last ~100 days)."""
    if not API_KEY:
        raise RuntimeError("ALPHA_VANTAGE_API_KEY not found in .env")

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "outputsize": "compact",   # <-- changed from "full" — free tier no longer supports full history
        "apikey": API_KEY,
    }
    # ... rest of the function is unchanged

    try:
        resp = requests.get(ALPHA_VANTAGE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        series = data.get("Time Series (Daily)")
        if not series:
            logger.warning(f"{ticker}: no Alpha Vantage data returned (msg: {data.get('Note') or data.get('Information') or data})")
            return None

        df = (
            pd.DataFrame.from_dict(series, orient="index")
            .rename(columns={"4. close": "av_close"})[["av_close"]]
            .reset_index()
            .rename(columns={"index": "Date"})
        )
        df["Date"] = pd.to_datetime(df["Date"])
        df["av_close"] = pd.to_numeric(df["av_close"], errors="coerce")
        df["ticker"] = ticker

        logger.info(f"{ticker}: fetched {len(df)} rows from Alpha Vantage.")
        return df

    except Exception as e:
        logger.error(f"{ticker}: Alpha Vantage fetch failed: {e}")
        return None


def fetch_all_alpha_vantage(tickers: list[str]) -> pd.DataFrame:
    """Loop tickers with rate-limit sleeps, skip failures instead of stopping."""
    frames = []
    failed = []

    for i, ticker in enumerate(tickers):
        df = fetch_alpha_vantage(ticker)
        if df is not None:
            frames.append(df)
        else:
            failed.append(ticker)

        if i < len(tickers) - 1:
            time.sleep(RATE_LIMIT_SLEEP)

    if failed:
        logger.warning(f"Alpha Vantage: failed tickers skipped: {failed}")

    if not frames:
        raise RuntimeError("Alpha Vantage: all tickers failed, cannot reconcile.")

    return pd.concat(frames, ignore_index=True)


def reconcile(yf_trusted: pd.DataFrame, av_data: pd.DataFrame, tolerance_pct: float = TOLERANCE_PCT) -> pd.DataFrame:
    """
    Compare yfinance close vs Alpha Vantage close on (Date, ticker).
    Returns a full comparison DataFrame with a match flag and % difference.
    """
    yf = yf_trusted[["Date", "ticker", "Close"]].copy()
    yf["Date"] = pd.to_datetime(yf["Date"])

    merged = yf.merge(av_data, on=["Date", "ticker"], how="inner")

    merged["pct_diff"] = ((merged["Close"] - merged["av_close"]).abs() / merged["av_close"]) * 100
    merged["match"] = merged["pct_diff"] <= tolerance_pct

    unmatched_dates = yf.merge(av_data, on=["Date", "ticker"], how="left", indicator=True)
    missing_in_av = unmatched_dates[unmatched_dates["_merge"] == "left_only"]

    logger.info(
        f"Reconciled {len(merged)} overlapping (Date, ticker) rows "
        f"(Alpha Vantage free tier limits this to ~last 100 trading days per ticker): "
        f"{merged['match'].sum()} matched, {(~merged['match']).sum()} mismatched "
        f"(tolerance: {tolerance_pct}%)."
    )
    if len(missing_in_av):
        logger.warning(f"{len(missing_in_av)} yfinance rows had no Alpha Vantage counterpart (date not covered by AV pull).")

    return merged


def run_cross_source_reconciliation(yf_trusted: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    av_data = fetch_all_alpha_vantage(tickers)
    report = reconcile(yf_trusted, av_data)

    out_path = DOCS_DIR / "cross_source_reconciliation_report.csv"
    report.to_csv(out_path, index=False)
    logger.info(f"Cross-source reconciliation report written to {out_path}")

    mismatches = report[~report["match"]]
    if len(mismatches):
        logger.warning(f"{len(mismatches)} mismatched rows — see report for detail.")

    return report


if __name__ == "__main__":
    from extract import run_extraction, TICKERS
    from validate import validate

    raw = run_extraction()
    result = validate(raw, TICKERS)
    run_cross_source_reconciliation(result.trusted, TICKERS)