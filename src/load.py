"""
load.py — incremental/delta loading for raw_prices, daily_returns, risk_metrics.
Each table gets its own per-ticker watermark (max trade_date already loaded),
so tables with different row counts (e.g. risk_metrics drops the 30-day warmup)
are each loaded correctly rather than sharing one watermark.
"""

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
engine = create_engine(os.getenv("DATABASE_URL"))

# table_name -> list of non-key columns to upsert
TABLE_CONFIGS = {
    "raw_prices": ["open_price", "high_price", "low_price", "close_price", "volume"],
    "daily_returns": ["pct_return"],
    "risk_metrics": ["ma_short", "ma_long", "volatility_30d", "var_95"],
}


def get_watermarks(table_name: str, tickers: list[str]) -> dict[str, pd.Timestamp | None]:
    """Latest trade_date already loaded per ticker for this table. None = not yet loaded."""
    watermarks = {t: None for t in tickers}
    query = text(f"""
        SELECT ticker, MAX(trade_date) AS max_date
        FROM {table_name}
        WHERE ticker = ANY(:tickers)
        GROUP BY ticker
    """)
    try:
        with engine.connect() as conn:
            rows = conn.execute(query, {"tickers": tickers}).fetchall()
        for ticker, max_date in rows:
            if max_date is not None:
                watermarks[ticker] = pd.Timestamp(max_date)
        logger.info(f"{table_name}: watermarks {watermarks}")
    except Exception as e:
        logger.warning(f"{table_name}: could not fetch watermarks (likely first run): {e}")
    return watermarks


def filter_incremental(df: pd.DataFrame, watermarks: dict) -> pd.DataFrame:
    """Keep only rows newer than each ticker's watermark. No watermark = keep all."""
    df = df.copy()
    df["trade_date"] = pd.to_datetime(df["trade_date"])

    keep_frames = []
    for ticker, group in df.groupby("ticker"):
        wm = watermarks.get(ticker)
        if wm is None:
            keep_frames.append(group)
        else:
            keep_frames.append(group[group["trade_date"] > wm])

    if not keep_frames:
        return df.iloc[0:0]
    return pd.concat(keep_frames, ignore_index=True)


def upsert_table(df: pd.DataFrame, table_name: str, value_cols: list[str]) -> int:
    """Upsert rows into table_name on (trade_date, ticker)."""
    if df.empty:
        logger.info(f"{table_name}: no new rows to load — up to date.")
        return 0

    cols = ["trade_date", "ticker"] + value_cols
    records = df[cols].to_dict(orient="records")

    col_list = ", ".join(cols)
    placeholders = ", ".join(f":{c}" for c in cols)
    set_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in value_cols)

    upsert_sql = text(f"""
        INSERT INTO {table_name} ({col_list})
        VALUES ({placeholders})
        ON CONFLICT (trade_date, ticker)
        DO UPDATE SET {set_clause}
    """)

    with engine.begin() as conn:
        conn.execute(upsert_sql, records)

    logger.info(f"{table_name}: upserted {len(records)} rows.")
    return len(records)


def run_load(tables: dict) -> dict:
    """Incrementally load raw_prices, daily_returns, risk_metrics. Returns rows loaded per table."""
    results = {}
    for table_name, value_cols in TABLE_CONFIGS.items():
        df = tables.get(table_name)
        if df is None or df.empty:
            logger.info(f"{table_name}: nothing to load.")
            results[table_name] = 0
            continue

        tickers = df["ticker"].unique().tolist()
        watermarks = get_watermarks(table_name, tickers)
        delta = filter_incremental(df, watermarks)
        results[table_name] = upsert_table(delta, table_name, value_cols)

    return results