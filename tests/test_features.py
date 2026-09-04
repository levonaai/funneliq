import pandas as pd

from analysis.features import RAW_FEATURE_COLUMNS, TARGET_COLUMNS, build_feature_matrix


def test_leakage_and_target_columns_excluded_from_features() -> None:
    assert "cumulative_profit" in TARGET_COLUMNS
    assert "ltv_months" in TARGET_COLUMNS
    assert not TARGET_COLUMNS & set(RAW_FEATURE_COLUMNS)


def test_build_feature_matrix_encodes_categoricals_and_drops_targets() -> None:
    df = pd.DataFrame(
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
            "purchased": [1],
            "upsell": [0],
            "referred": ["Yes"],
            "cumulative_profit": [9999.0],
            "ltv_months": [12.0],
        }
    )

    features = build_feature_matrix(df)

    assert "cumulative_profit" not in features.columns
    assert "ltv_months" not in features.columns
    assert features["referred"].iloc[0] == 1
    assert features["purchased"].dtype.kind == "i"
