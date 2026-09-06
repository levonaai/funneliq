"""FunnelIQ Streamlit dashboard.

Shows the Work Package 5 follow-up funnel visual. Reuses the same
computation functions as analysis/followup_funnel.py (single source of
truth for the numbers), so the chart always matches
docs/followup_funnel_findings.md.

Run locally (must be `python -m streamlit run`, not bare `streamlit run`
- on Linux the bare console script doesn't add the repo root to Python's
import path, so `from analysis... import` fails there):

    python -m streamlit run dashboard/app.py

Gated behind Supabase email/password sign-in (dashboard/auth.py), per
Pillar 2. Reads live data from the `funnel_records` table via the signed-in
user's own JWT (dashboard/data.py) - RLS applies exactly as it would for
any other authenticated client.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from analysis.followup_funnel import (
    STAGES,
    avg_followup_cycles_for_closed,
    dropoff_rates,
    find_anomalous_stage,
    stage_totals,
)
from dashboard.auth import render_account_sidebar, require_login
from dashboard.data import load_clean_funnel_data
from dashboard.filters import render_sidebar_filters

st.set_page_config(page_title="FunnelIQ Dashboard", page_icon="📊", layout="wide")

session = require_login()
render_account_sidebar(session)

st.title("📊 FunnelIQ — Follow-Up Funnel")

try:
    clean_df, cleaning_report = load_clean_funnel_data(session["access_token"])
except Exception as exc:  # noqa: BLE001 - surface any Supabase/query failure to the user
    st.error(f"Could not load data from Supabase: {exc}")
    st.stop()

filtered_df = render_sidebar_filters(clean_df)
if filtered_df.empty:
    st.warning("No rows match the current filters - adjust or reset them in the sidebar.")
    st.stop()

totals = stage_totals(filtered_df)
rates = dropoff_rates(totals)
anomalous_stage = find_anomalous_stage(rates)
avg_cycles, verified = avg_followup_cycles_for_closed(filtered_df)

st.caption(
    f"{cleaning_report.clean_rows} rows after cleaning (of {cleaning_report.raw_rows} raw) - "
    f"{len(filtered_df):,} shown after filters."
)

# Ordinal blue ramp, lightest -> darkest as the funnel narrows (validated
# colorblind-safe and >=2:1 against the light surface at the lightest step -
# see dataviz skill's ordinal-ramp check).
FUNNEL_STAGE_COLORS = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]
CHART_FONT = {"family": "system-ui, -apple-system, Segoe UI, sans-serif", "color": "#0b0b0b"}

fig = go.Figure(
    go.Funnel(
        y=[s.replace("_", " ").title() for s in STAGES],
        x=[int(totals[s]) for s in STAGES],
        textinfo="value+percent initial",
        marker={"color": FUNNEL_STAGE_COLORS},
        connector={"line": {"color": "#c3c2b7", "width": 1}},
    )
)
fig.update_layout(
    margin={"l": 10, "r": 10, "t": 10, "b": 10},
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=CHART_FONT,
)
st.plotly_chart(fig, width="stretch")

with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        if anomalous_stage:
            prior_stage = STAGES[STAGES.index(anomalous_stage) - 1]
            st.metric(
                "Anomalous drop-off",
                f"{prior_stage} -> {anomalous_stage}",
                f"{rates[anomalous_stage]:.1%}",
                delta_color="inverse",
                help="The one stage-to-stage transition where drop-off jumps back up instead of continuing to fall.",
            )
        else:
            st.metric("Anomalous drop-off", "None detected")
    with col2:
        st.metric(
            "Avg. follow-up cycles for closed deals",
            f"{avg_cycles:.1f}",
            help="Number of follow-up stages a deal completes, on average, before it closes.",
        )

st.divider()

with st.container(border=True):
    st.subheader("💡 Policy recommendation")
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
