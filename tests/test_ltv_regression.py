import numpy as np
import pandas as pd

from analysis.ltv_regression import (
    _k_fold_splits,
    _r2,
    _rmse,
    _XGBoostNative,
    cross_validate,
)


def test_k_fold_splits_cover_all_indices_without_overlap() -> None:
    splits = _k_fold_splits(n_samples=23, n_folds=5, random_state=0)

    assert len(splits) == 5
    all_test_indices: list[int] = []
    for train_idx, test_idx in splits:
        assert set(train_idx).isdisjoint(set(test_idx))
        all_test_indices.extend(test_idx.tolist())

    assert sorted(all_test_indices) == list(range(23))


def test_rmse_and_r2_perfect_prediction() -> None:
    y = np.array([1.0, 2.0, 3.0, 4.0])
    assert _rmse(y, y) == 0.0
    assert _r2(y, y) == 1.0


def test_rmse_and_r2_known_error() -> None:
    y_true = np.array([0.0, 0.0])
    y_pred = np.array([1.0, -1.0])
    assert _rmse(y_true, y_pred) == 1.0


def test_cross_validate_runs_and_returns_expected_shape() -> None:
    rng = np.random.default_rng(0)
    n = 60
    X = pd.DataFrame({"a": rng.normal(size=n), "b": rng.normal(size=n)})
    y = pd.Series(2 * X["a"] - X["b"] + rng.normal(scale=0.01, size=n))

    result = cross_validate(
        "TestXGB",
        lambda: _XGBoostNative(num_boost_round=10, max_depth=2, eta=0.3, objective="reg:squarederror", verbosity=0),
        X,
        y,
    )

    assert result["model"] == "TestXGB"
    assert result["rmse_mean"] >= 0
    assert result["r2_mean"] <= 1.0
    assert set(result["feature_importance"].index) == {"a", "b"}
