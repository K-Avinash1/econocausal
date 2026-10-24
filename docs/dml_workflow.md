# DML workflow (Day 8-9)

Code: `backend/econocausal/effect_model.py`. Run: `python scripts/run_first_model.py --quick`.

## What the model estimates
For each customer, the change in purchase probability if they are offered the 15% discount
(the CATE, "tau"). `0.07` means 7 percentage points. Binary treatment (`discount_offered`),
binary outcome (`purchased`).

## Inputs (and only these)
7 numeric attributes + region as 3 one-hot columns = 10 columns
(`age, tenure_months, past_purchases_12m, avg_order_value_past, days_since_last_purchase,
email_engagement, is_loyalty_member, region_South, region_East, region_West`; North is the
reference). All 8 attributes are both confounders (they drive who got a discount and who buys)
and effect modifiers (the effect may differ by them), as decided in `docs/causal_graph.md`.
Never inputs: `customer_id`, `order_value`, `discount_cost`, any simulated truth.

## The steps of double machine learning
1. Split the customers into K folds (K = 5; `--quick` uses 3).
2. For each fold, train on the other folds a model that predicts the outcome from the attributes
   and a model that predicts the discount from the attributes (the "nuisance" models, random forests).
3. Predict the held-out fold with them. No customer is predicted by a model that saw them
   (cross-fitting), which limits overfitting bias.
4. Remove the predicted parts: outcome residual = actual outcome - predicted outcome; treatment
   residual = actual discount - predicted chance of discount.
5. The final stage learns how the outcome residual moves with the treatment residual, allowing
   the relationship to depend on the attributes. That learned relationship is tau(x).

## Estimators
| name | what | intervals | role |
|---|---|---|---|
| `causal_forest` | `CausalForestDML` | yes | default; non-linear heterogeneity |
| `linear` | `LinearDML` | yes | simple baseline; effect linear in the attributes |
| `t_learner` | two random forests | no | non-DML comparison; also what the sandbox fixture used |

## Settings (first-run values, NOT tuned)
`n_folds=5, nuisance_trees=100, nuisance_min_leaf=20, effect_trees=200, effect_min_leaf=20,
confidence_level=0.95, random_state=42`. Any change goes in a decision record with the reason.
Tuning on the true effects would be cheating; tune only on observed-data criteria.

## Baseline probability p0
Needed by the optimizer (`tau/p0 > 0.1765`). Cross-fitted random forest on the untreated
customers of the training folds, clipped to 0.01-0.99.

## Output shape (`EffectResult.to_dict`)
`run` (estimator, settings, library versions, fit seconds), `average_effect`
(`ate, ci_low, ci_high`, `confidence_level`), `effect_summary` (percentiles, share positive /
negative), `customers_total`, `customers_returned`, `customers`
(`customer_id, effect, effect_low, effect_high, baseline_purchase_prob, expected_list_value`),
`notes`, and for simulations only `evaluation`. Intervals are `null` when unavailable.

## Checking against the truth (simulation only)
`evaluate_recovery` fits on a random 70% and compares estimates with `true_effect` on the other
30%: average-effect error, RMSE, rank correlation, true effect of the top/bottom 20% ranked,
interval coverage, and the naive treated-vs-untreated difference for contrast. This shows the
method recovers known effects when the simulation's assumptions hold. It is not evidence about
real customers.

## Limits
- Valid only if there are no unmeasured confounders (assumption, untestable; refutation tests Day 10).
- Effects near the 0.10/0.90 propensity edges rest on few comparable customers.
- Uploaded files have no ground truth: no evaluation block, no accuracy claim.
