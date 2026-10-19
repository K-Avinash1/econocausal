"""Tests for dataset validation (Day 3). Each test breaks one thing in a valid file."""
from functools import lru_cache

import numpy as np

from econocausal.data_generation import generate_campaign_data
from econocausal.validation import validate_campaign_data


@lru_cache(maxsize=None)
def _base():
    observed, _ = generate_campaign_data(2000, 42)
    return observed


def _fresh():
    return _base().copy()


def _codes(report, kind="errors"):
    return {item["code"] for item in getattr(report, kind)}


def test_valid_file_is_accepted():
    report = validate_campaign_data(_fresh())
    assert report.ok and not report.warnings
    assert report.summary["n_rows"] == 2000


def test_empty_file_is_rejected():
    report = validate_campaign_data(_fresh().iloc[0:0])
    assert "empty_file" in _codes(report)


def test_missing_columns_are_named():
    df = _fresh().drop(columns=["discount_offered", "region"])
    report = validate_campaign_data(df)
    assert "missing_columns" in _codes(report)
    msg = next(e["message"] for e in report.errors if e["code"] == "missing_columns")
    assert "discount_offered" in msg and "region" in msg


def test_text_in_numeric_column_is_rejected():
    df = _fresh()
    df["age"] = df["age"].astype(object)
    df.loc[[1, 2], "age"] = "forty"
    report = validate_campaign_data(df)
    assert "not_numeric" in _codes(report)


def test_missing_values_are_rejected():
    df = _fresh()
    df.loc[[0, 1], "email_engagement"] = np.nan
    assert "missing_values" in _codes(validate_campaign_data(df))


def test_out_of_range_values_are_rejected():
    df = _fresh()
    df.loc[0, "age"] = 5
    df.loc[1, "email_engagement"] = 1.5
    codes = _codes(validate_campaign_data(df))
    assert "below_minimum" in codes and "above_maximum" in codes


def test_non_binary_treatment_is_rejected():
    df = _fresh()
    df.loc[0, "discount_offered"] = 2
    assert "not_binary" in _codes(validate_campaign_data(df))


def test_bad_region_is_rejected():
    df = _fresh()
    df.loc[0, "region"] = "Central"
    assert "invalid_category" in _codes(validate_campaign_data(df))


def test_duplicate_ids_are_rejected():
    df = _fresh()
    df.loc[1, "customer_id"] = df.loc[0, "customer_id"]
    assert "duplicate_ids" in _codes(validate_campaign_data(df))


def test_all_treated_is_rejected():
    df = _fresh()
    df["discount_offered"] = 1
    assert "no_treatment_variation" in _codes(validate_campaign_data(df))


def test_no_one_treated_is_rejected():
    df = _fresh()
    df["discount_offered"] = 0
    assert "no_treatment_variation" in _codes(validate_campaign_data(df))


def test_too_few_rows_is_rejected_and_small_file_warns():
    assert "too_few_rows" in _codes(validate_campaign_data(_fresh().iloc[:100]))
    report = validate_campaign_data(_fresh().iloc[:600])
    assert report.ok and "few_rows" in _codes(report, "warnings")


def test_outcome_without_variation_is_rejected():
    df = _fresh()
    df["purchased"] = 0
    df["order_value"] = 0.0
    df["discount_cost"] = 0.0
    assert "no_outcome_variation" in _codes(validate_campaign_data(df))


def test_money_without_purchase_is_rejected():
    df = _fresh()
    idx = df.index[df["purchased"] == 0][0]
    df.loc[idx, "order_value"] = 50.0
    assert "money_without_purchase" in _codes(validate_campaign_data(df))


def test_unexpected_discount_depth_is_a_warning_not_an_error():
    df = _fresh()
    idx = df.index[(df["discount_offered"] == 1) & (df["purchased"] == 1)][0]
    df.loc[idx, "discount_cost"] = df.loc[idx, "discount_cost"] + 5.0
    report = validate_campaign_data(df)
    assert report.ok
    assert "cost_rule_mismatch" in _codes(report, "warnings")


def test_extra_columns_only_warn():
    df = _fresh()
    df["notes"] = "x"
    report = validate_campaign_data(df)
    assert report.ok and "extra_columns" in _codes(report, "warnings")
