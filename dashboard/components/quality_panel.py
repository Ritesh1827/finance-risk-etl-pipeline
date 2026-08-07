"""
quality_panel.py

Data Quality panel for the Financial Risk ETL Dashboard.
Surfaces the quality score/status plus underlying checks for the
currently filtered price data.
"""

import streamlit as st

from utils.quality import calculate_quality


# ----------------------------------------------------------
# Status -> Color Mapping
# ----------------------------------------------------------

_STATUS_COLORS = {
    "Excellent": "🟢",
    "Good": "🟢",
    "Warning": "🟠",
    "Poor": "🔴",
}


# ----------------------------------------------------------
# Data Quality Panel
# ----------------------------------------------------------

def render_quality_panel(price_df):
    """
    Renders the data quality panel for the given (filtered) price
    dataframe.

    Parameters
    ----------
    price_df : pd.DataFrame
        Filtered raw_prices data, as returned by
        utils.db_utils.filter_prices().
    """

    st.subheader("🧪 Data Quality")

    if price_df.empty:
        st.warning("No data available for the selected filters.")
        return

    quality = calculate_quality(price_df)

    status_icon = _STATUS_COLORS.get(quality["status"], "⚪")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Quality Score", f"{quality['score']} / 100")
    c2.metric("Status", f"{status_icon} {quality['status']}")
    c3.metric("Duplicates", quality["duplicates"])
    c4.metric("Nulls", quality["nulls"])
    c5.metric("Missing Trading Days", quality["missing_days"])

    if quality["freshness"] is not None:
        if quality["freshness"] <= 1:
            st.caption(f"✅ Data is fresh (last updated {quality['freshness']} day(s) ago).")
        elif quality["freshness"] <= 5:
            st.caption(f"⚠️ Data is {quality['freshness']} day(s) old.")
        else:
            st.caption(f"🔴 Data is stale — {quality['freshness']} day(s) old.")

    if quality["status"] in ("Warning", "Poor"):
        st.warning(
            "Data quality is below the expected threshold for this "
            "selection. Review the pipeline's validation and "
            "reconciliation reports before relying on these metrics."
        )