"""
returns_chart.py

Daily Returns chart for the Financial Risk ETL Dashboard.
"""

import plotly.express as px
import streamlit as st


# ----------------------------------------------------------
# Daily Returns
# ----------------------------------------------------------

def render_returns_chart(returns_df):
    """
    Renders the daily percentage return chart for the given
    (filtered) returns dataframe, one line per ticker.

    Parameters
    ----------
    returns_df : pd.DataFrame
        Filtered daily_returns data, as returned by
        utils.db_utils.filter_returns().
    """

    st.subheader("📊 Daily Returns")

    if returns_df.empty:
        st.info("No returns data available for the selected filters.")
        return

    fig = px.line(
        returns_df,
        x="trade_date",
        y="pct_return",
        color="ticker",
        title="Daily Percentage Return",
    )

    fig.add_hline(
        y=0,
        line_dash="dot",
        line_color="gray",
    )

    fig.update_layout(
        height=500,
        xaxis_title="Date",
        yaxis_title="Return (%)",
        legend_title="Ticker",
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)