"""Tests for the synthetic data generator (Day 2).

Statistical checks use wide tolerances so they do not depend on the exact
random stream of a particular NumPy version.
"""
from functools import lru_cache

import numpy as np
import pandas as pd

from econocausal.data_generation import generate_campaign_data
from econocausal.schema import COLUMN_NAMES, DISCOUNT_DEPTH, TRUTH_COLUMNS
from econocausal.validation import validate_campaign_data


@lru_cache(maxsize=None)
def _data(n=20000, seed=42):
    return generate_campaign_data(n, seed)


def test_columns_and_sizes():
    observed, truth = _data()
    assert list(observed.columns) == list(COLUMN_NAMES)
    assert list(truth.columns) == list(TRUTH_COLUMNS)
    assert len(observed) == len(truth) == 20000
    assert observed["customer_id"].is_unique
    assert not observed.isna().any().any()
    assert not truth.isna().any().any()


def test_same_seed_gives_identical_data():
    a_obs, a_truth = generate_campaign_data(2000, 42)
    b_obs, b_truth = generate_campaign_data(2000, 42)
    pd.testing.assert_frame_equal(a_obs, b_obs)
    pd.testing.assert_frame_equal(a_truth, b_truth)


def test_different_seed_gives_different_data():
    a_obs, _ = generate_campaign_data(2000, 42)
    b_obs, _ = generate_campaign_data(2000, 43)
    assert not a_obs["purchased"].equals(b_obs["purchased"]) or not a_obs["age"].equals(b_obs["age"])


def test_probabilities_stay_in_valid_range():
    _, truth = _data()
    for col in ("true_propensity", "p_no_discount", "p_discount"):
        assert truth[col].between(0.0, 1.0).all(), col
    assert truth["p_no_discount"].between(0.02, 0.95).all()
    assert truth["p_discount"].between(0.01, 0.99).all()
    assert truth["true_propensity"].between(0.10, 0.90).all()  # overlap guarantee


def test_true_effect_equals_p_discount_minus_p_no_discount():
    _, truth = _data()
    diff = truth["p_discount"] - truth["p_no_discount"]
    assert np.allclose(truth["true_effect"], diff, rtol=0, atol=1e-12)


def test_effects_are_heterogeneous():
    _, truth = _data()
    te = truth["true_effect"]
    assert te.std() > 0.02            # effects genuinely vary
    assert (te > 0).mean() > 0.80     # most customers respond positively
    assert 0.01 < (te < 0).mean() < 0.15   # a small group responds negatively
    assert 0.03 < te.mean() < 0.12    # plausible average effect


def test_treatment_assignment_is_confounded_but_has_overlap():
    observed, _ = _data()
    t = observed["discount_offered"] == 1
    assert 0.25 < t.mean() < 0.50
    # past campaign favoured loyal, frequent customers
    assert observed.loc[t, "is_loyalty_member"].mean() > observed.loc[~t, "is_loyalty_member"].mean() + 0.05
    assert observed.loc[t, "past_purchases_12m"].mean() > observed.loc[~t, "past_purchases_12m"].mean()


def test_naive_comparison_is_biased_upward():
    observed, truth = _data()
    t = observed["discount_offered"] == 1
    y = observed["purchased"]
    naive = y[t].mean() - y[~t].mean()
    assert naive - truth["true_effect"].mean() > 0.02


def test_observed_outcomes_match_the_true_probabilities():
    observed, truth = _data()
    t = observed["discount_offered"] == 1
    y = observed["purchased"]
    # treated customers buy with probability p_discount, untreated with p_no_discount
    for mask, prob in ((t, truth["p_discount"]), (~t, truth["p_no_discount"])):
        expected = prob[mask].mean()
        se = np.sqrt((prob[mask] * (1 - prob[mask])).sum()) / mask.sum()
        assert abs(y[mask].mean() - expected) < 5 * se


def test_money_columns_are_consistent():
    observed, _ = _data()
    no_buy = observed["purchased"] == 0
    assert (observed.loc[no_buy, "order_value"] == 0).all()
    assert (observed.loc[no_buy, "discount_cost"] == 0).all()
    assert (observed.loc[observed["discount_offered"] == 0, "discount_cost"] == 0).all()
    buyers = observed["purchased"] == 1
    assert (observed.loc[buyers, "order_value"] > 0).all()
    tb = buyers & (observed["discount_offered"] == 1)
    expected = observed.loc[tb, "order_value"] * DISCOUNT_DEPTH / (1 - DISCOUNT_DEPTH)
    assert ((observed.loc[tb, "discount_cost"] - expected).abs() <= 0.02).all()


def test_generated_data_passes_validation():
    observed, _ = _data()
    report = validate_campaign_data(observed)
    assert report.ok, report.errors
    assert report.warnings == []
