"""Work Package 6: interactive Budget Optimization Simulator page.

Reuses analysis/budget_optimizer.py directly so the numbers here always
match docs/budget_optimizer_findings.md.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from analysis.budget_optimizer import (
    DEFAULT_MONTHLY_BUDGET,
    MAX_CAMPAIGNS,
    MIN_CAMPAIGNS,
    build_profit_curve,
    simulate_equal_split,
    sweep_strategies,
)
from dashboard.auth import render_account_sidebar, require_login
from dashboard.data import load_clean_funnel_data
from dashboard.filters import render_sidebar_filters

st.set_page_config(page_title="FunnelIQ - Budget Simulator", page_icon="💰", layout="wide")

session = require_login()
render_account_sidebar(session)

st.title("💰 FunnelIQ — Budget Optimization Simulator")

try:
    clean_df, _ = load_clean_funnel_data(session["access_token"])
except Exception as exc:  # noqa: BLE001 - surface any Supabase/query failure to the user
    st.error(f"Could not load data from Supabase: {exc}")
    st.stop()

filtered_df = render_sidebar_filters(clean_df)
if filtered_df.empty:
    st.warning("No rows match the current filters - adjust or reset them in the sidebar.")
    st.stop()

curve = build_profit_curve(filtered_df)
if len(curve) < 2:
    st.warning(
        "The current filters leave too few distinct ad-budget levels to build a "
        "profit curve - widen the filters in the sidebar."
    )
    st.stop()

st.write(
    "Split a fixed monthly budget across a number of equal-sized "
    "campaigns and see the predicted total profit - concentrate into a "
    "few large campaigns, spread into many small ones, or something "
    "in between."
)

total_budget = st.number_input(
    "Monthly budget", min_value=10_000, max_value=200_000, value=DEFAULT_MONTHLY_BUDGET, step=5_000
)
n_campaigns = st.slider(
    "Number of campaigns",
    min_value=MIN_CAMPAIGNS,
    max_value=MAX_CAMPAIGNS,
    value=25,
    help="Budget is split equally across this many campaigns.",
)

selected = simulate_equal_split(total_budget, n_campaigns, curve)

with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    col1.metric("Budget per campaign", f"{selected['budget_per_campaign']:,.0f}")
    col2.metric("Predicted profit / campaign", f"{selected['predicted_profit_per_campaign']:,.0f}")
    col3.metric("Predicted total profit", f"{selected['total_predicted_profit']:,.0f}")

if not selected["within_historical_range"]:
    st.warning(
        "This per-campaign budget falls outside the range actually "
        "observed in the historical data - the prediction is extrapolated "
        "and less reliable."
    )

results = sweep_strategies(total_budget, curve)
best = results.loc[results["total_predicted_profit"].idxmax()]

# Categorical slots (line = blue, your selection = orange) plus the reserved
# "good" status color for the optimum, distinguished from the selection by
# shape (circle vs. star) as well as color - see the dataviz skill's
# CVD-separation check for this exact three-color combination.
CHART_FONT = {"family": "system-ui, -apple-system, Segoe UI, sans-serif", "color": "#0b0b0b"}
GRID_COLOR = "#e1e0d9"
AXIS_COLOR = "#c3c2b7"

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=results["n_campaigns"],
        y=results["total_predicted_profit"],
        mode="lines",
        name="Total predicted profit",
        line={"color": "#2a78d6", "width": 2},
    )
)
fig.add_trace(
    go.Scatter(
        x=[selected["n_campaigns"]],
        y=[selected["total_predicted_profit"]],
        mode="markers",
        marker={"size": 12, "color": "#eb6834"},
        name="Your selection",
    )
)
fig.add_trace(
    go.Scatter(
        x=[best["n_campaigns"]],
        y=[best["total_predicted_profit"]],
        mode="markers",
        marker={"size": 14, "symbol": "star", "color": "#0ca30c"},
        name="Best found",
    )
)
fig.update_layout(
    xaxis_title="Number of campaigns (fewer = more concentrated, more = more spread)",
    yaxis_title="Predicted total profit",
    margin={"l": 10, "r": 10, "t": 10, "b": 10},
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=CHART_FONT,
    legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
)
fig.update_xaxes(gridcolor=GRID_COLOR, zerolinecolor=AXIS_COLOR)
fig.update_yaxes(gridcolor=GRID_COLOR, zerolinecolor=AXIS_COLOR)
st.plotly_chart(fig, width="stretch")

st.divider()

with st.container(border=True):
    st.subheader("🏁 Bottom line")
    st.write(
        f"The best split found here is **{int(best['n_campaigns'])} campaigns of "
        f"{best['budget_per_campaign']:,.0f} each** (total predicted profit "
        f"{best['total_predicted_profit']:,.0f}). Profit is not monotonic in "
        "budget - campaigns in the 2,000-5,000 range historically outperform "
        "both smaller and larger ones by a wide margin, so neither pure "
        "concentration nor pure spread wins; a moderate number of "
        "medium-sized campaigns does."
    )

st.caption("Full write-up: docs/budget_optimizer_findings.md")
