"""Shared feature engineering for the Work Package 2+ ML models.

`cumulative_profit` is permanently excluded from every feature set: it is
only known after a customer's lifecycle has already played out, so using it
to predict an earlier-stage outcome (like `ltv_months` or `upsell`) leaks
the answer into the model. Such a model looks perfect in training and is
useless in production.

Every other column (including `ltv_months`) is a legitimate feature *unless
it is the current task's own prediction target* - e.g. Work Package 2
predicts `ltv_months`, so it must be excluded there, but Work Package 3
predicts `upsell` and is free to use `ltv_months` as a feature (the PRD's
own suggested business heuristic does exactly that). Callers pass whichever
column(s) are their target via `exclude`.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

LEAKAGE_COLUMNS = {"cumulative_profit"}

ALL_MODELING_COLUMNS = [
    "ad_budget",
    "num_leads",
    "leads_answered",
    "leads_not_answered",
    "followup_1",
    "followup_2",
    "followup_3",
    "followup_4",
    "followup_5",
    "not_closed",
    "closed",
    "calls_to_closed",
    "calls_to_not_closed",
    "customer_acquisition_cost",
    "ltv_months",
    "purchased",
    "upsell",
    "referred",
]

assert not LEAKAGE_COLUMNS & set(ALL_MODELING_COLUMNS), "leakage column present in modeling columns"


def build_feature_matrix(df: pd.DataFrame, exclude: Iterable[str] = ()) -> pd.DataFrame:
    exclude = set(exclude)
    columns = [c for c in ALL_MODELING_COLUMNS if c not in exclude]
    features = df[columns].copy()

    if "referred" in features.columns:
        features["referred"] = features["referred"].map({"Yes": 1, "No": 0}).astype(int)
    if "purchased" in features.columns:
        features["purchased"] = features["purchased"].astype(int)
    if "upsell" in features.columns:
        features["upsell"] = features["upsell"].astype(int)

    return features
