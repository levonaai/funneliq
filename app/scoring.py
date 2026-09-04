"""Backend scoring pipeline for Work Package 4 (Super-Customer Score).

Loads the CatBoost model trained by analysis/super_customer_score.py
(committed to models/super_customer_score.cbm - unlike the raw CSV, a
trained model artifact is small and safe to check in) and exposes a
0-100 likelihood score. Wired into the API as `POST /api/score-lead`.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier

from analysis.data_cleaning import assign_budget_tier

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "super_customer_score.cbm"


@lru_cache
def _get_model() -> CatBoostClassifier:
    model = CatBoostClassifier()
    model.load_model(str(MODEL_PATH))
    return model


def score_lead(features: dict) -> float:
    """Return a 0-100 'Super-Customer' likelihood score for one lead.

    `features` must cover the columns the model was trained on (see
    analysis/super_customer_score.build_features_with_tier); `budget_tier`
    is derived automatically from `ad_budget` if not supplied.
    """
    model = _get_model()
    row = pd.DataFrame([features])
    if "budget_tier" not in row.columns:
        row["budget_tier"] = assign_budget_tier(row["ad_budget"])

    proba = model.predict_proba(row[model.feature_names_])[:, 1][0]
    return round(float(np.clip(proba, 0.0, 1.0)) * 100, 1)
