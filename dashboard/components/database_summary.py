"""
database_summary.py

Database Summary component for the Financial Risk ETL Dashboard.
"""

import streamlit as st

from utils.db_utils import get_table_count


# ----------------------------------------------------------
# Database Summary
# ----------------------------------------------------------

def render_database_summary():
    """
    Renders the database summary table showing row counts for the
    core tables.
    """

    st.subheader("🗄 Database Summary")

    raw = get_table_count("raw_prices")
    returns = get_table_count("daily_returns")
    risk = get_table_count("risk_metrics")

    summary = {
        "Table": [
            "raw_prices",
            "daily_returns",
            "risk_metrics",
        ],
        "Rows": [
            raw,
            returns,
            risk,
        ],
    }

    st.table(summary)