"""Tests for the analysis workflow behind the API (no server needed)."""
import numpy as np
import pytest

from econocausal import analysis_service as svc
from econocausal.data_generation import generate_campaign_data


class DiffInMeans:
    def fit(self, Y, T, X=None, W=None):
        self.value = float(np.mean(Y[T == 1]) - np.mean(Y[T == 0]))
        return self

    def effect(self, X):
        return np.full(len(X), self.value)


FAKE = lambda cfg: DiffInMeans()  # noqa: E731


@pytest.fixture(scope="module")
def data():
    return generate_campaign_data(2000, 42)


def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


def test_analyze_valid_upload(data):
    observed, _ = data
    store = svc.RunStore()
    out = svc.analyze_csv_bytes(csv_bytes(observed), "t_learner", True, store, estimator_factory=FAKE)
    assert out["ok"] is True and out["run_id"] and len(store) == 1
    assert out["customers_total"] == 2000 and out["customers_returned"] == 100
    assert out["run"]["data_source"] == "upload"
    hist = out["chart_data"]["effect_histogram"]
    assert sum(hist["counts"]) == 2000 and len(hist["bin_edges"]) == len(hist["counts"]) + 1


def test_upload_never_returns_truth(data):
    observed, truth = data
    out = svc.analyze_csv_bytes(csv_bytes(observed), "t_learner", True, svc.RunStore(), estimator_factory=FAKE)
    text = str(out)
    assert "evaluation" not in out
    for word in ("true_effect", "p_discount", "p_no_discount", "true_propensity", "order_value", "discount_cost"):
        assert word not in text


def test_invalid_file_gets_validation_errors_and_no_run(data):
    observed, _ = data
    store = svc.RunStore()
    bad = observed.copy()
    bad["region"] = "Central"
    out = svc.analyze_csv_bytes(csv_bytes(bad), "t_learner", True, store, estimator_factory=FAKE)
    assert out["ok"] is False and out["errors"] and len(store) == 0
    assert svc.analyze_csv_bytes(b"", "t_learner", True, store)["errors"][0]["code"] == "empty_file"


def test_unknown_estimator_and_too_many_rows(data):
    observed, _ = data
    assert svc.analyze_csv_bytes(csv_bytes(observed), "magic")["errors"][0]["code"] == "invalid_estimator"
    out = svc.analyze_csv_bytes(csv_bytes(observed), "t_learner", True, svc.RunStore(), max_rows=500, estimator_factory=FAKE)
    assert out["errors"][0]["code"] == "too_many_rows" and "500" in out["errors"][0]["message"]


def test_model_failure_is_a_friendly_error(data):
    observed, _ = data

    class Boom:
        def fit(self, *a, **k):
            raise RuntimeError("internal detail that must not leak")

    out = svc.analyze_csv_bytes(csv_bytes(observed), "t_learner", True, svc.RunStore(), estimator_factory=lambda c: Boom())
    assert out["ok"] is False and out["errors"][0]["code"] == "analysis_failed"
    assert "internal detail" not in str(out)


def test_paging(data):
    observed, _ = data
    store = svc.RunStore()
    run_id = svc.analyze_csv_bytes(csv_bytes(observed), "t_learner", True, store, estimator_factory=FAKE)["run_id"]
    page = svc.get_customers(run_id, offset=1990, limit=50, store=store)
    assert page["total"] == 2000 and len(page["customers"]) == 10
    assert page["customers"][0]["customer_id"] < page["customers"][-1]["customer_id"]
    assert svc.get_customers(run_id, offset=-5, limit=10**6, store=store)["limit"] == svc.MAX_PAGE
    assert svc.get_customers("nope", store=store)["errors"][0]["code"] == "run_not_found"


def test_store_keeps_only_recent_runs():
    store = svc.RunStore(max_runs=2)
    ids = [store.add({"n": i}) for i in range(3)]
    assert store.get(ids[0]) is None and store.get(ids[1]) and store.get(ids[2]) and len(store) == 2


def test_demo_run_has_labelled_evaluation(data, tmp_path):
    observed, truth = data
    observed.to_csv(tmp_path / "d.csv", index=False)
    truth.to_csv(tmp_path / "t.csv", index=False)
    out = svc.demo_run("t_learner", True, svc.RunStore(), tmp_path / "d.csv", tmp_path / "t.csv", estimator_factory=FAKE)
    assert out["ok"] is True and out["run"]["data_source"] == "synthetic"
    assert "Simulation only" in out["evaluation"]["label"]


def test_demo_run_without_files(tmp_path):
    out = svc.demo_run("t_learner", True, svc.RunStore(), tmp_path / "x.csv", tmp_path / "y.csv")
    assert out["errors"][0]["code"] == "demo_data_missing" and "generate_data.py" in out["errors"][0]["message"]


def test_refute_run_and_cache(data):
    observed, _ = data
    store = svc.RunStore()
    run_id = svc.analyze_csv_bytes(csv_bytes(observed), "t_learner", True, store, estimator_factory=FAKE)["run_id"]
    first = svc.refute_run(run_id, 2, store, estimator_factory=FAKE)
    assert first["ok"] and first["cached"] is False and len(first["refutation"]["results"]) == 3
    second = svc.refute_run(run_id, 2, store, estimator_factory=FAKE)
    assert second["cached"] is True
    assert svc.refute_run(run_id, 99, store)["errors"][0]["code"] == "invalid_n_sims"
    assert svc.refute_run("nope", 2, store)["errors"][0]["code"] == "run_not_found"
