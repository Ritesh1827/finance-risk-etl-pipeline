"""
tests/test_transform.py
Minimal unit tests on transform.py's core logic — not full coverage,
just enough to prove correctness of the calculations that matter most.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from transform import clean_prices, build_daily_returns, historical_var


@pytest.fixture
def sample_prices():
    """Two tickers, 3 days each, hand-crafted so returns are easy to verify by hand."""
    return pd.DataFrame({
        "Date": ["2024-01-01", "2024-01-02", "2024-01-03"] * 2,
        "Open": [100, 102, 104, 50, 51, 49] ,
        "High": [101, 103, 105, 51, 52, 50],
        "Low": [99, 101, 103, 49, 50, 48],
        "Close": [100, 102, 105, 50, 51, 49],
        "Volume": [1000, 1100, 1200, 2000, 2100, 2200],
        "ticker": ["AAA", "AAA", "AAA", "BBB", "BBB", "BBB"],
    })


def test_daily_return_calculation_is_correct(sample_prices):
    """Manually verify: AAA day2 return = (102-100)/100 = 0.02"""
    cleaned = clean_prices(sample_prices)
    returns = build_daily_returns(cleaned)

    aaa_day2 = returns[(returns["ticker"] == "AAA")].iloc[0]
    assert round(aaa_day2["pct_return"], 4) == 0.02


def test_returns_do_not_bleed_across_tickers(sample_prices):
    """The first row of ticker BBB must NOT compute a return against AAA's last close."""
    cleaned = clean_prices(sample_prices)
    returns = build_daily_returns(cleaned)

    # BBB's first return should be (51-50)/50 = 0.02, NOT computed against AAA's close of 105
    bbb_first = returns[returns["ticker"] == "BBB"].iloc[0]
    assert round(bbb_first["pct_return"], 4) == 0.02


def test_first_day_per_ticker_has_no_return(sample_prices):
    """First day per ticker should be dropped (no prior close to compare against)."""
    cleaned = clean_prices(sample_prices)
    returns = build_daily_returns(cleaned)

    # 2 tickers x 3 days = 6 rows in, minus 1 dropped first-day row per ticker = 4 rows out
    assert len(returns) == 4


def test_historical_var_is_positive_for_losses():
    """VaR should be reported as a positive number representing potential loss."""
    returns = pd.Series([-0.05, -0.03, -0.01, 0.01, 0.02, 0.03, 0.04])
    var = historical_var(returns, confidence=0.95)

    assert var > 0  # sign convention: positive = potential loss magnitude


def test_clean_prices_removes_duplicates():
    """Duplicate (Date, ticker) rows should be dropped during cleaning."""
    df = pd.DataFrame({
        "Date": ["2024-01-01", "2024-01-01"],
        "Open": [100, 100],
        "High": [101, 101],
        "Low": [99, 99],
        "Close": [100, 100],
        "Volume": [1000, 1000],
        "ticker": ["AAA", "AAA"],
    })
    cleaned = clean_prices(df)
    assert len(cleaned) == 1