"""
risk_table.py

Latest Risk Metrics table for the Financial Risk ETL Dashboard.
"""

import streamlit as st


# ----------------------------------------------------------
# Latest Risk Metrics
# ----------------------------------------------------------

def render_risk_table(risk_df):
    """
    Renders the risk metrics table for the given (filtered) risk
    dataframe.

    Parameters
    ----------
    risk_df : pd.DataFrame
        Filtered risk_metrics data, as returned by
        utils.db_utils.filter_risk().
    """

    st.subheader("📋 Latest Risk Metrics")

    if risk_df.empty:
        st.info("No risk data available for the selected filters.")
        return

    st.dataframe(
        risk_df,
        hide_index=True,
        use_container_width=True,
    )