"""Tests for econocausal.effect_model that do NOT need EconML.

The EconML estimators are tested in test_effect_model_econml.py (skipped when EconML is absent).
"""
import numpy as np
import pandas as pd
import pytest

from econocausal.data_generation import generate_campaign_data
from econocausal.effect_model import (
    BASELINE_CLIP, MODEL_FEATURES, EffectModelConfig, ModelDependencyError, ModelInputError,
    TLearner, baseline_purchase_probabilities, build_features, estimate_effects,
    evaluate_recovery, fit_effect_model, make_estimator, recovery_metrics, to_jsonable,
)

CFG = EffectModelConfig.quick("t_learner", nuisance_trees=20, n_jobs=1)


@pytest.fixture(scope="module")
def data():
    return generate_campaign_data(3000, 42)


def test_features_have_expected_columns_and_no_forbidden_ones(data):
    observed, _ = data
    f = build_features(observed)
    assert list(f.columns) == list(MODEL_FEATURES) and f.shape == (3000, 10)
    for banned in ("customer_id", "order_value", "discount_cost", "discount_offered", "purchased", "true_effect"):
        assert banned not in f.columns
    assert set(np.unique(f["region_East"])) <= {0.0, 1.0}


def test_missing_columns_give_plain_error(data):
    observed, _ = data
    with pytest.raises(ModelInputError) as e:
        build_features(observed.drop(columns=["region"]))
    assert "region" in str(e.value)


def test_invalid_data_is_refused(data):
    observed, _ = data
    bad = observed.copy()
    bad["discount_offered"] = 1
    with pytest.raises(ModelInputError):
        estimate_effects(bad, CFG)


def test_config_validation():
    with pytest.raises(ValueError):
        EffectModelConfig(estimator="magic")
    with pytest.raises(ValueError):
        EffectModelConfig(n_folds=1)
    with pytest.raises(ValueError):
        EffectModelConfig(effect_trees=150)  # not a multiple of 4
    assert EffectModelConfig.quick("t_learner").n_folds == 3


def test_missing_econml_gives_clear_message(monkeypatch):
    import builtins
    real = builtins.__import__

    def fake(name, *a, **k):
        if name.startswith("econml"):
            raise ImportError("no econml")
        return real(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake)
    with pytest.raises(ModelDependencyError) as e:
        make_estimator(EffectModelConfig(estimator="causal_forest"))
    assert "pip install" in str(e.value)


def test_estimate_effects_shape_and_ranges(data):
    observed, _ = data
    r = estimate_effects(observed, CFG)
    c = r.customers
    assert len(c) == 3000 and c["customer_id"].is_unique
    assert c["effect"].between(-1, 1).all()
    assert c["baseline_purchase_prob"].between(*BASELINE_CLIP).all()
    assert (c["expected_list_value"] == observed["avg_order_value_past"]).all()
    assert c["effect_low"].isna().all()  # T-learner gives no intervals: never invented
    assert r.average_effect["ci_low"] is None and any("baseline" in n for n in r.notes)


def test_results_are_deterministic(data):
    observed, _ = data
    a = estimate_effects(observed, CFG).customers["effect"].to_numpy()
    b = estimate_effects(observed, CFG).customers["effect"].to_numpy()
    assert np.array_equal(a, b)


def test_to_dict_is_json_safe_and_capped(data):
    import json
    observed, _ = data
    d = estimate_effects(observed, CFG).to_dict(max_customers=25)
    text = json.dumps(d, allow_nan=False)  # raises on NaN/inf
    assert d["customers_returned"] == 25 and d["customers_total"] == 3000
    assert d["customers"][0]["effect_low"] is None
    assert "true_effect" not in text and "p_discount" not in text
    assert "order_value" not in d["customers"][0] and "discount_cost" not in d["customers"][0]


def test_baseline_probability_tracks_truth(data):
    observed, truth = data
    p0 = baseline_purchase_probabilities(observed, CFG)
    corr = np.corrcoef(p0, truth["p_no_discount"])[0, 1]
    assert corr > 0.5


def test_recovery_beats_naive_difference(data):
    observed, truth = data
    ev = evaluate_recovery(observed, truth, CFG)
    assert ev["n_evaluated"] == 900
    assert abs(ev["ate_error"]) < abs(ev["naive_error"])


def test_recovery_metrics_known_values():
    true = np.array([0.0, 0.1, 0.2, 0.3, 0.4])
    m = recovery_metrics(true, true, low=true - 0.05, high=true + 0.05, naive_difference=0.35)
    assert m["rmse"] == 0 and m["interval_coverage"] == 1.0 and m["rank_correlation"] == pytest.approx(1.0)
    assert m["naive_error"] == pytest.approx(0.35 - 0.2)
    assert m["top20_true_effect_mean"] == pytest.approx(0.4)


def test_recovery_needs_matching_truth(data):
    observed, truth = data
    with pytest.raises(ModelInputError):
        evaluate_recovery(observed, truth.head(10), CFG)


def test_interval_stand_in_estimator_is_used_and_nan_becomes_none(data):
    """Stand-in with intervals, so the interval handling is tested without EconML."""
    observed, _ = data

    class Fake:
        def fit(self, Y, T, X=None, W=None):
            return self

        def effect(self, X):
            return np.full(len(X), 0.05)

        def effect_interval(self, X, alpha=0.05):
            return np.full(len(X), 0.01), np.full(len(X), 0.09)

        def ate_interval(self, X, alpha=0.05):
            return np.array([0.03]), np.array([0.07])

    r = estimate_effects(observed, CFG, estimator_factory=lambda cfg: Fake())
    assert r.customers["effect_low"].eq(0.01).all() and r.average_effect["ci_high"] == 0.07


def test_nan_effects_are_rejected(data):
    observed, _ = data

    class Bad:
        def fit(self, Y, T, X=None, W=None):
            return self

        def effect(self, X):
            return np.full(len(X), np.nan)

    with pytest.raises(ValueError):
        estimate_effects(observed, CFG, estimator_factory=lambda cfg: Bad())


def test_to_jsonable_handles_numpy_and_nan():
    out = to_jsonable({"a": np.float64(1.5), "b": [np.int64(2), float("nan")], "c": np.array([1.0, np.inf])})
    assert out == {"a": 1.5, "b": [2, None], "c": [1.0, None]}
