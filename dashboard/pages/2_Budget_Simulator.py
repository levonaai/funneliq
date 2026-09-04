"""Work Package 6: interactive Budget Optimization Simulator page.

Reuses analysis/budget_optimizer.py directly so the numbers here always
match docs/budget_optimizer_findings.md.
"""

from __future__ import annotations

from pathlib import Path

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
from analysis.data_cleaning import clean, load_raw
from dashboard.auth import render_account_sidebar, require_login

CSV_PATH = "funnel_marketing_data.csv"

st.set_page_config(page_title="FunnelIQ - Budget Simulator", page_icon="💰")

session = require_login()
render_account_sidebar(session)

st.title("Budget Optimization Simulator")

if not Path(CSV_PATH).exists():
    st.error(f"'{CSV_PATH}' not found - this page needs the local dataset.")
    st.stop()

raw = load_raw(CSV_PATH)
clean_df, _ = clean(raw)
curve = build_profit_curve(clean_df)

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

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=results["n_campaigns"],
        y=results["total_predicted_profit"],
        mode="lines",
        name="Total predicted profit",
    )
)
fig.add_trace(
    go.Scatter(
        x=[selected["n_campaigns"]],
        y=[selected["total_predicted_profit"]],
        mode="markers",
        marker={"size": 12, "color": "orange"},
        name="Your selection",
    )
)
fig.add_trace(
    go.Scatter(
        x=[best["n_campaigns"]],
        y=[best["total_predicted_profit"]],
        mode="markers",
        marker={"size": 12, "symbol": "star", "color": "green"},
        name="Best found",
    )
)
fig.update_layout(
    xaxis_title="Number of campaigns (fewer = more concentrated, more = more spread)",
    yaxis_title="Predicted total profit",
    margin={"l": 10, "r": 10, "t": 10, "b": 10},
)
st.plotly_chart(fig, width="stretch")

st.subheader("Bottom line")
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
