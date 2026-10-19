"""Dataset schema for EconoCausal.

Single source of truth for column names, types and allowed ranges. The data
generator, the validator, the EDA code and (later) the API all import from here.
See docs/dataset_schema.md for the human-readable description.
"""
from dataclasses import dataclass
from typing import Optional, Tuple

# --- Fixed project settings (approved by Avinash, 17-18 Oct 2026) -------------
DISCOUNT_DEPTH = 0.15  # one fixed discount depth: 15% off the list price
REGIONS: Tuple[str, ...] = ("North", "South", "East", "West")

ID_COL = "customer_id"
TREATMENT_COL = "discount_offered"
OUTCOME_COL = "purchased"
REVENUE_COL = "order_value"
COST_COL = "discount_cost"


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    kind: str  # "id", "int", "float", "binary" or "category"
    description: str
    minimum: Optional[float] = None
    maximum: Optional[float] = None


COLUMNS = (
    ColumnSpec("customer_id", "id", "Unique customer identifier", 1, None),
    ColumnSpec("age", "int", "Age in years", 18, 75),
    ColumnSpec("tenure_months", "int", "Months as a customer", 0, 120),
    ColumnSpec("past_purchases_12m", "int", "Orders placed in the last 12 months", 0, 60),
    ColumnSpec("avg_order_value_past", "float", "Typical past order value (currency units)", 0, None),
    ColumnSpec("days_since_last_purchase", "int", "Days since the last purchase", 0, 730),
    ColumnSpec("email_engagement", "float", "Share of marketing emails opened (0 to 1)", 0, 1),
    ColumnSpec("is_loyalty_member", "binary", "1 if in the loyalty programme, else 0"),
    ColumnSpec("region", "category", "Customer region: " + ", ".join(REGIONS)),
    ColumnSpec("discount_offered", "binary", "TREATMENT: 1 if offered the discount, else 0"),
    ColumnSpec("purchased", "binary", "OUTCOME: 1 if the customer purchased, else 0"),
    ColumnSpec("order_value", "float", "Amount paid after discount; 0 if no purchase", 0, None),
    ColumnSpec("discount_cost", "float", "Discount given away; 0 if untreated or no purchase", 0, None),
)

COLUMN_NAMES = tuple(c.name for c in COLUMNS)
FEATURE_COLS = (
    "age", "tenure_months", "past_purchases_12m", "avg_order_value_past",
    "days_since_last_purchase", "email_engagement", "is_loyalty_member", "region",
)
NUMERIC_FEATURE_COLS = tuple(c for c in FEATURE_COLS if c != "region")

# Columns of the separate evaluation file (simulation only, never real data)
TRUTH_COLUMNS = (
    "customer_id", "true_propensity", "p_no_discount", "p_discount",
    "true_effect", "expected_list_value",
)
