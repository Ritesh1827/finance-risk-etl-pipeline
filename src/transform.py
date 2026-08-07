"""
transform.py
Consumes validate.py's trusted DataFrame and produces three
schema-aligned outputs: raw_prices, daily_returns, risk_metrics.
"""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

VOL_WINDOW = 30       # rolling volatility window (trading days)
MA_SHORT = 7          # short moving average
MA_LONG = 30           # long moving average
VAR_WINDOW = 30        # rolling VaR window
VAR_CONFIDENCE = 0.95  # 95% historical VaR


def clean_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Sort, dedupe, and enforce dtypes on the trusted price data."""
    df = df.copy()

    df["Date"] = pd.to_datetime(df["Date"])
    df["ticker"] = df["ticker"].str.upper().str.strip()

    numeric_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    before = len(df)
    df = df.drop_duplicates(subset=["Date", "ticker"])
    dropped = before - len(df)
    if dropped:
        logger.info(f"Dropped {dropped} duplicate (Date, ticker) rows during clean.")

    df = df.sort_values(["ticker", "Date"]).reset_index(drop=True)

    logger.info(f"Cleaned prices: {len(df)} rows across {df['ticker'].nunique()} tickers.")
    return df


def build_raw_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Map cleaned data onto the raw_prices target schema."""
    out = df.rename(
        columns={
            "Date": "trade_date",
            "Open": "open_price",
            "High": "high_price",
            "Low": "low_price",
            "Close": "close_price",
            "Volume": "volume",
        }
    )[["trade_date", "ticker", "open_price", "high_price", "low_price", "close_price", "volume"]]
    return out


def build_daily_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Per-ticker daily pct return. groupby ensures no bleed across ticker boundaries."""
    df = df.copy()
    df["pct_return"] = df.groupby("ticker")["Close"].pct_change()

    out = df.rename(columns={"Date": "trade_date"})[["trade_date", "ticker", "pct_return"]]
    out = out.dropna(subset=["pct_return"]).reset_index(drop=True)

    logger.info(f"Computed daily returns: {len(out)} rows (first day per ticker dropped, no prior close).")
    return out


def historical_var(returns: pd.Series, confidence: float = VAR_CONFIDENCE) -> float:
    """5th percentile of the return distribution -> reported as a positive loss figure."""
    if returns.count() < 2:
        return np.nan
    quantile = 1 - confidence
    var = returns.quantile(quantile)
    return -var  # convention: VaR reported as a positive number representing potential loss


def build_risk_metrics(df: pd.DataFrame, returns_df: pd.DataFrame) -> pd.DataFrame:
    """Rolling volatility, moving averages, and rolling historical VaR — all per ticker."""
    price = df.copy()
    ret = returns_df.copy()

    # Moving averages on price, per ticker
    price["ma_short"] = price.groupby("ticker")["Close"].transform(
        lambda s: s.rolling(window=MA_SHORT, min_periods=MA_SHORT).mean()
    )
    price["ma_long"] = price.groupby("ticker")["Close"].transform(
        lambda s: s.rolling(window=MA_LONG, min_periods=MA_LONG).mean()
    )

    # Rolling volatility + rolling VaR on returns, per ticker
    ret["volatility_30d"] = ret.groupby("ticker")["pct_return"].transform(
        lambda s: s.rolling(window=VOL_WINDOW, min_periods=VOL_WINDOW).std()
    )
    ret["var_95"] = ret.groupby("ticker")["pct_return"].transform(
        lambda s: s.rolling(window=VAR_WINDOW, min_periods=VAR_WINDOW).apply(historical_var, raw=False)
    )

    merged = price.rename(columns={"Date": "trade_date"})[
        ["trade_date", "ticker", "ma_short", "ma_long"]
    ].merge(
        ret[["trade_date", "ticker", "volatility_30d", "var_95"]],
        on=["trade_date", "ticker"],
        how="inner",
    )

    merged = merged.dropna(subset=["ma_long", "volatility_30d", "var_95"]).reset_index(drop=True)

    logger.info(
        f"Computed risk metrics: {len(merged)} rows "
        f"(rows before the {max(MA_LONG, VOL_WINDOW, VAR_WINDOW)}-day warmup window per ticker are dropped)."
    )
    return merged


def run_transformation(trusted: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Entry point: trusted DataFrame in, three schema-ready DataFrames out."""
    cleaned = clean_prices(trusted)

    raw_prices = build_raw_prices(cleaned)
    daily_returns = build_daily_returns(cleaned)
    risk_metrics = build_risk_metrics(cleaned, daily_returns)

    return {
        "raw_prices": raw_prices,
        "daily_returns": daily_returns,
        "risk_metrics": risk_metrics,
    }


if __name__ == "__main__":
    from extract import run_extraction, TICKERS
    from validate import validate

    raw = run_extraction()
    result = validate(raw, TICKERS)
    tables = run_transformation(result.trusted)

    for name, tbl in tables.items():
        logger.info(f"{name}: shape={tbl.shape}")
        out_path = DOCS_DIR.parent / "data" / f"{name}_sample.csv"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tbl.head(20).to_csv(out_path, index=False)
        logger.info(f"Sample written to {out_path}")