"""Work Package 2: LTV (`ltv_months`) regression - XGBoost, LightGBM, CatBoost.

Reads the local funnel_marketing_data.csv (gitignored) and writes
docs/ltv_regression_findings.md. Re-run any time the CSV changes:

    python -m analysis.ltv_regression

CRITICAL DATA LEAKAGE GUARD: `cumulative_profit` is never used as a feature
here (see analysis/features.py) - it is only known after a customer's
lifecycle ends, so including it would leak the answer and produce a model
that looks perfect in training but is useless in production.

NOTE: XGBoost and LightGBM are used via their native `Booster` APIs
(`xgb.train`/`lgb.train`) rather than the sklearn-compatible wrapper
classes (`XGBRegressor`/`LGBMRegressor`). Those wrappers hard-require a
working `import sklearn`, which transitively imports scipy.optimize's
HiGHS solver - a compiled extension blocked by Windows Smart App Control on
this machine. The native APIs don't have that dependency. CatBoost's
regressor class works standalone and needs no such workaround.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from catboost import CatBoostRegressor

from analysis.data_cleaning import clean, load_raw
from analysis.features import build_feature_matrix

CSV_PATH = "funnel_marketing_data.csv"
OUTPUT_PATH = Path("docs/ltv_regression_findings.md")
TARGET = "ltv_months"
N_FOLDS = 5
RANDOM_STATE = 42
TOP_N_FEATURES = 8


class _XGBoostNative:
    """Thin fit/predict/feature_importances_ adapter over xgb.train."""

    def __init__(self, num_boost_round: int = 300, **params):
        self.num_boost_round = num_boost_round
        self.params = params
        self.booster: xgb.Booster | None = None
        self.feature_names: list[str] | None = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> _XGBoostNative:
        self.feature_names = list(X.columns)
        dtrain = xgb.DMatrix(X, label=y, feature_names=self.feature_names)
        self.booster = xgb.train(self.params, dtrain, num_boost_round=self.num_boost_round)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.booster.predict(xgb.DMatrix(X, feature_names=self.feature_names))

    @property
    def feature_importances_(self) -> np.ndarray:
        scores = self.booster.get_score(importance_type="gain")
        return np.array([scores.get(f, 0.0) for f in self.feature_names])


class _LightGBMNative:
    """Thin fit/predict/feature_importances_ adapter over lgb.train."""

    def __init__(self, num_boost_round: int = 300, **params):
        self.num_boost_round = num_boost_round
        self.params = params
        self.booster: lgb.Booster | None = None

    def fit(self, X: pd.DataFrame, y: pd.Series) -> _LightGBMNative:
        train_set = lgb.Dataset(X, label=y, feature_name=list(X.columns))
        self.booster = lgb.train(self.params, train_set, num_boost_round=self.num_boost_round)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.booster.predict(X)

    @property
    def feature_importances_(self) -> np.ndarray:
        return self.booster.feature_importance(importance_type="gain")


MODEL_FACTORIES: dict[str, Callable] = {
    "XGBoost": lambda: _XGBoostNative(
        num_boost_round=300,
        max_depth=4,
        eta=0.05,
        objective="reg:squarederror",
        seed=RANDOM_STATE,
        verbosity=0,
    ),
    "LightGBM": lambda: _LightGBMNative(
        num_boost_round=300,
        max_depth=4,
        learning_rate=0.05,
        objective="regression",
        seed=RANDOM_STATE,
        verbose=-1,
    ),
    "CatBoost": lambda: CatBoostRegressor(
        iterations=300, depth=4, learning_rate=0.05, random_seed=RANDOM_STATE, verbose=False
    ),
}


def _k_fold_splits(n_samples: int, n_folds: int, random_state: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """Shuffled K-fold index splits, implemented directly with numpy.

    Avoids a scikit-learn dependency: importing sklearn transitively pulls in
    scipy.optimize's HiGHS solver, whose compiled extension is blocked by
    Windows Smart App Control on this machine - a system security policy
    that should not be worked around, so the (small) CV/metric logic it
    would have provided is implemented here instead.
    """
    rng = np.random.default_rng(random_state)
    shuffled = rng.permutation(n_samples)
    folds = np.array_split(shuffled, n_folds)
    return [
        (np.concatenate([folds[j] for j in range(n_folds) if j != i]), folds[i])
        for i in range(n_folds)
    ]


def _rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return float(1 - ss_res / ss_tot)


def cross_validate(model_name: str, factory: Callable, X: pd.DataFrame, y: pd.Series) -> dict:
    rmses: list[float] = []
    r2s: list[float] = []
    importances = np.zeros(X.shape[1])
    y_values = y.to_numpy()

    for train_idx, test_idx in _k_fold_splits(len(X), N_FOLDS, RANDOM_STATE):
        model = factory()
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        preds = np.asarray(model.predict(X.iloc[test_idx]))

        rmses.append(_rmse(y_values[test_idx], preds))
        r2s.append(_r2(y_values[test_idx], preds))
        importances += np.asarray(model.feature_importances_, dtype=float)

    importances /= N_FOLDS
    return {
        "model": model_name,
        "rmse_mean": float(np.mean(rmses)),
        "rmse_std": float(np.std(rmses)),
        "r2_mean": float(np.mean(r2s)),
        "r2_std": float(np.std(r2s)),
        "feature_importance": pd.Series(importances, index=X.columns).sort_values(ascending=False),
    }


def render_report(results: list[dict], n_rows: int) -> str:
    lines = ["# Work Package 2: LTV Regression Findings", ""]
    lines += [
        (
            f"Target: `ltv_months` (continuous). Rows used: {n_rows}. "
            f"{N_FOLDS}-fold cross-validation, metrics averaged across folds."
        ),
        "",
        (
            "**Data leakage guard**: `cumulative_profit` is intentionally "
            "excluded from every feature set - it is only known after a "
            "customer's lifecycle ends, so using it here would leak the "
            "answer and produce a model that looks perfect in training but "
            "is useless in production."
        ),
        "",
        "## Model comparison (5-fold CV)",
        "",
        "| Model | RMSE (mean ± std) | R² (mean ± std) |",
        "|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['model']} | {r['rmse_mean']:.3f} ± {r['rmse_std']:.3f} | "
            f"{r['r2_mean']:.3f} ± {r['r2_std']:.3f} |"
        )
    lines.append("")

    best = min(results, key=lambda r: r["rmse_mean"])
    lines += [f"Best by RMSE: **{best['model']}** ({best['rmse_mean']:.3f}).", ""]

    lines += [f"## Feature importance (top {TOP_N_FEATURES} per model)", ""]
    for r in results:
        lines += [f"### {r['model']}", "", "| Feature | Importance |", "|---|---|"]
        for feat, val in r["feature_importance"].head(TOP_N_FEATURES).items():
            lines.append(f"| `{feat}` | {val:.1f} |")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    if not Path(CSV_PATH).exists():
        print(f"CSV not found at '{CSV_PATH}' - LTV regression needs the local dataset.", file=sys.stderr)
        sys.exit(1)

    raw = load_raw(CSV_PATH)
    clean_df, _ = clean(raw)

    X = build_feature_matrix(clean_df, exclude={TARGET})
    y = clean_df[TARGET]

    results = [cross_validate(name, factory, X, y) for name, factory in MODEL_FACTORIES.items()]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_report(results, len(clean_df)), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({len(clean_df)} rows).")


if __name__ == "__main__":
    main()
