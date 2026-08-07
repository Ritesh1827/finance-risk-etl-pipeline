"""
volatility_chart.py

Volatility chart for the Financial Risk ETL Dashboard.
Plots the 30-day rolling volatility for a single selected ticker.
"""

import streamlit as st
import plotly.express as px


# ----------------------------------------------------------
# Volatility Chart
# ----------------------------------------------------------

def render_volatility_chart(risk_df, ticker):
    """
    Renders the 30-day rolling volatility chart for the current
    selection. Requires a single ticker (same rationale as
    moving_average.py: overlaying multiple tickers' volatility
    bands is hard to read as line-on-line).

    Parameters
    ----------
    risk_df : pd.DataFrame     filtered risk_metrics
    ticker : str                 selected ticker ("All" or a symbol)
    """

    st.subheader("🌪️ Volatility (30D)")

    if ticker == "All":
        st.info("Select a single ticker in the sidebar to view volatility.")
        return

    if risk_df.empty:
        st.info("No data available for the selected filters.")
        return

    fig = px.area(
        risk_df,
        x="trade_date",
        y="volatility_30d",
        title=f"{ticker} — 30-Day Rolling Volatility",
    )

    fig.update_traces(
        line_color="#EF553B",
        fillcolor="rgba(239, 85, 59, 0.2)",
    )

    fig.update_layout(
        height=450,
        xaxis_title="Date",
        yaxis_title="Volatility (%)",
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)