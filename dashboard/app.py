"""FunnelIQ Streamlit dashboard.

Currently shows the Work Package 5 follow-up funnel visual. Reuses the same
computation functions as analysis/followup_funnel.py (single source of
truth for the numbers), so the chart always matches
docs/followup_funnel_findings.md.

Run locally:

    streamlit run dashboard/app.py

NOTE: reads the local funnel_marketing_data.csv directly, same as the
analysis/ scripts - this is a placeholder data source. A deployed instance
needs the Supabase-backed read path (and the login UI) from Pillar 2 before
it can show real data in production; both are tracked as open gaps in the
README roadmap.
"""

from __future__ import annotations

from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from analysis.data_cleaning import clean, load_raw
from analysis.followup_funnel import (
    STAGES,
    avg_followup_cycles_for_closed,
    dropoff_rates,
    find_anomalous_stage,
    stage_totals,
)

CSV_PATH = "funnel_marketing_data.csv"

st.set_page_config(page_title="FunnelIQ Dashboard", page_icon="📊")
st.title("FunnelIQ - Follow-Up Funnel")

if not Path(CSV_PATH).exists():
    st.error(
        f"'{CSV_PATH}' not found. This local dashboard reads the raw dataset "
        "directly (same as the analysis/ scripts) - place the CSV in the "
        "project root to see the chart."
    )
    st.stop()

raw = load_raw(CSV_PATH)
clean_df, cleaning_report = clean(raw)

totals = stage_totals(clean_df)
rates = dropoff_rates(totals)
anomalous_stage = find_anomalous_stage(rates)
avg_cycles, verified = avg_followup_cycles_for_closed(clean_df)

st.caption(f"{cleaning_report.clean_rows} rows after cleaning (of {cleaning_report.raw_rows} raw).")

fig = go.Figure(
    go.Funnel(
        y=[s.replace("_", " ").title() for s in STAGES],
        x=[int(totals[s]) for s in STAGES],
        textinfo="value+percent initial",
    )
)
fig.update_layout(margin={"l": 10, "r": 10, "t": 10, "b": 10})
st.plotly_chart(fig, width="stretch")

col1, col2 = st.columns(2)
with col1:
    if anomalous_stage:
        prior_stage = STAGES[STAGES.index(anomalous_stage) - 1]
        st.metric(
            "Anomalous drop-off",
            f"{prior_stage} -> {anomalous_stage}",
            f"{rates[anomalous_stage]:.1%}",
            delta_color="inverse",
        )
    else:
        st.metric("Anomalous drop-off", "None detected")
with col2:
    st.metric("Avg. follow-up cycles for closed deals", f"{avg_cycles:.1f}")

st.subheader("Policy recommendation")
st.write(
    "Since no deal can close before completing all 5 follow-ups, the stage "
    "where drop-off unexpectedly *increases* is where the most-engaged "
    "remaining leads are being lost right before the point that determines "
    "whether they can close at all. Pilot a change specifically at that "
    "touchpoint (different channel, personal outreach, shorter gap) for a "
    "sample of leads and compare their stage-5 survival rate before rolling "
    "it out broadly."
)

st.caption("Full write-up: docs/followup_funnel_findings.md")
