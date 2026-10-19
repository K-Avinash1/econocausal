# Dataset schema and data-generation design

Status: approved by Avinash (17-18 Oct 2026). Code: `backend/econocausal/schema.py`,
`backend/econocausal/data_generation.py`. If this document and the code disagree, the code
is the truth and this document must be fixed.

## 1. Purpose and the one-line story

A retailer sent a past discount campaign. The people who ran it did not pick customers at
random: they favoured loyal, frequent, high-spending, engaged customers. We want to know,
for each customer, how much the discount changed their chance of buying (not just who buys).

- **Treatment** (`discount_offered`): 1 = offered one fixed discount of **15%**, 0 = not offered.
- **Outcome used for causal estimation** (`purchased`): 1 = bought, 0 = did not.
- `order_value` and `discount_cost` are kept for the optimizer (see `docs/methodology.md`).

## 2. Observed data: `data/generated/campaign_data.csv`

| Column | Meaning | Type | Allowed values in uploads |
|---|---|---|---|
| `customer_id` | unique customer identifier | integer | >= 1, unique |
| `age` | years | integer | 18 to 75 |
| `tenure_months` | months as a customer | integer | 0 to 120 |
| `past_purchases_12m` | orders in the last 12 months | integer | 0 to 60 |
| `avg_order_value_past` | typical past order value (currency units) | number | >= 0 |
| `days_since_last_purchase` | recency | integer | 0 to 730 |
| `email_engagement` | share of marketing emails opened | number | 0 to 1 |
| `is_loyalty_member` | in the loyalty programme | 0 / 1 | 0 or 1 |
| `region` | customer region | text | North, South, East, West |
| `discount_offered` | **treatment** | 0 / 1 | 0 or 1 |
| `purchased` | **outcome** | 0 / 1 | 0 or 1 |
| `order_value` | amount **paid** after discount; 0 if no purchase | number | >= 0 |
| `discount_cost` | discount **given away**; 0 if untreated or no purchase | number | >= 0 |

Notes on the approved schema:
- No column was added to the observed data. The list (pre-discount) price of a purchase is
  exactly recoverable: for a treated purchase `list value = order_value / (1 - 0.15)`, for an
  untreated purchase `list value = order_value`.
- Two upload rules are slightly looser than first proposed: `past_purchases_12m` may be 0 and
  `avg_order_value_past` may be 0 (a customer with no history). Generated data always has at
  least one past purchase.

## 3. Separate evaluation file: `data/evaluation/ground_truth.csv` (simulation only)

Real data has no such file. It is never given to a model and never shown as observed data.

| Column | Meaning |
|---|---|
| `customer_id` | joins to the observed data |
| `true_propensity` | true probability of being offered the discount |
| `p_no_discount` | true purchase probability without the discount |
| `p_discount` | true purchase probability with the discount |
| `true_effect` | `p_discount - p_no_discount` (exact) |
| `expected_list_value` | expected pre-discount order value if the customer buys |

`true_propensity` is needed to check overlap and PSM. `expected_list_value` is needed to compute
the *true* incremental value of any targeting rule when the optimizer is evaluated. Both are
evaluation-only columns that do not change the observed schema.

## 4. Validation rules (`backend/econocausal/validation.py`)

Errors reject the file; warnings let it through.
- Errors: no rows; fewer than 200 rows; missing required columns; empty values; text in a numeric
  column; values outside the allowed range; non-integers in integer columns; values other than
  0/1 in binary columns; region not in the list; duplicate `customer_id`; no treatment variation
  (everyone or no one offered); fewer than 50 customers in the smaller treatment group; the outcome
  has a single value; money in rows with no purchase; a purchase with zero `order_value`;
  `discount_cost` > 0 for customers who were not offered the discount.
- Warnings: 200 to 999 rows; extra columns (ignored); fewer than 5% of customers in one treatment
  group; `discount_cost` that does not match a 15% discount.
- Avinash finalises the backend rules on Day 5; these are the Day 3 starting point.

## 5. How the data is generated

Fixed seed (default 42) and `numpy.random.default_rng`. N = 20,000 by default.
`sigma(x) = 1 / (1 + exp(-x))`; `L` = `is_loyalty_member`; `T` = `discount_offered`.

### 5.1 Customer features
- `age` ~ Normal(42, 13), rounded, clipped to [18, 75].
- `region`: North 0.30, South 0.25, East 0.25, West 0.20.
- `tenure_months` = round( Gamma(shape 2, scale 14) x (0.6 + 0.4 x (age - 18)/57) ), clipped to [0, 120].
- `L` ~ Bernoulli( sigma(-1.5 + 0.03 x tenure) ).
- `past_purchases_12m` = 1 + Poisson( exp(0.5 + 0.010 x tenure + 0.45 x L) ), at most 60.
- `email_engagement` ~ Beta(2 + 1.5 x L, 3).
- `days_since_last_purchase` = round( Exponential(mean 90 / (1 + 0.15 x past_purchases)) ), clipped to [0, 365].
- `avg_order_value_past` = max( exp( Normal(ln 55 + 0.004 x (age - 40), 0.35) ), 1 ), 2 decimals.

Standardised helpers (fixed constants, not estimated from the data):
`freq_z = (ln(past_purchases) - 1.5) / 0.7`, `recency_z = (days - 45) / 45`,
`eng_z = (email_engagement - 0.5) / 0.2`, `aov_z = (ln(avg_order_value_past) - ln 55) / 0.35`,
`tenure_z = (tenure - 22) / 17`. `region_effect`: North +0.15, South 0, East -0.15, West +0.05.

### 5.2 Treatment assignment (this creates the confounding)
```
logit(e) = -0.50 + 0.45 L + 0.35 freq_z + 0.25 aov_z + 0.20 eng_z - 0.15 recency_z
e        = clip( sigma(logit(e)), 0.10, 0.90 )          # true_propensity; guarantees overlap
T        ~ Bernoulli(e)
```
Loyal, frequent, high-value, engaged and recent customers are more likely to be offered the
discount. These are the same customers who buy more anyway, so a plain comparison of offered vs
not-offered customers overstates the discount's effect. This is the confounding the DML model
must remove.

### 5.3 Purchase probability without the discount
```
logit(p0) = -1.25 + 0.60 L + 0.55 freq_z + 0.45 eng_z - 0.55 recency_z
            + 0.20 aov_z + 0.12 tenure_z + region_effect
p0        = clip( sigma(logit(p0)), 0.02, 0.95 )         # p_no_discount
```

### 5.4 Heterogeneous treatment effect (change in purchase probability)
```
s       = sigma( 0.9 recency_z - 1.1 eng_z - 0.8 L - 0.35 freq_z + 0.3 )   # "persuadability"
PF      = 1 if days_since_last_purchase <= 7 and email_engagement >= 0.6, else 0   # pull-forward
tau_raw = -0.015 + 0.14 s - 0.03 PF
tau     = clip( tau_raw, 0.01 - p0, 0.99 - p0 )          # keeps p1 inside [0.01, 0.99]
p1      = p0 + tau                                        # p_discount
true_effect = p1 - p0                                     # exact identity
```
- Persuadable customers (long since last purchase, low engagement, not loyal) respond most.
- Loyal, engaged, frequent customers would buy anyway, so the discount adds little.
- A small group (very recent, highly engaged buyers) responds slightly negatively: the discount
  pulls forward a purchase they would have made at full price.

### 5.5 Outcomes
One shared uniform draw `U ~ Uniform(0,1)` per customer gives both potential outcomes:
`Y0 = 1 if U < p0`, `Y1 = 1 if U < p1`. The **observed** outcome is `purchased = Y1` if `T = 1`,
else `Y0`. The unobserved potential outcome is never written to the observed file.

### 5.6 Money
`list value V = avg_order_value_past x exp(Normal(0, 0.25))`.
`order_value = purchased x V x (1 - 0.15 T)`; `discount_cost = purchased x V x 0.15 x T`. Both are
rounded to 2 decimals. Simplifying assumption: the discount changes whether a customer buys, not
the list value of what they buy.

## 6. Probability and effect guarantees (and the tests that check them)

| Guarantee | Test in `backend/tests/test_generator.py` |
|---|---|
| `true_propensity` in [0.10, 0.90]; `p_no_discount` in [0.02, 0.95]; `p_discount` in [0.01, 0.99] | `test_probabilities_stay_in_valid_range` |
| `true_effect == p_discount - p_no_discount` | `test_true_effect_equals_p_discount_minus_p_no_discount` |
| effects vary, mostly positive, a small negative group | `test_effects_are_heterogeneous` |
| treatment is confounded but both groups exist everywhere | `test_treatment_assignment_is_confounded_but_has_overlap` |
| naive comparison is biased upward | `test_naive_comparison_is_biased_upward` |
| observed outcomes match the true probabilities | `test_observed_outcomes_match_the_true_probabilities` |
| money columns are consistent | `test_money_columns_are_consistent` |
| same seed gives identical data | `test_same_seed_gives_identical_data` |

## 7. Limits
- Simulated data. Recovering known effects shows a method works under these assumptions, not on
  real customers.
- All confounders are observed in the simulation. Real data may have unobserved confounding.
- One fixed discount depth; real campaigns vary.
- The discount does not change the list value of an order (a simplification).

## 8. Reproduce
```
python scripts/generate_data.py            # writes data/generated/ and data/evaluation/
python scripts/run_eda.py                  # writes docs/eda_report.md
pytest                                     # runs backend/tests
```
