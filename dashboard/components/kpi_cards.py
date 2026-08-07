"""
kpi_cards.py

Top-line KPI cards for the Financial Risk ETL Dashboard.
Summarizes the most recent close price, daily return, volatility,
and VaR for the current filter selection.
"""

import streamlit as st

from utils.db_utils import (
    latest_close_price,
    latest_return,
    latest_var,
    latest_volatility,
)


# ----------------------------------------------------------
# KPI Cards
# ----------------------------------------------------------

def render_kpi_cards(price_df, returns_df, risk_df, ticker):
    """
    Renders top-line KPI cards for the current selection.

    Parameters
    ----------
    price_df : pd.DataFrame    filtered raw_prices
    returns_df : pd.DataFrame  filtered daily_returns
    risk_df : pd.DataFrame     filtered risk_metrics
    ticker : str                selected ticker ("All" or a symbol)
    """

    st.subheader("📌 Key Metrics")

    if ticker == "All":
        st.caption(
            "Showing the latest value across all tickers combined. "
            "Select a single ticker in the sidebar for per-stock metrics."
        )

    close_price = latest_close_price(price_df)
    pct_return = latest_return(returns_df)
    volatility = latest_volatility(risk_df)
    var_95 = latest_var(risk_df)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Latest Close",
        f"${close_price:,.2f}" if close_price is not None else "N/A",
    )

    c2.metric(
        "Daily Return",
        f"{pct_return:+.2f}%" if pct_return is not None else "N/A",
        delta=f"{pct_return:+.2f}%" if pct_return is not None else None,
    )

    c3.metric(
        "30D Volatility",
        f"{volatility:.2f}%" if volatility is not None else "N/A",
    )

    c4.metric(
        "VaR (95%)",
        f"{var_95:.2f}%" if var_95 is not None else "N/A",
    )