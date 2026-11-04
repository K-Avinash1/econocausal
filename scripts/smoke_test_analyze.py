"""Smoke test for the analysis endpoints of a RUNNING EconoCausal API (standard library only).

1. Start the backend (project root, venv active):
       python -m uvicorn --app-dir backend api.main:app --port 8000
2. In a second terminal, from the project root:
       python scripts/smoke_test_analyze.py
   Faster/slower estimator: python scripts/smoke_test_analyze.py --estimator linear
It takes about a minute. Exit code 0 = every check passed, 1 = at least one failed.
Also run scripts/smoke_test_api.py (the /health and /validate checks).
"""
import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "data" / "samples"
ORIGIN = "http://localhost:5173"
results = []


def check(name, passed, detail=""):
    results.append(passed)
    print(f"[{'PASS' if passed else 'FAIL'}] {name}" + (f"  ({detail})" if detail and not passed else ""))


def call(base, path, method="GET", body=None):
    req = urllib.request.Request(base + path, data=body, method=method,
                                 headers={"Content-Type": "text/csv", "Origin": ORIGIN})
    with urllib.request.urlopen(req, timeout=600) as resp:
        return resp.status, {k.lower(): v for k, v in resp.headers.items()}, json.loads(resp.read().decode("utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--estimator", default="linear", choices=["linear", "causal_forest", "t_learner"])
    args = ap.parse_args()
    base, est = args.base, args.estimator

    try:
        status, _, health = call(base, "/health")
    except Exception as exc:
        print(f"Cannot reach {base}: {exc}\nStart the backend first (see the top of this file).")
        return 1
    check("health answers and reports version 0.2.0", status == 200 and health.get("version") == "0.2.0", str(health))

    good = (SAMPLES / "sample_valid.csv").read_bytes()
    status, headers, out = call(base, f"/analyze?estimator={est}&quick=true", "POST", good)
    check("analyze: valid file gives ok and a run_id", status == 200 and out.get("ok") is True and bool(out.get("run_id")), str(out)[:200])
    run_id = out.get("run_id", "")
    check("analyze: summary and first customers present",
          out.get("customers_total") == 1000 and out.get("customers_returned") == 100 and len(out.get("customers", [])) == 100)
    check("analyze: average effect is a number between -1 and 1",
          isinstance(out.get("average_effect", {}).get("ate"), (int, float)) and -1 <= out["average_effect"]["ate"] <= 1)
    hist = out.get("chart_data", {}).get("effect_histogram", {})
    check("analyze: histogram counts add up to the customers", sum(hist.get("counts", [])) == 1000)
    text = json.dumps(out)
    check("analyze: no ground truth or post-offer columns in the answer",
          not any(w in text for w in ("true_effect", "p_discount", "p_no_discount", "order_value", "discount_cost")))
    check("analyze: no evaluation block for an upload", "evaluation" not in out)
    check("analyze: CORS header for the React page", headers.get("access-control-allow-origin") == ORIGIN)

    status, _, page = call(base, f"/results/{run_id}/customers?offset=900&limit=100")
    check("results: last page has 100 customers", page.get("ok") is True and len(page.get("customers", [])) == 100 and page.get("total") == 1000)
    status, _, page = call(base, "/results/doesnotexist/customers")
    check("results: unknown run gives run_not_found",
          page.get("ok") is False and page["errors"][0]["code"] == "run_not_found")

    bad = (SAMPLES / "invalid_bad_region.csv").read_bytes()
    status, _, out_bad = call(base, f"/analyze?estimator={est}", "POST", bad)
    check("analyze: invalid file is refused with a message",
          status == 200 and out_bad.get("ok") is False and "Central" in out_bad["errors"][0]["message"])
    status, _, out_est = call(base, "/analyze?estimator=magic", "POST", good)
    check("analyze: unknown estimator is refused",
          out_est.get("ok") is False and out_est["errors"][0]["code"] == "invalid_estimator")

    print("Running refutation tests (about 10 model fits, please wait)...")
    status, _, ref = call(base, f"/refute/{run_id}?n_sims=1", "POST")
    r = ref.get("refutation", {})
    check("refute: three tests returned with verdicts",
          ref.get("ok") is True and len(r.get("results", [])) == 3 and all("passed" in x for x in r["results"]), str(ref)[:200])
    check("refute: states that passing is not proof", "does not prove" in r.get("disclaimer", ""))
    status, _, ref2 = call(base, f"/refute/{run_id}?n_sims=1", "POST")
    check("refute: second call is served from the cache", ref2.get("cached") is True)
    status, _, ref3 = call(base, "/refute/doesnotexist", "POST")
    check("refute: unknown run gives run_not_found", ref3.get("ok") is False and ref3["errors"][0]["code"] == "run_not_found")

    status, _, demo = call(base, f"/demo?estimator={est}&quick=true")
    if demo.get("ok") is False and demo["errors"][0]["code"] == "demo_data_missing":
        check("demo: needs data (run python scripts/generate_data.py first)", False, demo["errors"][0]["message"])
    else:
        check("demo: ok, labelled as synthetic with a simulation-only evaluation",
              demo.get("ok") is True and demo["run"]["data_source"] == "synthetic"
              and "Simulation only" in demo.get("evaluation", {}).get("label", ""), str(demo)[:200])

    passed = sum(results)
    print(f"\n{passed} passed, {len(results) - passed} failed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
