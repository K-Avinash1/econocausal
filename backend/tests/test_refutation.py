"""Refutation tests. Logic is checked with simple stand-in estimators (fast, exact);
one test runs the real random-forest baseline to check the plumbing end to end."""
import json

import numpy as np
import pytest

from econocausal.data_generation import generate_campaign_data
from econocausal.effect_model import EffectModelConfig, ModelInputError
from econocausal.refutation import TESTS, TOLERANCE, run_refutations

CFG = EffectModelConfig.quick("t_learner", nuisance_trees=20, n_jobs=1)


class DiffInMeans:
    """Honest stand-in: effect = mean(Y | T=1) - mean(Y | T=0), the same for every customer."""

    def fit(self, Y, T, X=None, W=None):
        self.value = float(np.mean(Y[T == 1]) - np.mean(Y[T == 0]))
        return self

    def effect(self, X):
        return np.full(len(X), self.value)


class AlwaysTenPoints:
    """Broken stand-in: reports +0.10 whatever the data say. Must FAIL the placebo test."""

    def fit(self, Y, T, X=None, W=None):
        return self

    def effect(self, X):
        return np.full(len(X), 0.10)


class NoEffect:
    def fit(self, Y, T, X=None, W=None):
        return self

    def effect(self, X):
        return np.zeros(len(X))


@pytest.fixture(scope="module")
def data():
    observed, _ = generate_campaign_data(4000, 42)
    return observed


def by_name(report):
    return {r["name"]: r for r in report["results"]}


def test_honest_estimator_passes_all_three(data):
    rep = run_refutations(data, CFG, n_sims=3, estimator_factory=lambda c: DiffInMeans())
    r = by_name(rep)
    assert set(r) == set(TESTS)
    assert all(x["passed"] is True for x in rep["results"]), rep["results"]
    assert rep["n_passed"] == 3 and rep["n_failed"] == 0 and rep["n_inconclusive"] == 0


def test_broken_estimator_fails_placebo_only(data):
    rep = run_refutations(data, CFG, n_sims=3, estimator_factory=lambda c: AlwaysTenPoints())
    r = by_name(rep)
    assert r["placebo_treatment"]["passed"] is False
    assert r["random_common_cause"]["passed"] is True
    assert r["data_subset"]["passed"] is True


def test_zero_effect_is_inconclusive_not_passed(data):
    rep = run_refutations(data, CFG, n_sims=2, estimator_factory=lambda c: NoEffect())
    assert all(x["passed"] is None for x in rep["results"])
    assert rep["n_inconclusive"] == 3 and "note" in rep
    assert rep["tolerance_absolute"] is None


def test_report_structure_and_json_safe(data):
    rep = run_refutations(data, CFG, n_sims=2, estimator_factory=lambda c: DiffInMeans())
    json.dumps(rep, allow_nan=False)
    assert rep["settings"]["n_sims"] == 2 and rep["settings"]["tolerance_fraction"] == TOLERANCE
    for r in rep["results"]:
        assert len(r["re_estimates"]) == 2 and len(r["deviations"]) == 2
        assert r["criterion"] and r["expected"] and r["what_it_does"]
    assert "does not prove" in rep["disclaimer"] and rep["not_done"]


def test_same_seed_same_result(data):
    a = run_refutations(data, CFG, n_sims=2, seed=5, estimator_factory=lambda c: DiffInMeans())
    b = run_refutations(data, CFG, n_sims=2, seed=5, estimator_factory=lambda c: DiffInMeans())
    assert [r["re_estimates"] for r in a["results"]] == [r["re_estimates"] for r in b["results"]]


def test_can_run_a_single_test(data):
    rep = run_refutations(data, CFG, n_sims=1, tests=["data_subset"], estimator_factory=lambda c: DiffInMeans())
    assert [r["name"] for r in rep["results"]] == ["data_subset"]


def test_bad_arguments_and_bad_data(data):
    with pytest.raises(ValueError):
        run_refutations(data, CFG, n_sims=0)
    with pytest.raises(ValueError):
        run_refutations(data, CFG, tests=["magic"])
    bad = data.copy()
    bad["discount_offered"] = 1
    with pytest.raises(ModelInputError):
        run_refutations(bad, CFG, n_sims=1, estimator_factory=lambda c: DiffInMeans())


def test_real_baseline_estimator_runs_end_to_end(data):
    rep = run_refutations(data.head(2000), CFG, n_sims=1, estimator_factory=None)
    assert len(rep["results"]) == 3 and np.isfinite(rep["original_average_effect"])
