import numpy as np
import pandas as pd

from analysis.upsell_classification import (
    _XGBoostNativeClassifier,
    business_heuristic_baseline,
    classification_metrics,
    cross_validate,
    majority_class_baseline,
    stratified_k_fold_splits,
)


def test_stratified_k_fold_splits_preserve_class_ratio_and_cover_all_rows() -> None:
    y = np.array([0] * 40 + [1] * 10)
    splits = stratified_k_fold_splits(y, n_folds=5, random_state=0)

    assert len(splits) == 5
    all_test_indices: list[int] = []
    for train_idx, test_idx in splits:
        assert set(train_idx).isdisjoint(set(test_idx))
        # each fold's test set should keep roughly the same 4:1 class ratio
        assert (y[test_idx] == 1).sum() == 2
        assert (y[test_idx] == 0).sum() == 8
        all_test_indices.extend(test_idx.tolist())

    assert sorted(all_test_indices) == list(range(50))


def test_classification_metrics_perfect_predictions() -> None:
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 0, 1, 1])
    y_score = np.array([0.1, 0.2, 0.8, 0.9])

    metrics = classification_metrics(y_true, y_pred, y_score)

    assert metrics["accuracy"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0
    assert metrics["roc_auc"] == 1.0


def test_classification_metrics_all_wrong() -> None:
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([1, 1, 0, 0])
    y_score = np.array([0.9, 0.8, 0.2, 0.1])

    metrics = classification_metrics(y_true, y_pred, y_score)

    assert metrics["accuracy"] == 0.0
    assert metrics["precision"] == 0.0
    assert metrics["recall"] == 0.0
    assert metrics["roc_auc"] == 0.0


def test_majority_class_baseline_has_zero_recall_when_minority_is_target() -> None:
    y = pd.Series([0] * 40 + [1] * 10)
    result = majority_class_baseline(y)

    assert result["model"] == "Majority-class baseline"
    assert result["recall"] == 0.0
    assert result["accuracy"] > 0.5


def test_business_heuristic_baseline_runs_and_returns_metrics() -> None:
    rng = np.random.default_rng(0)
    n = 60
    ltv = rng.uniform(1, 40, size=n)
    cac = rng.uniform(500, 2000, size=n)
    upsell = ((ltv > 20) & (cac < 1200)).astype(int)
    df = pd.DataFrame({"ltv_months": ltv, "customer_acquisition_cost": cac, "upsell": upsell})

    result = business_heuristic_baseline(df)

    assert result["model"].startswith("Business heuristic")
    assert 0.0 <= result["accuracy"] <= 1.0


def test_cross_validate_runs_and_returns_expected_shape() -> None:
    rng = np.random.default_rng(0)
    n = 80
    X = pd.DataFrame({"a": rng.normal(size=n), "b": rng.normal(size=n)})
    y = pd.Series(((X["a"] + rng.normal(scale=0.1, size=n)) > 0).astype(int))

    result = cross_validate(
        "TestXGB",
        lambda: _XGBoostNativeClassifier(
            num_boost_round=10, max_depth=2, eta=0.3, objective="binary:logistic", verbosity=0
        ),
        X,
        y,
    )

    assert result["model"] == "TestXGB"
    assert 0.0 <= result["accuracy"] <= 1.0
    assert set(result["feature_importance"].index) == {"a", "b"}
