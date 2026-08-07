"""
monitoring.py

Pipeline Monitoring component for the Financial Risk ETL Dashboard.
Shows the status of the most recent pipeline run plus a collapsible
history of past runs.
"""

import streamlit as st

from utils.db_utils import latest_pipeline_run, pipeline_history


# ----------------------------------------------------------
# Pipeline Monitoring
# ----------------------------------------------------------

def render_monitoring():
    """
    Renders the pipeline monitoring section: latest run status,
    key metrics, and an expandable run history table.
    """

    st.subheader("🚀 Pipeline Monitoring")

    run_df = latest_pipeline_run()

    if run_df.empty:
        st.warning("No pipeline runs found yet.")
        return

    run = run_df.iloc[0]

    status = "🟢 SUCCESS" if run["status"] == "SUCCESS" else "🔴 FAILED"

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Pipeline Status", status)
    c2.metric("Execution Time", f"{run['duration_seconds']:.2f} sec")
    c3.metric("Rows Loaded", int(run["loaded_rows"]))
    c4.metric("Validation Errors", int(run["validation_errors"]))

    st.caption(
        f"Last Run: **{run['end_time']}**  |  "
        f"Reconciliation: **{run['reconciliation_status']}**"
    )

    if run["status"] != "SUCCESS":
        st.error(
            "The most recent pipeline run did not complete successfully. "
            "Check pipeline logs before trusting downstream metrics."
        )

    # --------------------------------------------------
    # Run History
    # --------------------------------------------------

    with st.expander("📜 View recent pipeline run history"):

        history_df = pipeline_history(limit=20)

        if history_df.empty:
            st.caption("No run history available.")
        else:
            st.dataframe(
                history_df,
                hide_index=True,
                use_container_width=True,
            )