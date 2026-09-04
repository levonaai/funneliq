import numpy as np
import pandas as pd

from analysis.super_customer_score import (
    build_features_with_tier,
    cross_validated_score,
    grid_search,
)


def _make_clean_df(n: int = 60) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    ad_budget = rng.choice([800, 3000, 8000], size=n)
    referred = rng.integers(0, 2, size=n)
    return pd.DataFrame(
        {
            "ad_budget": ad_budget,
            "num_leads": rng.integers(10, 100, size=n),
            "leads_answered": rng.integers(5, 50, size=n),
            "leads_not_answered": rng.integers(1, 20, size=n),
            "followup_1": rng.integers(0, 20, size=n),
            "followup_2": rng.integers(0, 20, size=n),
            "followup_3": rng.integers(0, 20, size=n),
            "followup_4": rng.integers(0, 20, size=n),
            "followup_5": rng.integers(0, 20, size=n),
            "not_closed": rng.integers(0, 10, size=n),
            "closed": rng.integers(0, 10, size=n),
            "calls_to_closed": rng.integers(0, 10, size=n),
            "calls_to_not_closed": rng.integers(0, 10, size=n),
            "customer_acquisition_cost": rng.integers(500, 2000, size=n),
            "ltv_months": rng.uniform(1, 40, size=n),
            "purchased": rng.integers(0, 2, size=n),
            "upsell": rng.integers(0, 2, size=n),
            "referred": np.where(referred == 1, "Yes", "No"),
        }
    )


def test_build_features_with_tier_adds_categorical_column_and_drops_target() -> None:
    clean_df = _make_clean_df()
    X = build_features_with_tier(clean_df)

    assert "budget_tier" in X.columns
    assert "referred" not in X.columns
    assert set(X["budget_tier"].unique()) <= {
        "Low (<=1500)",
        "Medium (2000-5000)",
        "High (>5000)",
        "Undefined (1500-2000)",
    }


def test_cross_validated_score_returns_all_metrics() -> None:
    clean_df = _make_clean_df()
    X = build_features_with_tier(clean_df)
    y = (clean_df["referred"] == "Yes").astype(int)

    result = cross_validated_score({"learning_rate": 0.1, "depth": 3, "iterations": 20}, X, y)

    for key in ("accuracy", "precision", "recall", "f1", "roc_auc"):
        assert key in result


def test_grid_search_returns_sorted_results_for_small_grid() -> None:
    clean_df = _make_clean_df()
    X = build_features_with_tier(clean_df)
    y = (clean_df["referred"] == "Yes").astype(int)

    tiny_grid = {"learning_rate": [0.1], "depth": [3], "iterations": [20]}
    results = grid_search(X, y, param_grid=tiny_grid)

    assert len(results) == 1
    assert results[0]["learning_rate"] == 0.1
    assert "f1" in results[0]
