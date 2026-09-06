"""Shared, cross-page interactive filters for the FunnelIQ dashboard.

`apply_filters` is pure and unit-tested directly (see
tests/test_dashboard_filters.py); `render_sidebar_filters` wraps it with
the actual sidebar widgets. Widget keys are fixed so a filter selection
made on one page carries over when the user switches to another page in
the same browser session - Streamlit re-runs the whole script per page, so
without shared keys each page would silently reset to its own defaults.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analysis.data_cleaning import (
    BUDGET_TIER_HIGH,
    BUDGET_TIER_LOW,
    BUDGET_TIER_MEDIUM,
    BUDGET_TIER_UNDEFINED,
    assign_budget_tier,
)

ALL_TIERS = [BUDGET_TIER_LOW, BUDGET_TIER_MEDIUM, BUDGET_TIER_HIGH, BUDGET_TIER_UNDEFINED]
YES_NO_ALL = ["All", "Yes", "No"]

FILTER_KEYS = ("filter_tiers", "filter_purchased", "filter_upsell", "filter_referred")


def apply_filters(df: pd.DataFrame, tiers: list[str], purchased: str, upsell: str, referred: str) -> pd.DataFrame:
    """Filter funnel rows by budget tier and the three Yes/No/All flags.

    `purchased`/`upsell`/`referred` are real booleans in `funnel_records`
    (see schema.sql, ingest_data.py) - "Yes"/"No" here are just the UI
    labels, mapped to True/False before comparing. An empty `tiers` list
    means "nothing selected", not "no filter" - it correctly yields zero
    rows rather than silently showing everything.
    """
    if not tiers:
        return df.iloc[0:0]

    filtered = df[assign_budget_tier(df["ad_budget"]).isin(tiers)]

    for column, choice in (("purchased", purchased), ("upsell", upsell), ("referred", referred)):
        if choice != "All":
            filtered = filtered[filtered[column] == (choice == "Yes")]

    return filtered


def render_sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Render the filter widgets in the sidebar and return the filtered rows.

    Call this once per page, right after loading the cleaned DataFrame -
    every chart/metric on the page should be computed from its return
    value, not from the unfiltered `df`.
    """
    with st.sidebar:
        st.header("🔍 Filters")
        tiers = st.multiselect(
            "Ad budget tier",
            options=ALL_TIERS,
            default=ALL_TIERS,
            key="filter_tiers",
            help="PRD tiers: Low <=1500, Medium 2000-5000, High >5000, Undefined 1500-2000.",
        )

        col1, col2 = st.columns(2)
        with col1:
            purchased = st.selectbox("Purchased", YES_NO_ALL, key="filter_purchased")
        with col2:
            upsell = st.selectbox("Upsold", YES_NO_ALL, key="filter_upsell")
        referred = st.selectbox("Referred", YES_NO_ALL, key="filter_referred")

        filtered = apply_filters(df, tiers, purchased, upsell, referred)

        st.divider()
        st.caption(f"**{len(filtered):,}** of **{len(df):,}** rows match the current filters.")
        if st.button("↺ Reset filters", width="stretch"):
            for key in FILTER_KEYS:
                st.session_state.pop(key, None)
            st.rerun()

    return filtered
