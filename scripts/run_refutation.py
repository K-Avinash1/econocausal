"""Run the causal refutation tests on the synthetic data and print the verdicts.

Run from the project root (virtual environment active):
    python scripts/run_refutation.py                         # forest, quick settings, 3 repeats each
    python scripts/run_refutation.py --estimator linear      # faster
    python scripts/run_refutation.py --n-sims 5 --full       # slower, full settings

Writes data/demo/refutation_demo.json (the file the frontend shows on the Validation tab).
Read docs/refutation.md first: passing does NOT prove the causal assumptions.
"""
import argparse
import json
import sys
import traceback
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from econocausal.effect_model import ESTIMATORS, EffectModelConfig  # noqa: E402
from econocausal.refutation import run_refutations  # noqa: E402
from econocausal.validation import validate_campaign_data  # noqa: E402

DATA = ROOT / "data" / "generated" / "campaign_data.csv"
OUT = ROOT / "data" / "demo" / "refutation_demo.json"
WORD = {True: "PASS", False: "FAIL", None: "INCONCLUSIVE"}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--estimator", default="causal_forest", choices=ESTIMATORS)
    p.add_argument("--n-sims", type=int, default=3, help="repeats per test (1-20)")
    p.add_argument("--full", action="store_true", help="full settings instead of quick")
    p.add_argument("--seed", type=int, default=7)
    args = p.parse_args()

    if not DATA.exists():
        print("Data is missing. Run first:  python scripts/generate_data.py")
        return 1
    df = pd.read_csv(DATA)
    report = validate_campaign_data(df)
    print(f"Data: {len(df):,} customers, validation {'OK' if report.ok else 'FAILED'}")
    if not report.ok:
        return 1

    config = EffectModelConfig(estimator=args.estimator) if args.full else EffectModelConfig.quick(args.estimator)
    print(f"Estimator: {args.estimator} ({'full' if args.full else 'quick'} settings), {args.n_sims} repeats per test")
    print("This runs about 10 model fits. Please wait...")
    try:
        result = run_refutations(df, config, n_sims=args.n_sims, seed=args.seed)
    except Exception:
        print("FAILED. Copy everything below and send it to Claude:")
        traceback.print_exc()
        return 1

    print(f"\nOriginal average effect: {result['original_average_effect']:.4f}")
    tol = result["tolerance_absolute"]
    print(f"Tolerance (25% of the original effect): {'n/a' if tol is None else f'{tol:.4f}'}\n")
    for r in result["results"]:
        print(f"[{WORD[r['passed']]}] {r['title']}")
        print(f"    re-estimates: {', '.join(f'{v:.4f}' for v in r['re_estimates'])}")
        print(f"    rule: {r['criterion']}")
        print(f"    took {r['seconds']} s")
    print(f"\nPassed {result['n_passed']}, failed {result['n_failed']}, inconclusive {result['n_inconclusive']}; "
          f"total {result['total_seconds']} s")
    print(result["disclaimer"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2))
    print(f"\nWrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
