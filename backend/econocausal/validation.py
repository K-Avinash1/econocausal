"""Validation of an uploaded or generated campaign dataset.

validate_campaign_data(df) never raises for bad data. It returns a
ValidationReport whose errors/warnings are written in plain English so the
dashboard can show them to a user as they are.

Rules are the Day 3 starting point (docs/dataset_schema.md). Avinash finalises
the backend validation rules on Day 5.
"""
from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np
import pandas as pd

from .schema import (
    COLUMNS, COLUMN_NAMES, COST_COL, DISCOUNT_DEPTH, ID_COL, OUTCOME_COL,
    REGIONS, REVENUE_COL, TREATMENT_COL,
)

MIN_ROWS_ERROR = 200       # below this, effects cannot be estimated reliably
MIN_ROWS_WARNING = 1000    # below this, results will be noisy
MIN_ARM_SIZE = 50          # customers needed in BOTH treated and untreated groups
MIN_ARM_SHARE_WARNING = 0.05
COST_TOLERANCE = 0.02      # rounding allowance when checking discount_cost


@dataclass
class ValidationReport:
    errors: List[Dict] = field(default_factory=list)
    warnings: List[Dict] = field(default_factory=list)
    summary: Dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add_error(self, code, message, column=None):
        self.errors.append({"code": code, "column": column, "message": message})

    def add_warning(self, code, message, column=None):
        self.warnings.append({"code": code, "column": column, "message": message})

    def to_dict(self) -> Dict:
        return {"ok": self.ok, "errors": self.errors, "warnings": self.warnings, "summary": self.summary}


def _examples(values, k=3):
    return ", ".join(str(v) for v in list(values)[:k])


def validate_campaign_data(df: pd.DataFrame) -> ValidationReport:
    report = ValidationReport()

    if df is None or len(df) == 0:
        report.add_error("empty_file", "The file has no data rows. Upload a CSV that contains customer rows under the header.")
        report.summary = {"n_rows": 0}
        return report

    n = len(df)
    report.summary["n_rows"] = int(n)

    # 1. Required columns --------------------------------------------------------
    missing = [c for c in COLUMN_NAMES if c not in df.columns]
    if missing:
        report.add_error(
            "missing_columns",
            "These required columns are missing: " + ", ".join(missing)
            + ". Column names must match exactly (for example 'discount_offered').",
        )
    present = [c for c in COLUMN_NAMES if c in df.columns]
    extra = [c for c in df.columns if c not in COLUMN_NAMES]
    if extra:
        report.add_warning("extra_columns", "These extra columns will be ignored: " + ", ".join(map(str, extra)))

    # 2. Per-column checks ------------------------------------------------------
    clean = {}  # numeric versions of columns that passed their type check
    for spec in COLUMNS:
        name = spec.name
        if name not in df.columns:
            continue
        col = df[name]

        n_missing = int(col.isna().sum())
        if n_missing:
            report.add_error("missing_values", f"Column '{name}' has {n_missing} empty value(s). Fill or remove those rows.", name)
            continue

        if spec.kind == "category":
            bad = sorted(set(col.astype(str)) - set(REGIONS))
            if bad:
                report.add_error(
                    "invalid_category",
                    f"Column '{name}' contains values that are not allowed ({_examples(bad)}). Allowed: {', '.join(REGIONS)}.",
                    name,
                )
            continue

        numeric = pd.to_numeric(col, errors="coerce")
        n_text = int(numeric.isna().sum())
        if n_text:
            bad_vals = col[numeric.isna()].astype(str).unique()
            report.add_error(
                "not_numeric",
                f"Column '{name}' must contain numbers only, but {n_text} value(s) are text (for example {_examples(bad_vals)}).",
                name,
            )
            continue

        if spec.kind == "binary":
            bad = sorted(set(numeric.unique()) - {0, 1})
            if bad:
                report.add_error("not_binary", f"Column '{name}' must contain only 0 or 1, but found {_examples(bad)}.", name)
                continue
        if spec.kind in ("int", "id", "binary"):
            if not np.all(np.isclose(numeric, np.round(numeric))):
                report.add_error("not_integer", f"Column '{name}' must contain whole numbers only.", name)
                continue
        if spec.minimum is not None and (numeric < spec.minimum).any():
            k = int((numeric < spec.minimum).sum())
            report.add_error("below_minimum", f"Column '{name}' has {k} value(s) below the allowed minimum of {spec.minimum:g}.", name)
            continue
        if spec.maximum is not None and (numeric > spec.maximum).any():
            k = int((numeric > spec.maximum).sum())
            report.add_error("above_maximum", f"Column '{name}' has {k} value(s) above the allowed maximum of {spec.maximum:g}.", name)
            continue
        clean[name] = numeric

    # 3. Identifier uniqueness ---------------------------------------------------
    if ID_COL in df.columns and df[ID_COL].notna().all() and df[ID_COL].duplicated().any():
        k = int(df[ID_COL].duplicated().sum())
        report.add_error("duplicate_ids", f"Column '{ID_COL}' has {k} duplicate ID(s). Each customer must appear once.", ID_COL)

    # 4. Sample size and treatment variation (needs the treatment column) --------
    if n < MIN_ROWS_ERROR:
        report.add_error("too_few_rows", f"The file has only {n} rows. At least {MIN_ROWS_ERROR} customers are needed to estimate discount effects.")
    elif n < MIN_ROWS_WARNING:
        report.add_warning("few_rows", f"The file has {n} rows. Results will be noisy; {MIN_ROWS_WARNING}+ customers are recommended.")

    if TREATMENT_COL in clean:
        t = clean[TREATMENT_COL]
        n_treated, n_control = int((t == 1).sum()), int((t == 0).sum())
        report.summary.update({"n_treated": n_treated, "n_untreated": n_control, "treated_share": round(n_treated / n, 4)})
        if n_treated == 0 or n_control == 0:
            which = "no customer was offered the discount" if n_treated == 0 else "every customer was offered the discount"
            report.add_error(
                "no_treatment_variation",
                f"In column '{TREATMENT_COL}', {which}. The effect of a discount cannot be measured without both treated and untreated customers.",
                TREATMENT_COL,
            )
        else:
            if min(n_treated, n_control) < MIN_ARM_SIZE:
                report.add_error(
                    "arm_too_small",
                    f"Only {min(n_treated, n_control)} customers are in the smaller group (offered vs not offered). At least {MIN_ARM_SIZE} are needed in each group.",
                    TREATMENT_COL,
                )
            elif min(n_treated, n_control) / n < MIN_ARM_SHARE_WARNING:
                report.add_warning("unbalanced_treatment", f"Fewer than {int(MIN_ARM_SHARE_WARNING * 100)}% of customers are in one treatment group; estimates for that group will be uncertain.", TREATMENT_COL)

    if OUTCOME_COL in clean:
        y = clean[OUTCOME_COL]
        report.summary["purchase_rate"] = round(float(y.mean()), 4)
        if y.nunique() < 2:
            report.add_error("no_outcome_variation", f"Column '{OUTCOME_COL}' has the same value in every row, so there is nothing to explain.", OUTCOME_COL)

    # 5. Consistency between money columns and purchases -------------------------
    needed = (OUTCOME_COL, TREATMENT_COL, REVENUE_COL, COST_COL)
    if all(c in clean for c in needed):
        y, t, rev, cost = (clean[c] for c in needed)
        if ((y == 0) & ((rev > 0) | (cost > 0))).any():
            report.add_error("money_without_purchase", f"Some rows have '{OUTCOME_COL}' = 0 but a positive '{REVENUE_COL}' or '{COST_COL}'. Both must be 0 when there is no purchase.")
        if ((y == 1) & (rev <= 0)).any():
            report.add_error("purchase_without_revenue", f"Some rows have '{OUTCOME_COL}' = 1 but '{REVENUE_COL}' is 0.")
        if ((t == 0) & (cost > 0)).any():
            report.add_error("cost_without_discount", f"Some customers were not offered the discount but have a positive '{COST_COL}'.")
        treated_buyers = (t == 1) & (y == 1) & (rev > 0)
        if treated_buyers.any():
            expected = rev[treated_buyers] * DISCOUNT_DEPTH / (1.0 - DISCOUNT_DEPTH)
            off = int(((cost[treated_buyers] - expected).abs() > COST_TOLERANCE).sum())
            if off:
                report.add_warning(
                    "cost_rule_mismatch",
                    f"For {off} treated purchase(s), '{COST_COL}' does not match a {int(DISCOUNT_DEPTH * 100)}% discount on the list price. "
                    "This project assumes one fixed discount depth.",
                    COST_COL,
                )

    return report
