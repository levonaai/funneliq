import pandas as pd

from analysis.features import (
    ALL_MODELING_COLUMNS,
    LEAKAGE_COLUMNS,
    build_feature_matrix,
)


def test_leakage_column_never_in_modeling_columns() -> None:
    assert LEAKAGE_COLUMNS == {"cumulative_profit"}
    assert not LEAKAGE_COLUMNS & set(ALL_MODELING_COLUMNS)


def _make_row() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ad_budget": [1000],
            "num_leads": [20],
            "leads_answered": [10],
            "leads_not_answered": [10],
            "followup_1": [5],
            "followup_2": [4],
            "followup_3": [3],
            "followup_4": [2],
            "followup_5": [1],
            "not_closed": [3],
            "closed": [2],
            "calls_to_closed": [2],
            "calls_to_not_closed": [3],
            "customer_acquisition_cost": [500],
            "ltv_months": [12.0],
            "purchased": [1],
            "upsell": [0],
            "referred": ["Yes"],
            "cumulative_profit": [9999.0],
        }
    )


def test_build_feature_matrix_always_drops_cumulative_profit() -> None:
    features = build_feature_matrix(_make_row())

    assert "cumulative_profit" not in features.columns
    assert "ltv_months" in features.columns
    assert "upsell" in features.columns


def test_build_feature_matrix_drops_requested_target() -> None:
    features = build_feature_matrix(_make_row(), exclude={"ltv_months"})

    assert "ltv_months" not in features.columns
    assert "cumulative_profit" not in features.columns


def test_build_feature_matrix_encodes_categoricals() -> None:
    features = build_feature_matrix(_make_row())

    assert features["referred"].iloc[0] == 1
    assert features["purchased"].dtype.kind == "i"
    assert features["upsell"].dtype.kind == "i"
