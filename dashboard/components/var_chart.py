"""
var_chart.py

Value at Risk (VaR) chart for the Financial Risk ETL Dashboard.
Plots the 95% VaR for a single selected ticker.
"""

import streamlit as st
import plotly.express as px


# ----------------------------------------------------------
# VaR Chart
# ----------------------------------------------------------

def render_var_chart(risk_df, ticker):
    """
    Renders the VaR (95%) chart for the current selection. Requires
    a single ticker, same rationale as moving_average.py /
    volatility_chart.py.

    Parameters
    ----------
    risk_df : pd.DataFrame     filtered risk_metrics
    ticker : str                 selected ticker ("All" or a symbol)
    """

    st.subheader("⚠️ Value at Risk (95%)")

    if ticker == "All":
        st.info("Select a single ticker in the sidebar to view VaR.")
        return

    if risk_df.empty:
        st.info("No data available for the selected filters.")
        return

    fig = px.line(
        risk_df,
        x="trade_date",
        y="var_95",
        title=f"{ticker} — Value at Risk (95%)",
    )

    fig.update_traces(line_color="#AB63FA")

    fig.update_layout(
        height=450,
        xaxis_title="Date",
        yaxis_title="VaR (%)",
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)