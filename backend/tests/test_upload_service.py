import json
from pathlib import Path

from econocausal.upload_service import MAX_UPLOAD_BYTES, PREVIEW_ROWS, validate_csv_bytes

SAMPLES = Path(__file__).resolve().parents[2] / "data" / "samples"

# file -> (should be accepted, text that must appear in the first error or warning)
EXPECTED = {
    "sample_valid.csv": (True, None),
    "warning_500_rows.csv": (True, "The file has 500 rows"),
    "invalid_missing_columns.csv": (False, "required columns are missing: region, discount_offered"),
    "invalid_text_in_number.csv": (False, "Column 'age' must contain numbers only"),
    "invalid_all_treated.csv": (False, "every customer was offered the discount"),
    "invalid_none_treated.csv": (False, "no customer was offered the discount"),
    "invalid_empty.csv": (False, "The file has no data rows"),
    "invalid_too_few_rows.csv": (False, "The file has only 50 rows"),
    "invalid_bad_region.csv": (False, "Column 'region' contains values that are not allowed (Central)"),
    "invalid_duplicate_ids.csv": (False, "Column 'customer_id' has 1 duplicate"),
    "invalid_missing_values.csv": (False, "Column 'email_engagement' has 2 empty"),
    "invalid_not_binary.csv": (False, "must contain only 0 or 1, but found 2"),
}


def _run(name):
    return validate_csv_bytes((SAMPLES / name).read_bytes())


def test_every_sample_file_gives_the_documented_result():
    for name, (ok, text) in EXPECTED.items():
        result = _run(name)
        assert result["ok"] is ok, name
        if text:
            messages = [m["message"] for m in result["errors"] + result["warnings"]]
            assert any(text in m for m in messages), (name, messages)


def test_valid_file_has_summary_and_preview():
    result = _run("sample_valid.csv")
    assert result["summary"]["n_rows"] == 1000
    assert 0 < result["summary"]["treated_share"] < 1
    assert 0 < result["summary"]["purchase_rate"] < 1
    assert len(result["preview"]) == PREVIEW_ROWS
    assert "customer_id" in result["columns"]
    json.dumps(result)  # must be JSON-safe


def test_missing_columns_file_still_shows_what_was_found():
    result = _run("invalid_missing_columns.csv")
    assert result["columns"] and "region" not in result["columns"]
    assert len(result["preview"]) == PREVIEW_ROWS


def test_header_only_file_has_no_preview():
    result = _run("invalid_empty.csv")
    assert result["ok"] is False and result["preview"] == []


def test_zero_byte_file_is_a_clear_error():
    for raw in (b"", b"   \n"):
        result = validate_csv_bytes(raw)
        assert result["ok"] is False
        assert result["errors"][0]["code"] == "empty_file"


def test_oversized_file_is_refused_before_parsing():
    result = validate_csv_bytes(b"a," * (MAX_UPLOAD_BYTES // 2 + 10))
    assert result["errors"][0]["code"] == "file_too_large"


def test_non_text_file_is_a_clear_error():
    result = validate_csv_bytes(b"\xff\xfe\x00\x81\x82\x83\xff")
    assert result["ok"] is False
    assert result["errors"][0]["code"] == "unreadable_file"
