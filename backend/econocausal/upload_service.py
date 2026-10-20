"""Turn the raw bytes of an uploaded CSV into a validation response.

The API (backend/api/main.py) is a thin wrapper around validate_csv_bytes(), so
all the logic can be tested without starting a server.

The response always has the same shape, whether the file is good or bad:
  ok        True if there are no errors
  errors    list of {code, column, message}
  warnings  list of {code, column, message}
  summary   n_rows, n_treated, n_untreated, treated_share, purchase_rate (when known)
  columns   column names found in the file
  preview   first 10 rows as a list of dicts (empty if no rows could be read)
"""
import io
import json

import pandas as pd

from .validation import validate_campaign_data

MAX_UPLOAD_BYTES = 10 * 1024 * 1024   # 10 MB (to be confirmed by Avinash)
PREVIEW_ROWS = 10


def _plain(obj):
    """Make numpy numbers JSON-safe."""
    def default(value):
        if hasattr(value, "item"):
            return value.item()
        raise TypeError(f"cannot serialise {type(value)}")
    return json.loads(json.dumps(obj, default=default))


def _failure(code, message):
    return {
        "ok": False,
        "errors": [{"code": code, "column": None, "message": message}],
        "warnings": [],
        "summary": {},
        "columns": [],
        "preview": [],
    }


def validate_csv_bytes(raw: bytes) -> dict:
    if not raw or not raw.strip():
        return _failure("empty_file", "The file is empty. Upload a CSV that contains a header row and customer rows.")
    if len(raw) > MAX_UPLOAD_BYTES:
        return _failure("file_too_large", "This file is larger than 10 MB. Please upload a smaller file.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return _failure("unreadable_file", "We could not read this file as text. Save it as a CSV (UTF-8) and try again.")
    try:
        df = pd.read_csv(io.StringIO(text))
    except pd.errors.EmptyDataError:
        return _failure("empty_file", "The file is empty. Upload a CSV that contains a header row and customer rows.")
    except (pd.errors.ParserError, ValueError):
        return _failure("unreadable_file", "We could not read this file as a CSV. Check that the values are separated by commas.")

    report = validate_campaign_data(df).to_dict()
    preview = json.loads(df.head(PREVIEW_ROWS).to_json(orient="records")) if len(df) else []
    report["columns"] = [str(c) for c in df.columns]
    report["preview"] = preview
    return _plain(report)
