"""
extract.py
Extraction stage of the Financial Risk Data ETL Pipeline.

Downloads daily OHLCV data for a configured list of tickers via yfinance,
tags each row with its ticker, combines results into a single DataFrame,
and writes the raw output to disk. Failed ticker downloads are logged and
skipped so a single bad ticker never halts the pipeline.
"""

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
PERIOD = "2y"
INTERVAL = "1d"

RAW_DATA_DIR = Path("data/raw")
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("extract")


# --------------------------------------------------------------------------
# Core functions
# --------------------------------------------------------------------------

def download_ticker(ticker: str, period: str = PERIOD, interval: str = INTERVAL) -> pd.DataFrame | None:
    """
    Download OHLCV data for a single ticker.

    Returns a DataFrame tagged with a 'ticker' column, or None if the
    download failed or returned no data.
    """
    logger.info(f"Downloading {ticker} ({period}, {interval})...")

    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
    except Exception as e:
        logger.error(f"Failed to download {ticker}: {e}")
        return None

    if df is None or df.empty:
        logger.warning(f"No data returned for {ticker}. Skipping.")
        return None

    # yfinance can return MultiIndex columns even for a single ticker
    # in some versions — flatten defensively so downstream stages
    # always see simple column names.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    df["ticker"] = ticker

    logger.info(f"Downloaded {len(df)} rows for {ticker}.")
    return df


def extract_all(tickers: list[str] = TICKERS) -> pd.DataFrame:
    """
    Download data for all configured tickers, skipping any that fail.

    Returns a single combined DataFrame across all successful tickers.
    Raises RuntimeError if every ticker fails, since an empty extraction
    should not be allowed to silently continue into later stages.
    """
    frames = []
    failed_tickers = []

    for ticker in tickers:
        df = download_ticker(ticker)
        if df is not None:
            frames.append(df)
        else:
            failed_tickers.append(ticker)

    if failed_tickers:
        logger.warning(f"Failed/skipped tickers: {failed_tickers}")

    if not frames:
        raise RuntimeError("Extraction failed for all tickers. Aborting pipeline.")

    combined = pd.concat(frames, ignore_index=True)
    logger.info(
        f"Combined extraction complete: {len(combined)} total rows "
        f"across {len(frames)}/{len(tickers)} tickers."
    )
    return combined


def save_raw(df: pd.DataFrame, out_dir: Path = RAW_DATA_DIR) -> Path:
    """
    Persist the combined raw extract to disk as the 'landing zone' file,
    timestamped so each pipeline run keeps its own snapshot.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"raw_prices_{timestamp}.csv"
    df.to_csv(out_path, index=False)
    logger.info(f"Raw data written to {out_path}")
    return out_path


# --------------------------------------------------------------------------
# Entry point for standalone testing of this stage
# --------------------------------------------------------------------------

def run_extraction() -> pd.DataFrame:
    """Runs the full extraction stage and returns the combined DataFrame."""
    combined = extract_all(TICKERS)
    save_raw(combined)
    return combined


if __name__ == "__main__":
    run_extraction()