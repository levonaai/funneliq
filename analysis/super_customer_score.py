"""Work Package 4: Super-Customer Score - classification on `referred`.

CatBoost only (not the 3-model comparison used in WP2/WP3): the PRD asks
specifically for CatBoost's native categorical handling of a new
`budget_tier` feature, and its hyperparameter names (`depth`, `iterations`)
are CatBoost's own, not XGBoost's/LightGBM's.

Reads the local funnel_marketing_data.csv (gitignored), runs a small grid
search over (learning_rate, depth, iterations), trains the best
configuration on the full cleaned dataset, and saves the model to
models/super_customer_score.cbm (committed - the backend scoring endpoint
in app/scoring.py loads it at request time). Writes
docs/super_customer_score_findings.md. Re-run any time the CSV changes:

    python -m analysis.super_customer_score

CAVEAT worth flagging explicitly: this dataset's rows are campaign/cohort
aggregates (num_leads, closed, followups, ...), not individual-lead
records. A "new lead" in the literal sense wouldn't yet have values for
mid/late-funnel columns like `closed` or `purchased`. The PRD's scoring
pipeline is implemented against the same feature schema used for training
(matching its literal instructions), but in a real deployment the intake
form for a genuinely brand-new lead should only ask for the subset of
fields actually known at that time.
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier

from analysis.data_cleaning import assign_budget_tier, clean, load_raw
from analysis.features import build_feature_matrix
from analysis.upsell_classification import (
    classification_metrics,
    stratified_k_fold_splits,
)

CSV_PATH = "funnel_marketing_data.csv"
OUTPUT_PATH = Path("docs/super_customer_score_findings.md")
MODEL_PATH = Path("models/super_customer_score.cbm")
TARGET = "referred"
N_FOLDS = 5
RANDOM_STATE = 42
CAT_FEATURES = ["budget_tier"]

PARAM_GRID = {
    "learning_rate": [0.03, 0.05, 0.1],
    "depth": [4, 6],
    "iterations": [200, 400],
}


def build_features_with_tier(clean_df: pd.DataFrame) -> pd.DataFrame:
    """Feature matrix for this task, plus a categorical `budget_tier` column
    left as a raw string - CatBoost handles it natively via `cat_features`,
    no manual one-hot/ordinal encoding needed."""
    X = build_feature_matrix(clean_df, exclude={TARGET}).copy()
    X["budget_tier"] = assign_budget_tier(clean_df["ad_budget"]).to_numpy()
    return X


def _make_model(params: dict) -> CatBoostClassifier:
    return CatBoostClassifier(
        learning_rate=params["learning_rate"],
        depth=params["depth"],
        iterations=params["iterations"],
        cat_features=CAT_FEATURES,
        random_seed=RANDOM_STATE,
        auto_class_weights="Balanced",
        verbose=False,
    )


def cross_validated_score(params: dict, X: pd.DataFrame, y: pd.Series) -> dict:
    y_values = y.to_numpy()
    fold_metrics = []
    for train_idx, test_idx in stratified_k_fold_splits(y_values, N_FOLDS, RANDOM_STATE):
        model = _make_model(params)
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        scores = model.predict_proba(X.iloc[test_idx])[:, 1]
        preds = (scores >= 0.5).astype(int)
        fold_metrics.append(classification_metrics(y_values[test_idx], preds, scores))
    return {k: float(np.mean([m[k] for m in fold_metrics])) for k in fold_metrics[0]}


def grid_search(X: pd.DataFrame, y: pd.Series, param_grid: dict | None = None) -> list[dict]:
    grid = param_grid if param_grid is not None else PARAM_GRID
    keys = list(grid.keys())
    results = []
    for values in itertools.product(*grid.values()):
        params = dict(zip(keys, values, strict=True))
        metrics = cross_validated_score(params, X, y)
        results.append({**params, **metrics})
    return sorted(results, key=lambda r: r["f1"], reverse=True)


def score_leads(leads: pd.DataFrame, model_path: Path = MODEL_PATH) -> pd.Series:
    """Return a 0-100 'Super-Customer' likelihood score for each row.

    `leads` must contain the columns used at training time (see
    `build_features_with_tier`), or an `ad_budget` column from which
    `budget_tier` can be derived if it's missing.
    """
    model = CatBoostClassifier()
    model.load_model(str(model_path))

    leads = leads.copy()
    if "budget_tier" not in leads.columns:
        leads["budget_tier"] = assign_budget_tier(leads["ad_budget"])

    proba = model.predict_proba(leads[model.feature_names_])[:, 1]
    return pd.Series(np.round(proba * 100, 1), index=leads.index, name="super_customer_score")


def render_report(grid_results: list[dict], n_rows: int) -> str:
    best = grid_results[0]
    param_keys = list(PARAM_GRID.keys())

    lines = ["# Work Package 4: Super-Customer Score Findings", ""]
    lines += [
        (
            f"Target: `referred` (binary - did the customer refer someone "
            f"else). Rows used: {n_rows}. CatBoost only, using its native "
            "categorical handling for a new `budget_tier` feature "
            "(Low/Medium/High, no manual encoding). Stratified "
            f"{N_FOLDS}-fold CV for every grid point."
        ),
        "",
        "## Hyperparameter search",
        "",
        "| " + " | ".join(param_keys) + " | Accuracy | Precision | Recall | F1 | ROC-AUC |",
        "|" + "---|" * (len(param_keys) + 5),
    ]
    for r in grid_results:
        param_cells = " | ".join(str(r[k]) for k in param_keys)
        lines.append(
            f"| {param_cells} | {r['accuracy']:.3f} | {r['precision']:.3f} | "
            f"{r['recall']:.3f} | {r['f1']:.3f} | {r['roc_auc']:.3f} |"
        )
    lines.append("")

    best_param_str = ", ".join(f"{k}={best[k]}" for k in param_keys)
    lines += [
        f"**Best configuration** ({best_param_str}): F1={best['f1']:.3f}, ROC-AUC={best['roc_auc']:.3f}.",
        "",
        (
            "This configuration is retrained on the full cleaned dataset and "
            f"saved to `{MODEL_PATH}` for the scoring pipeline "
            "(`app/scoring.py`, `POST /api/score-lead`)."
        ),
        "",
        (
            "**Caveat**: this dataset's rows are campaign/cohort aggregates, "
            "not individual-lead records, so several training features "
            "(e.g. `closed`, `purchased`) describe outcomes a genuinely new "
            "lead wouldn't have yet. See this module's docstring."
        ),
        "",
    ]

    return "\n".join(lines)


def main() -> None:
    if not Path(CSV_PATH).exists():
        print(f"CSV not found at '{CSV_PATH}' - super-customer scoring needs the local dataset.", file=sys.stderr)
        sys.exit(1)

    raw = load_raw(CSV_PATH)
    clean_df, _ = clean(raw)

    X = build_features_with_tier(clean_df)
    y = (clean_df[TARGET] == "Yes").astype(int)

    grid_results = grid_search(X, y)
    best_params = {k: grid_results[0][k] for k in PARAM_GRID}

    final_model = _make_model(best_params)
    final_model.fit(X, y)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    final_model.save_model(str(MODEL_PATH))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_report(grid_results, len(clean_df)), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} and {MODEL_PATH} ({len(clean_df)} rows).")


if __name__ == "__main__":
    main()
