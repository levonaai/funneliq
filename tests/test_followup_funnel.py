import pandas as pd

from analysis.followup_funnel import (
    STAGES,
    avg_followup_cycles_for_closed,
    dropoff_rates,
    find_anomalous_stage,
    stage_totals,
)


def _make_clean_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "followup_1": [100, 80],
            "followup_2": [80, 60],
            "followup_3": [70, 50],
            "followup_4": [65, 45],
            "followup_5": [40, 20],
            "not_closed": [30, 15],
            "closed": [10, 5],
        }
    )


def test_stage_totals_sums_across_rows() -> None:
    totals = stage_totals(_make_clean_df())
    assert totals["followup_1"] == 180
    assert totals["followup_5"] == 60


def test_dropoff_rates_first_stage_is_nan_and_rest_are_fractions() -> None:
    totals = stage_totals(_make_clean_df())
    rates = dropoff_rates(totals)

    assert pd.isna(rates["followup_1"])
    for stage in STAGES[1:]:
        assert 0.0 <= rates[stage] <= 1.0


def test_find_anomalous_stage_detects_increase_in_dropoff() -> None:
    # drop-off shrinks 1->2->3, then jumps back up 3->4: anomaly at followup_4
    totals = pd.Series({"followup_1": 100, "followup_2": 80, "followup_3": 70, "followup_4": 40, "followup_5": 35})
    rates = dropoff_rates(totals)

    assert find_anomalous_stage(rates) == "followup_4"


def test_find_anomalous_stage_returns_none_when_monotonically_decreasing() -> None:
    totals = pd.Series({"followup_1": 100, "followup_2": 60, "followup_3": 50, "followup_4": 45, "followup_5": 43})
    rates = dropoff_rates(totals)

    assert find_anomalous_stage(rates) is None


def test_avg_followup_cycles_for_closed_is_five_when_identity_holds() -> None:
    avg_cycles, verified = avg_followup_cycles_for_closed(_make_clean_df())

    assert avg_cycles == 5.0
    assert verified is True


def test_avg_followup_cycles_flags_unverified_when_identity_breaks() -> None:
    df = _make_clean_df()
    df.loc[0, "followup_5"] = 999  # breaks followup_5 == not_closed + closed

    _, verified = avg_followup_cycles_for_closed(df)

    assert verified is False
