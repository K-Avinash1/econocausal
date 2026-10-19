"""Generate the synthetic campaign dataset and its separate ground-truth file.

Run from the project root (virtual environment active):
    python scripts/generate_data.py
    python scripts/generate_data.py --n 20000 --seed 42
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from econocausal.data_generation import generate_campaign_data  # noqa: E402
from econocausal.validation import validate_campaign_data  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=20000, help="number of customers (default 20000)")
    parser.add_argument("--seed", type=int, default=42, help="random seed (default 42)")
    args = parser.parse_args()

    observed, truth = generate_campaign_data(args.n, args.seed)

    report = validate_campaign_data(observed)
    if not report.ok:
        print("Generated data failed validation:")
        for e in report.errors:
            print("  -", e["message"])
        return 1

    gen_dir = ROOT / "data" / "generated"
    eval_dir = ROOT / "data" / "evaluation"
    gen_dir.mkdir(parents=True, exist_ok=True)
    eval_dir.mkdir(parents=True, exist_ok=True)
    observed.to_csv(gen_dir / "campaign_data.csv", index=False)
    truth.to_csv(eval_dir / "ground_truth.csv", index=False)

    print(f"Wrote {len(observed):,} rows -> data/generated/campaign_data.csv")
    print(f"Wrote ground truth     -> data/evaluation/ground_truth.csv  (simulation only)")
    print(f"seed={args.seed}  treated share={observed['discount_offered'].mean():.3f}  purchase rate={observed['purchased'].mean():.3f}")
    print("Validation: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
