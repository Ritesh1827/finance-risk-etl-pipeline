"""
moving_average.py

Moving Average chart for the Financial Risk ETL Dashboard.
Overlays short/long moving averages on the closing price for a
single selected ticker.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ----------------------------------------------------------
# Moving Average Chart
# ----------------------------------------------------------

def render_moving_average(price_df, risk_df, ticker):
    """
    Renders a closing price chart overlaid with short/long moving
    averages.

    Parameters
    ----------
    price_df : pd.DataFrame    filtered raw_prices
    risk_df : pd.DataFrame     filtered risk_metrics (has ma_short, ma_long)
    ticker : str                 selected ticker ("All" or a symbol)
    """

    st.subheader("📉 Moving Averages")

    if ticker == "All":
        st.info("Select a single ticker in the sidebar to view moving averages.")
        return

    if price_df.empty or risk_df.empty:
        st.info("No data available for the selected filters.")
        return

    merged = pd.merge(
        price_df[["trade_date", "ticker", "close_price"]],
        risk_df[["trade_date", "ticker", "ma_short", "ma_long"]],
        on=["trade_date", "ticker"],
        how="inner",
    )

    if merged.empty:
        st.info("No overlapping price/risk data for the selected range.")
        return

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=merged["trade_date"],
            y=merged["close_price"],
            mode="lines",
            name="Close Price",
            line=dict(color="#636EFA"),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=merged["trade_date"],
            y=merged["ma_short"],
            mode="lines",
            name="Short MA",
            line=dict(color="#00CC96", dash="dot"),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=merged["trade_date"],
            y=merged["ma_long"],
            mode="lines",
            name="Long MA",
            line=dict(color="#EF553B", dash="dot"),
        )
    )

    fig.update_layout(
        height=500,
        title=f"{ticker} — Price vs Moving Averages",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)