"""
price_chart.py

Closing Price Trend chart for the Financial Risk ETL Dashboard.
"""

import plotly.express as px
import streamlit as st


# ----------------------------------------------------------
# Closing Price Trend
# ----------------------------------------------------------

def render_price_chart(price_df):
    """
    Renders the closing price trend chart for the given (filtered)
    price dataframe, one line per ticker.

    Parameters
    ----------
    price_df : pd.DataFrame
        Filtered raw_prices data, as returned by
        utils.db_utils.filter_prices().
    """

    st.subheader("📈 Closing Price Trend")

    if price_df.empty:
        st.info("No price data available for the selected filters.")
        return

    fig = px.line(
        price_df,
        x="trade_date",
        y="close_price",
        color="ticker",
        title="Closing Price",
    )

    fig.update_layout(
        height=500,
        xaxis_title="Date",
        yaxis_title="Close Price ($)",
        legend_title="Ticker",
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)