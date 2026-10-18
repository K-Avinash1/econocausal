"""Validate the generated dataset, run EDA and write docs/eda_report.md.

Run from the project root, after scripts/generate_data.py:
    python scripts/run_eda.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from econocausal.eda import compute_eda, format_eda_markdown  # noqa: E402
from econocausal.validation import validate_campaign_data  # noqa: E402


def main():
    data_path = ROOT / "data" / "generated" / "campaign_data.csv"
    truth_path = ROOT / "data" / "evaluation" / "ground_truth.csv"
    if not data_path.exists() or not truth_path.exists():
        print("Data files not found. Run first:  python scripts/generate_data.py")
        return 1

    observed = pd.read_csv(data_path)
    truth = pd.read_csv(truth_path)

    report = validate_campaign_data(observed)
    print("Validation:", "OK" if report.ok else "FAILED")
    for e in report.errors:
        print("  ERROR:", e["message"])
    for w in report.warnings:
        print("  warning:", w["message"])
    if not report.ok:
        return 1

    summary = compute_eda(observed, truth)
    out = ROOT / "docs" / "eda_report.md"
    out.write_text(format_eda_markdown(summary), encoding="utf-8")

    o, g = summary["overview"], summary["ground_truth"]
    print(f"Customers: {o['n_rows']:,}   treated share: {o['treated_share']:.3f}   purchase rate: {o['purchase_rate']:.3f}")
    print(f"Naive difference: {o['naive_difference']:.4f}   true ATE: {g['true_ate']:.4f}   naive bias: {g['naive_bias']:+.4f}")
    print("Wrote docs/eda_report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
