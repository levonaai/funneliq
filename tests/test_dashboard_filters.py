import pandas as pd

from analysis.data_cleaning import BUDGET_TIER_HIGH, BUDGET_TIER_LOW, BUDGET_TIER_MEDIUM
from dashboard.filters import ALL_TIERS, apply_filters


def _make_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ad_budget": [1000, 3000, 8000, 3000],
            "purchased": [True, True, False, False],
            "upsell": [True, False, False, False],
            "referred": [False, True, False, False],
        }
    )


def test_apply_filters_defaults_keep_all_rows() -> None:
    filtered = apply_filters(_make_df(), ALL_TIERS, "All", "All", "All")
    assert len(filtered) == 4


def test_apply_filters_empty_tier_selection_yields_no_rows() -> None:
    filtered = apply_filters(_make_df(), [], "All", "All", "All")
    assert filtered.empty


def test_apply_filters_by_budget_tier() -> None:
    filtered = apply_filters(_make_df(), [BUDGET_TIER_LOW], "All", "All", "All")
    assert list(filtered["ad_budget"]) == [1000]

    filtered = apply_filters(_make_df(), [BUDGET_TIER_MEDIUM], "All", "All", "All")
    assert list(filtered["ad_budget"]) == [3000, 3000]

    filtered = apply_filters(_make_df(), [BUDGET_TIER_HIGH], "All", "All", "All")
    assert list(filtered["ad_budget"]) == [8000]


def test_apply_filters_by_boolean_flags() -> None:
    filtered = apply_filters(_make_df(), ALL_TIERS, "Yes", "All", "All")
    assert list(filtered["purchased"]) == [True, True]

    filtered = apply_filters(_make_df(), ALL_TIERS, "All", "Yes", "All")
    assert list(filtered["upsell"]) == [True]

    filtered = apply_filters(_make_df(), ALL_TIERS, "All", "All", "No")
    assert list(filtered["referred"]) == [False, False, False]


def test_apply_filters_combines_all_conditions() -> None:
    filtered = apply_filters(_make_df(), [BUDGET_TIER_MEDIUM], "All", "All", "Yes")
    assert list(filtered["ad_budget"]) == [3000]
    assert list(filtered["referred"]) == [True]
