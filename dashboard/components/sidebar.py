"""
sidebar.py

Sidebar filters for the Financial Risk ETL Dashboard.
Renders ticker + date range controls and returns the selected values
so the rest of the app can filter its data consistently.
"""

import datetime

import streamlit as st

from utils.db_utils import get_tickers


# ----------------------------------------------------------
# Sidebar Filters
# ----------------------------------------------------------

def render_sidebar():
    """
    Renders the sidebar controls and returns the selected filters.

    Returns
    -------
    dict with keys:
        ticker : str        ("All" or a specific ticker symbol)
        start_date : date
        end_date : date
    """

    st.sidebar.title("🔎 Filters")

    st.sidebar.divider()

    # --------------------------------------------------
    # Ticker Selector
    # --------------------------------------------------

    tickers = get_tickers()

    ticker_options = ["All"] + tickers

    selected_ticker = st.sidebar.selectbox(
        "Ticker",
        options=ticker_options,
        index=0,
    )

    st.sidebar.divider()

    # --------------------------------------------------
    # Date Range Selector
    # --------------------------------------------------

    st.sidebar.subheader("Date Range")

    today = datetime.date.today()
    default_start = today - datetime.timedelta(days=90)

    date_range = st.sidebar.date_input(
        "Select range",
        value=(default_start, today),
    )

    # date_input returns a single date until the user picks
    # a second one — guard against that so downstream code
    # always gets a (start, end) pair.
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = default_start, today

    st.sidebar.divider()

    # --------------------------------------------------
    # Refresh Control
    # --------------------------------------------------

    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.caption(
        f"Showing data from **{start_date}** to **{end_date}**"
    )

    return {
        "ticker": selected_ticker,
        "start_date": start_date,
        "end_date": end_date,
    }