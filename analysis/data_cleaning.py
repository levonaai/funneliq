"""Deterministic cleaning for funnel_marketing_data.csv.

Every rule below is reproducible (no randomness) and was chosen by first
inspecting the actual missingness pattern in the dataset, not applied
blindly:

1. Drop exact duplicate rows (10 in the current dataset).
2. `cumulative_profit` is null for 29 rows: 2 of them are non-purchasers
   (`purchased == 0`), and 335/337 non-purchaser rows already have
   `cumulative_profit == 0.0` - so those 2 are filled with 0.0 to match
   the established pattern for that group.
3. Any row still missing `cumulative_profit` (27 rows - purchasers with a
   genuinely missing profit figure) or `ltv_months` (4 rows, no clear
   default) is dropped. Inventing a specific number for either would bias
   the correlation analysis and later regression work, so dropping is the
   safer deterministic choice.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

BUDGET_TIER_LOW = "Low (<=1500)"
BUDGET_TIER_MEDIUM = "Medium (2000-5000)"
BUDGET_TIER_HIGH = "High (>5000)"
BUDGET_TIER_UNDEFINED = "Undefined (1500-2000)"


@dataclass(frozen=True)
class CleaningReport:
    raw_rows: int
    duplicates_dropped: int
    profit_zero_filled: int
    rows_dropped_missing_target: int
    clean_rows: int


def load_raw(csv_path: str) -> pd.DataFrame:
    return pd.read_csv(csv_path)


def clean(df: pd.DataFrame) -> tuple[pd.DataFrame, CleaningReport]:
    raw_rows = len(df)

    df = df.drop_duplicates()
    duplicates_dropped = raw_rows - len(df)

    zero_fill_mask = (df["purchased"] == 0) & df["cumulative_profit"].isna()
    profit_zero_filled = int(zero_fill_mask.sum())
    df = df.copy()
    df.loc[zero_fill_mask, "cumulative_profit"] = 0.0

    before_dropna = len(df)
    df = df.dropna(subset=["cumulative_profit", "ltv_months"])
    rows_dropped_missing_target = before_dropna - len(df)

    report = CleaningReport(
        raw_rows=raw_rows,
        duplicates_dropped=duplicates_dropped,
        profit_zero_filled=profit_zero_filled,
        rows_dropped_missing_target=rows_dropped_missing_target,
        clean_rows=len(df),
    )
    return df.reset_index(drop=True), report


def assign_budget_tier(ad_budget: pd.Series) -> pd.Series:
    """PRD-defined tiers: Low <=1500, Medium 2000-5000, High >5000.

    The 1500-2000 gap is intentionally left out of the PRD's definition;
    rows that fall in it are labelled separately rather than silently
    forced into a neighboring tier.
    """
    conditions = [
        ad_budget <= 1500,
        (ad_budget >= 2000) & (ad_budget <= 5000),
        ad_budget > 5000,
    ]
    choices = [BUDGET_TIER_LOW, BUDGET_TIER_MEDIUM, BUDGET_TIER_HIGH]
    return pd.Series(
        np.select(conditions, choices, default=BUDGET_TIER_UNDEFINED),
        index=ad_budget.index,
        name="budget_tier",
    )
