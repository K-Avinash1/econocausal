"""EconML-specific tests. Skipped automatically when EconML is not installed.

These are the first real check of the EconML calls. Run on a machine with EconML:
    python -m pytest backend/tests/test_effect_model_econml.py -v
"""
import numpy as np
import pytest

pytest.importorskip("econml")

from econocausal.data_generation import generate_campaign_data  # noqa: E402
from econocausal.effect_model import EffectModelConfig, estimate_effects  # noqa: E402


@pytest.fixture(scope="module")
def data():
    return generate_campaign_data(2500, 42)


@pytest.mark.parametrize("name", ["linear", "causal_forest"])
def test_econml_estimator_runs_and_returns_valid_effects(data, name):
    observed, _ = data
    cfg = EffectModelConfig.quick(name, n_folds=2, nuisance_trees=20, effect_trees=40, n_jobs=1)
    r = estimate_effects(observed, cfg)
    c = r.customers
    assert len(c) == 2500
    assert np.isfinite(c["effect"]).all() and c["effect"].between(-1, 1).all()
    if c["effect_low"].notna().all():
        assert (c["effect_low"] <= c["effect"] + 1e-9).all() and (c["effect"] <= c["effect_high"] + 1e-9).all()
