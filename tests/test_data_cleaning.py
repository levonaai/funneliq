import pandas as pd

from analysis.data_cleaning import (
    BUDGET_TIER_HIGH,
    BUDGET_TIER_LOW,
    BUDGET_TIER_MEDIUM,
    BUDGET_TIER_UNDEFINED,
    assign_budget_tier,
    clean,
)


def _make_df(**overrides) -> pd.DataFrame:
    base = {
        # row 0 and 1 are exact duplicates (same values in every column).
        "ad_budget": [1000, 1000, 1000, 3000, 6000],
        "num_leads": [20, 20, 20, 40, 80],
        "purchased": [0, 0, 0, 1, 1],
        "cumulative_profit": [0.0, 0.0, None, 5000.0, None],
        "ltv_months": [5.0, 5.0, 5.0, 20.0, 30.0],
    }
    base.update(overrides)
    return pd.DataFrame(base)


def test_clean_drops_exact_duplicates() -> None:
    df = _make_df()
    clean_df, report = clean(df)

    assert report.raw_rows == 5
    assert report.duplicates_dropped == 1
    assert len(clean_df) == report.clean_rows


def test_clean_fills_zero_profit_for_non_purchasers_only() -> None:
    df = _make_df()
    clean_df, report = clean(df)

    assert report.profit_zero_filled == 1
    non_purchaser_rows = clean_df[clean_df["purchased"] == 0]
    assert (non_purchaser_rows["cumulative_profit"] == 0.0).all()


def test_clean_drops_rows_with_unrecoverable_missing_target() -> None:
    df = _make_df()
    clean_df, report = clean(df)

    # The 4th row (purchased=1, cumulative_profit=None) has no safe default
    # and must be dropped rather than imputed.
    assert report.rows_dropped_missing_target == 1
    assert clean_df["cumulative_profit"].isna().sum() == 0
    assert clean_df["ltv_months"].isna().sum() == 0


def test_assign_budget_tier_matches_prd_boundaries() -> None:
    budgets = pd.Series([1500, 2000, 5000, 5001, 1800])
    tiers = assign_budget_tier(budgets)

    assert list(tiers) == [
        BUDGET_TIER_LOW,
        BUDGET_TIER_MEDIUM,
        BUDGET_TIER_MEDIUM,
        BUDGET_TIER_HIGH,
        BUDGET_TIER_UNDEFINED,
    ]
