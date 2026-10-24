"""Run the first effect model(s) on the synthetic data and print what came out.

Run from the project root (virtual environment active):
    python scripts/run_first_model.py --quick                  # fast first run (a few minutes at most)
    python scripts/run_first_model.py                          # full default settings
    python scripts/run_first_model.py --estimators t_learner   # baseline only (no EconML needed)
    python scripts/run_first_model.py --estimators causal_forest linear t_learner

Writes data/generated/first_model_run.json (git-ignored) and, with --export-demo,
data/demo/analysis_demo.json (the file the frontend displays).
"""
import argparse
import json
import sys
import traceback
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from econocausal.effect_model import (  # noqa: E402
    ESTIMATORS, EffectModelConfig, estimate_effects, evaluate_recovery,
)
from econocausal.validation import validate_campaign_data  # noqa: E402

DATA = ROOT / "data" / "generated" / "campaign_data.csv"
TRUTH = ROOT / "data" / "evaluation" / "ground_truth.csv"


def fmt(x, digits=4):
    return "n/a" if x is None else f"{x:.{digits}f}"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--estimators", nargs="+", default=["causal_forest", "linear", "t_learner"], choices=ESTIMATORS)
    p.add_argument("--quick", action="store_true", help="smaller, faster settings")
    p.add_argument("--n", type=int, default=0, help="use only the first N customers (0 = all)")
    p.add_argument("--export-demo", choices=ESTIMATORS, help="write data/demo/analysis_demo.json from this estimator")
    args = p.parse_args()

    if not DATA.exists() or not TRUTH.exists():
        print("Data files are missing. Run first:  python scripts/generate_data.py")
        return 1
    observed = pd.read_csv(DATA)
    truth = pd.read_csv(TRUTH)
    if args.n:
        observed = observed.head(args.n).reset_index(drop=True)
        truth = truth[truth["customer_id"].isin(observed["customer_id"])].reset_index(drop=True)
    report = validate_campaign_data(observed)
    print(f"Data: {len(observed):,} customers, validation {'OK' if report.ok else 'FAILED'}")
    if not report.ok:
        return 1

    results, failures = {}, []
    for name in args.estimators:
        config = EffectModelConfig.quick(name) if args.quick else EffectModelConfig(estimator=name)
        print(f"\n=== {name} ({'quick' if args.quick else 'full'} settings) ===")
        try:
            evaluation = evaluate_recovery(observed, truth, config)
            result = estimate_effects(observed, config, data_source="synthetic")
        except Exception:
            failures.append(name)
            print(f"FAILED. Copy everything below and send it to Claude:")
            traceback.print_exc()
            continue
        results[name] = (result, evaluation)
        ate = result.average_effect
        print(f"Average effect (all customers): {fmt(ate['ate'])}  95% interval: {fmt(ate['ci_low'])} to {fmt(ate['ci_high'])}")
        print(f"Spread of per-customer effects: {result.effect_summary['p05']:.3f} (5th pct) to {result.effect_summary['p95']:.3f} (95th pct); "
              f"{result.effect_summary['share_negative']:.0%} negative")
        print("Check against the TRUE effects (simulation only, held-out 30%):")
        print(f"  true average effect      {fmt(evaluation['true_ate'])}")
        print(f"  estimated average effect {fmt(evaluation['estimated_ate'])}   (error {fmt(evaluation['ate_error'])})")
        print(f"  naive treated-vs-untreated difference {fmt(evaluation['naive_difference'])}   (error {fmt(evaluation['naive_error'])})")
        print(f"  RMSE {fmt(evaluation['rmse'])}   rank correlation {fmt(evaluation['rank_correlation'], 3)}")
        print(f"  true effect of the customers ranked top 20%: {fmt(evaluation['top20_true_effect_mean'])}  "
              f"bottom 20%: {fmt(evaluation['bottom20_true_effect_mean'])}  all: {fmt(evaluation['all_true_effect_mean'])}")
        print(f"  interval coverage {fmt(evaluation['interval_coverage'], 3)} (target about 0.95)   "
              f"fit time {evaluation['fit_seconds']} s")
        for note in result.notes[2:]:
            print("  note:", note)

    if results:
        out = ROOT / "data" / "generated" / "first_model_run.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {name: r.to_dict(max_customers=100, evaluation=ev) for name, (r, ev) in results.items()}
        out.write_text(json.dumps(payload, indent=2))
        print(f"\nWrote {out.relative_to(ROOT)}")
        if args.export_demo:
            if args.export_demo not in results:
                print(f"--export-demo {args.export_demo} did not run successfully; nothing exported.")
            else:
                r, ev = results[args.export_demo]
                demo = ROOT / "data" / "demo" / "analysis_demo.json"
                demo.parent.mkdir(parents=True, exist_ok=True)
                demo.write_text(json.dumps(r.to_dict(max_customers=50, evaluation=ev), indent=2))
                print(f"Wrote {demo.relative_to(ROOT)} from {args.export_demo}")

    if failures:
        print(f"\nFAILED estimators: {', '.join(failures)}")
        return 1
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
