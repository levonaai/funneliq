"""Shared feature engineering for the Work Package 2+ ML models.

`cumulative_profit` is deliberately excluded from every feature set: it is
only known after a customer's lifecycle has already played out, so using it
to predict an earlier-stage outcome (like `ltv_months` or `upsell`) leaks
the answer into the model. Such a model looks perfect in training and is
useless in production. `ltv_months` is excluded too since it is itself the
regression target in Work Package 2.
"""

from __future__ import annotations

import pandas as pd

TARGET_COLUMNS = {"ltv_months", "cumulative_profit"}

RAW_FEATURE_COLUMNS = [
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
    "purchased",
    "upsell",
    "referred",
]

assert not TARGET_COLUMNS & set(RAW_FEATURE_COLUMNS), "leakage/target column present in feature list"


def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    features = df[RAW_FEATURE_COLUMNS].copy()
    features["referred"] = features["referred"].map({"Yes": 1, "No": 0}).astype(int)
    features["purchased"] = features["purchased"].astype(int)
    features["upsell"] = features["upsell"].astype(int)
    return features
