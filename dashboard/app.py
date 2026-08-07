"""
app.py

Financial Risk ETL Dashboard — entry point.
Wires together the sidebar filters and all dashboard components.
"""

import streamlit as st

from components.sidebar import render_sidebar
from components.monitoring import render_monitoring
from components.quality_panel import render_quality_panel
from components.kpi_cards import render_kpi_cards
from components.price_chart import render_price_chart
from components.returns_chart import render_returns_chart
from components.moving_average import render_moving_average
from components.volatility_chart import render_volatility_chart
from components.var_chart import render_var_chart
from components.risk_table import render_risk_table
from components.database_summary import render_database_summary

from utils.db_utils import (
    latest_prices,
    latest_returns,
    latest_risk,
    filter_prices,
    filter_returns,
    filter_risk,
)


# ----------------------------------------------------------
# Page Config
# ----------------------------------------------------------

st.set_page_config(
    page_title="Financial Risk ETL Dashboard",
    page_icon="📊",
    layout="wide",
)


# ----------------------------------------------------------
# Header
# ----------------------------------------------------------

st.title("📊 Financial Risk ETL Dashboard")

st.caption(
    "Production-inspired monitoring dashboard for the Financial Risk ETL Platform"
)

st.divider()


# ----------------------------------------------------------
# Sidebar Filters
# ----------------------------------------------------------

filters = render_sidebar()

ticker = filters["ticker"]
start_date = filters["start_date"]
end_date = filters["end_date"]


# ----------------------------------------------------------
# Load + Filter Data
# ----------------------------------------------------------

price_df = filter_prices(latest_prices(), ticker, start_date, end_date)
returns_df = filter_returns(latest_returns(), ticker, start_date, end_date)
risk_df = filter_risk(latest_risk(), ticker, start_date, end_date)


# ----------------------------------------------------------
# Pipeline Monitoring
# ----------------------------------------------------------

render_monitoring()

st.divider()


# ----------------------------------------------------------
# Data Quality
# ----------------------------------------------------------

render_quality_panel(price_df)

st.divider()


# ----------------------------------------------------------
# Key Metrics
# ----------------------------------------------------------

render_kpi_cards(price_df, returns_df, risk_df, ticker)

st.divider()


# ----------------------------------------------------------
# Price & Returns Charts
# ----------------------------------------------------------

render_price_chart(price_df)

render_returns_chart(returns_df)

st.divider()


# ----------------------------------------------------------
# Risk Charts
# ----------------------------------------------------------

render_moving_average(price_df, risk_df, ticker)

render_volatility_chart(risk_df, ticker)

render_var_chart(risk_df, ticker)

st.divider()


# ----------------------------------------------------------
# Risk Table
# ----------------------------------------------------------

render_risk_table(risk_df)

st.divider()


# ----------------------------------------------------------
# Database Summary
# ----------------------------------------------------------

render_database_summary()