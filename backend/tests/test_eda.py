"""Tests for the EDA calculations (Day 3)."""
import numpy as np

from econocausal.data_generation import generate_campaign_data
from econocausal.eda import compute_eda, format_eda_markdown


def _summary():
    observed, truth = generate_campaign_data(5000, 42)
    return observed, truth, compute_eda(observed, truth)


def test_overview_matches_the_data():
    observed, _, s = _summary()
    assert s["overview"]["n_rows"] == 5000
    assert np.isclose(s["overview"]["purchase_rate"], observed["purchased"].mean())
    t = observed["discount_offered"] == 1
    naive = observed.loc[t, "purchased"].mean() - observed.loc[~t, "purchased"].mean()
    assert np.isclose(s["overview"]["naive_difference"], naive)


def test_naive_bias_is_naive_minus_true_ate():
    _, truth, s = _summary()
    expected = s["overview"]["naive_difference"] - truth["true_effect"].mean()
    assert np.isclose(s["ground_truth"]["naive_bias"], expected)
    assert s["ground_truth"]["naive_bias"] > 0


def test_loyalty_is_unbalanced_between_groups():
    _, _, s = _summary()
    assert abs(s["covariate_balance_smd"]["is_loyalty_member"]) > 0.1


def test_eda_without_truth_has_no_ground_truth_section():
    observed, _ = generate_campaign_data(1000, 1)
    s = compute_eda(observed)
    assert "ground_truth" not in s
    assert "Part B" not in format_eda_markdown(s)


def test_markdown_contains_both_parts_and_limits():
    _, _, s = _summary()
    md = format_eda_markdown(s)
    assert "Part A" in md and "Part B" in md and "Limits" in md
