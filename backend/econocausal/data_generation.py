"""Reproducible synthetic retail-campaign data for EconoCausal.

Returns two tables:
  observed - what a retailer would actually have (schema in schema.py)
  truth    - simulation-only ground truth (true probabilities and effects)

The generating equations are documented in docs/dataset_schema.md and must be
kept in sync with this file. Real-world data has no 'truth' table.
"""
import numpy as np
import pandas as pd

from .schema import DISCOUNT_DEPTH, REGIONS, TRUTH_COLUMNS, COLUMN_NAMES

REGION_PROBS = (0.30, 0.25, 0.25, 0.20)
REGION_BASELINE_EFFECT = {"North": 0.15, "South": 0.00, "East": -0.15, "West": 0.05}
LIST_VALUE_SIGMA = 0.25  # spread of one order's list value around the customer's typical value


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def generate_campaign_data(n=20000, seed=42):
    """Generate (observed, truth) for n customers using a fixed seed."""
    if n < 1:
        raise ValueError("n must be at least 1")
    rng = np.random.default_rng(seed)

    # ---- 1. Customer features -------------------------------------------------
    age = np.clip(np.round(rng.normal(42, 13, n)), 18, 75).astype(int)
    region = rng.choice(np.array(REGIONS), size=n, p=REGION_PROBS)
    age_scaled = (age - 18) / 57.0
    tenure = np.clip(np.round(rng.gamma(2.0, 14.0, n) * (0.6 + 0.4 * age_scaled)), 0, 120).astype(int)
    loyal = rng.binomial(1, _sigmoid(-1.5 + 0.03 * tenure))
    past_purchases = np.clip(1 + rng.poisson(np.exp(0.5 + 0.010 * tenure + 0.45 * loyal)), 1, 60).astype(int)
    engagement = rng.beta(2.0 + 1.5 * loyal, 3.0)
    recency = np.clip(np.round(rng.exponential(90.0 / (1.0 + 0.15 * past_purchases))), 0, 365).astype(int)
    aov = np.round(np.maximum(np.exp(rng.normal(np.log(55.0) + 0.004 * (age - 40), 0.35)), 1.0), 2)

    # Fixed-constant standardisation (constants are documented, not data-driven)
    freq_z = (np.log(past_purchases) - 1.5) / 0.7
    recency_z = (recency - 45.0) / 45.0
    eng_z = (engagement - 0.5) / 0.2
    aov_z = (np.log(aov) - np.log(55.0)) / 0.35
    tenure_z = (tenure - 22.0) / 17.0
    region_effect = np.array([REGION_BASELINE_EFFECT[r] for r in region])

    # ---- 2. Treatment assignment (confounded) --------------------------------
    # The past campaign favoured loyal, frequent, high-value, engaged customers.
    logit_e = (-0.50 + 0.45 * loyal + 0.35 * freq_z + 0.25 * aov_z
               + 0.20 * eng_z - 0.15 * recency_z)
    propensity = np.clip(_sigmoid(logit_e), 0.10, 0.90)  # guarantees overlap
    treated = rng.binomial(1, propensity)

    # ---- 3. Purchase probability without the discount ------------------------
    logit_p0 = (-1.25 + 0.60 * loyal + 0.55 * freq_z + 0.45 * eng_z
                - 0.55 * recency_z + 0.20 * aov_z + 0.12 * tenure_z + region_effect)
    p0 = np.clip(_sigmoid(logit_p0), 0.02, 0.95)

    # ---- 4. Heterogeneous treatment effect (in probability points) -----------
    persuadability = _sigmoid(0.9 * recency_z - 1.1 * eng_z - 0.8 * loyal - 0.35 * freq_z + 0.3)
    pull_forward = ((recency <= 7) & (engagement >= 0.6)).astype(float)
    tau_raw = -0.015 + 0.14 * persuadability - 0.03 * pull_forward
    tau = np.clip(tau_raw, 0.01 - p0, 0.99 - p0)  # keeps p_discount inside [0.01, 0.99]
    p1 = p0 + tau
    true_effect = p1 - p0  # defined as the difference, so the identity is exact

    # ---- 5. Potential outcomes and the outcome we actually observe -----------
    u = rng.uniform(size=n)
    y0 = (u < p0).astype(int)
    y1 = (u < p1).astype(int)
    purchased = np.where(treated == 1, y1, y0)

    # ---- 6. Money -------------------------------------------------------------
    list_value = aov * np.exp(rng.normal(0.0, LIST_VALUE_SIGMA, n))  # price before discount
    order_value = np.round(purchased * list_value * (1.0 - DISCOUNT_DEPTH * treated), 2)
    discount_cost = np.round(purchased * list_value * DISCOUNT_DEPTH * treated, 2)

    observed = pd.DataFrame({
        "customer_id": np.arange(1, n + 1),
        "age": age,
        "tenure_months": tenure,
        "past_purchases_12m": past_purchases,
        "avg_order_value_past": aov,
        "days_since_last_purchase": recency,
        "email_engagement": np.round(engagement, 4),
        "is_loyalty_member": loyal,
        "region": region,
        "discount_offered": treated,
        "purchased": purchased,
        "order_value": order_value,
        "discount_cost": discount_cost,
    })[list(COLUMN_NAMES)]

    truth = pd.DataFrame({
        "customer_id": np.arange(1, n + 1),
        "true_propensity": propensity,
        "p_no_discount": p0,
        "p_discount": p1,
        "true_effect": true_effect,
        "expected_list_value": aov * np.exp(LIST_VALUE_SIGMA ** 2 / 2.0),
    })[list(TRUTH_COLUMNS)]

    return observed, truth
