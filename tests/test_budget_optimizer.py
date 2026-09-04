import pandas as pd

from analysis.budget_optimizer import (
    build_profit_curve,
    predict_profit,
    simulate_equal_split,
    sweep_strategies,
)


def _make_clean_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ad_budget": [1000, 1000, 3000, 3000, 8000, 8000],
            "cumulative_profit": [1000.0, 1200.0, 20000.0, 22000.0, 5000.0, 5400.0],
        }
    )


def test_build_profit_curve_averages_per_budget_level() -> None:
    curve = build_profit_curve(_make_clean_df())

    assert list(curve["ad_budget"]) == [1000, 3000, 8000]
    assert curve.loc[curve["ad_budget"] == 1000, "avg_profit"].iloc[0] == 1100.0
    assert curve.loc[curve["ad_budget"] == 3000, "avg_profit"].iloc[0] == 21000.0


def test_predict_profit_interpolates_between_known_levels() -> None:
    curve = build_profit_curve(_make_clean_df())

    # halfway between 1000 (avg 1100) and 3000 (avg 21000)
    mid = predict_profit(2000, curve)
    assert 1100.0 < mid < 21000.0


def test_predict_profit_clamps_outside_historical_range() -> None:
    curve = build_profit_curve(_make_clean_df())

    assert predict_profit(0, curve) == predict_profit(1000, curve)
    assert predict_profit(100_000, curve) == predict_profit(8000, curve)


def test_simulate_equal_split_computes_totals_and_range_flag() -> None:
    curve = build_profit_curve(_make_clean_df())

    result = simulate_equal_split(total_budget=6000, n_campaigns=2, curve=curve)

    assert result["n_campaigns"] == 2
    assert result["budget_per_campaign"] == 3000
    assert result["predicted_profit_per_campaign"] == 21000.0
    assert result["total_predicted_profit"] == 42000.0
    assert result["within_historical_range"] is True


def test_sweep_strategies_covers_requested_campaign_range() -> None:
    curve = build_profit_curve(_make_clean_df())

    results = sweep_strategies(total_budget=24000, curve=curve, min_campaigns=3, max_campaigns=8)

    assert list(results["n_campaigns"]) == list(range(3, 9))
    assert (results["total_predicted_profit"] > 0).all()
