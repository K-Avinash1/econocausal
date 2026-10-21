"""Smoke test for a RUNNING EconoCausal API (standard library only, no pip install needed).

1. Start the backend (project root, venv active):
       python -m uvicorn --app-dir backend api.main:app --port 8000
2. In a second terminal, from the project root:
       python scripts/smoke_test_api.py
   Another address: python scripts/smoke_test_api.py --base http://127.0.0.1:8000

It checks /health, /validate for every file in data/samples, the page-level errors
(empty body, non-text body) and the CORS headers the React page needs.
Exit code 0 = every check passed, 1 = at least one failed.
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "data" / "samples"
PAGE_ORIGIN = "http://localhost:5173"   # where the React dev server runs

# sample file -> (accepted?, text that must appear in one of its messages)
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

results = []   # (passed, name, detail)


def record(name, passed, detail=""):
    results.append((passed, name, detail))
    print(f"{'PASS' if passed else 'FAIL'}  {name}" + (f"   <- {detail}" if detail and not passed else ""))


def call(base, method, path, body=None, headers=None):
    request = urllib.request.Request(base + path, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read()


def post_csv(base, body, extra=None):
    headers = {"Content-Type": "text/csv"}
    headers.update(extra or {})
    return call(base, "POST", "/validate", body, headers)


def messages(report):
    return [m["message"] for m in report["errors"] + report["warnings"]]


def run(base):
    status, _, raw = call(base, "GET", "/health")
    try:
        health = json.loads(raw)
    except ValueError:
        health = {}
    record("GET /health answers 200 with status ok", status == 200 and health.get("status") == "ok", f"status {status}, body {raw[:80]!r}")

    for name, (accepted, text) in EXPECTED.items():
        path = SAMPLES / name
        if not path.exists():
            record(f"/validate {name}", False, f"{path} not found")
            continue
        status, _, raw = post_csv(base, path.read_bytes())
        if status != 200:
            record(f"/validate {name}", False, f"HTTP {status}")
            continue
        report = json.loads(raw)
        problems = []
        if report["ok"] is not accepted:
            problems.append(f"ok was {report['ok']}, expected {accepted}")
        if text and not any(text in m for m in messages(report)):
            problems.append(f"expected text {text!r} not in {messages(report)}")
        record(f"/validate {name}", not problems, "; ".join(problems))
        if name == "sample_valid.csv" and not problems:
            summary_ok = report["summary"].get("n_rows") == 1000 and len(report["preview"]) == 10
            record("valid file: summary has 1000 rows and preview has 10 rows", summary_ok, str(report["summary"]))
        if name == "invalid_empty.csv" and not problems:
            record("header-only file: preview is empty", report["preview"] == [], str(report["preview"])[:80])

    status, _, raw = post_csv(base, b"")
    report = json.loads(raw) if status == 200 else {}
    record("empty body -> error code empty_file", status == 200 and report.get("errors", [{}])[0].get("code") == "empty_file", f"HTTP {status}")

    status, _, raw = post_csv(base, b"\xff\xfe\x00\x81\x82\x83\xff")
    report = json.loads(raw) if status == 200 else {}
    record("non-text body -> error code unreadable_file", status == 200 and report.get("errors", [{}])[0].get("code") == "unreadable_file", f"HTTP {status}")

    sample = (SAMPLES / "sample_valid.csv")
    if sample.exists():
        _, headers, _ = post_csv(base, sample.read_bytes(), {"Origin": PAGE_ORIGIN})
        allowed = {k.lower(): v for k, v in headers.items()}.get("access-control-allow-origin")
        record(f"CORS: POST from {PAGE_ORIGIN} is allowed", allowed == PAGE_ORIGIN, f"header was {allowed!r}")
        _, headers, _ = post_csv(base, sample.read_bytes(), {"Origin": "http://not-allowed.example"})
        allowed = {k.lower(): v for k, v in headers.items()}.get("access-control-allow-origin")
        record("CORS: an unknown origin is NOT allowed", allowed is None, f"header was {allowed!r}")

    status, headers, _ = call(base, "OPTIONS", "/validate", None, {
        "Origin": PAGE_ORIGIN,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    allowed = {k.lower(): v for k, v in headers.items()}.get("access-control-allow-origin")
    record("CORS: browser preflight (OPTIONS) is accepted", status == 200 and allowed == PAGE_ORIGIN, f"HTTP {status}, header {allowed!r}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    base = parser.parse_args().base.rstrip("/")
    print(f"Smoke test against {base}\n")
    try:
        run(base)
    except (urllib.error.URLError, ConnectionError, OSError) as error:
        print(f"\nCould not reach {base}: {error}")
        print("Start the backend first:  python -m uvicorn --app-dir backend api.main:app --port 8000")
        return 1
    failed = [r for r in results if not r[0]]
    print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
