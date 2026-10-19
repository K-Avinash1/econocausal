# Methodology

Decisions are recorded here before they become implementation assumptions. Sections for DML,
refutation, PSM, uplift/Qini and drift are added as those stages are built.

## Decision record 1. Treatment and outcome (approved 17 Oct 2026)
- Treatment: binary, one fixed discount depth of 15% (PSM and Qini both need a yes/no treatment).
- Outcome for causal estimation: `purchased` (0/1). The estimand is the effect of the discount on
  purchase probability, per customer (CATE) and on average (ATE).
- A multi-level discount is deferred.

## Decision record 2. Optimizer objective (documented 18 Oct 2026, before any optimizer code)

### The objective is incremental NET REVENUE, not profit
The data contain no product cost or margin, so **this project does not claim to optimise profit**.
The objective is the expected **incremental net revenue** from offering the discount: extra money
received, with the discount already deducted.

Notation, for customer i with discount depth d = 0.15:
- p0 = purchase probability without the discount, p1 = with it, tau = p1 - p0
- V = list (pre-discount) order value if the customer buys

Expected net revenue without the discount: `p0 x V`.
Expected net revenue with the discount: `p1 x V x (1 - d)`.

```
incremental net revenue  =  p1 V (1 - d)  -  p0 V
                         =  tau V (1 - d)  -  p0 V d
```
Equivalent reading: `tau V` of extra list-price sales, minus the discount given away
`p1 V d`. Do **not** subtract `discount_cost` again from `order_value`: `order_value` is already
the amount paid after the discount, so doing both would double-count the cost.

### Consequences
- A discount is worth giving only if `tau (1 - d) > p0 d`, i.e. `tau / p0 > d / (1 - d) = 0.1765`.
  Customers who would buy anyway (high `p0`) are costly to discount even when `tau` is positive.
  So the optimizer needs an estimate of **both** `tau` (from the DML model) **and** `p0`.
- `V` is estimated from the customer's history and purchases (for treated purchases the list value
  is `order_value / 0.85`). Assumption: the discount does not change the list value of an order.
- Budget (proposed, to be confirmed on Day 19): the expected discount given away,
  `sum_i x_i p1_i V_i d`, must not exceed the budget B, with `x_i` between 0 and 1.

### What this is not
- Not profit. Extra sales cost money to supply; with no margin, incremental net revenue can
  overstate the value of an extra sale.
- If a margin or product-cost assumption is supplied later it will be labelled "estimated
  incremental contribution under an assumed margin of m%" and shown separately. Until then no
  result may be described as profit.

## Open items
- Estimator configuration (Day 8), refutation tests (Day 10), uplift/Qini (Day 12), PSM (Day 16),
  optimizer constraints (Day 19), drift statistics (Day 23).
