# Model interface: inputs and outputs (draft v0.1, Day 6)

Status: v0.1, section 4 answered by Avinash on 21 Oct 2026. Nothing in this file is
implemented yet except `POST /validate`. Numbers in the examples are placeholders that show the
SHAPE of a response, not results.
Owner: Avinash (backend and model contracts). Zahra uses this file on Day 8 to design the results display.

## 1. What goes in
| Input | Source | Rule |
|---|---|---|
| Customer table | an uploaded CSV that passed `POST /validate`, or the generated demo data | the 13 columns in `docs/dataset_schema.md`, no errors reported |
| Treatment | `discount_offered` | 0/1, fixed 15% depth |
| Outcome | `purchased` | 0/1 |
| Controls and effect modifiers | the 8 customer attributes in `docs/causal_graph.md` | which of them go in X (effect modifiers) and which in W (controls only) is decided on Day 8 |
| Never used as inputs | `customer_id`, `order_value`, `discount_cost` | identifier, and results measured after the offer |
| Never reaches the model | `data/evaluation/ground_truth.csv` | true effects are for evaluating the model on simulated data only |

## 2. What comes out
One result object per analysis run.

```json
{
  "run": {
    "data_source": "upload",
    "n_customers": 20000,
    "estimator": "LinearDML",
    "seed": 42,
    "library_versions": {"econml": "0.17.0"}
  },
  "average_effect": {
    "ate": 0.07,
    "ci_low": 0.06,
    "ci_high": 0.08,
    "confidence_level": 0.95,
    "meaning": "change in purchase probability; 0.07 = 7 percentage points"
  },
  "customers": [
    {
      "customer_id": 1,
      "effect": 0.08,
      "effect_low": 0.02,
      "effect_high": 0.14,
      "baseline_purchase_prob": 0.21,
      "expected_list_value": 58.3
    }
  ],
  "notes": ["Estimates assume no unmeasured confounders (docs/causal_graph.md)."]
}
```
(placeholder numbers: this is a shape example only)

| Field | Type and range | Used for |
|---|---|---|
| `effect` | number, -1 to 1 | the estimated change in this customer's purchase probability if offered the discount (CATE) |
| `effect_low`, `effect_high` | numbers, `effect_low` <= `effect_high` | uncertainty range for the customer's effect |
| `baseline_purchase_prob` | number, 0 to 1 | p0, the chance of buying WITHOUT the discount; the optimizer needs it (docs/methodology.md, Decision record 2) |
| `expected_list_value` | number, >= 0 | V, expected pre-discount order value; the optimizer needs it |
| `ate`, `ci_low`, `ci_high` | numbers | average effect over all customers |

Rules for every response:
1. Probabilities stay between 0 and 1. A missing number is `null`, never `NaN`.
2. A response for UPLOADED data never contains true effects. Only a run on the generated
   simulation data may add an `evaluation` block (for example `true_ate`, error of the estimated
   effects), labelled "simulation".
3. Failures use the same shape as `/validate`: `{"ok": false, "errors": [{"code", "column", "message"}], ...}`.
4. A result is never shown if the data failed validation or has no treatment variation.

## 3. Endpoints
| Endpoint | State | Purpose |
|---|---|---|
| `GET /health` | built (Day 6) | is the server up |
| `POST /validate` | built (Day 5) | check an uploaded CSV, return messages, summary, preview |
| `POST /analyze` | planned (Day 9 to 11) | run the effect estimation on a validated CSV and return section 2 |
| `GET /demo` | planned (Day 11) | run on the generated sample data so the dashboard has something to show |
| refutation, uplift, PSM, optimize, drift | planned (Day 10 onward) | one endpoint each, formats defined when they are built |
| `GET /results/{run_id}/customers` | planned (Day 9 to 11) | page through customer results |

## 4. Decisions (answered 21 Oct 2026)
1. **Uncertainty method.** Every run must return a 95% interval per customer. The method is chosen on Day 8 together with the final-stage model. If the chosen method cannot give an interval, `effect_low` and `effect_high` are `null` and the dashboard says "interval not available". Intervals are never invented.
2. **`baseline_purchase_prob`.** Approved as proposed: a separate outcome model fitted on untreated customers only, cross-fitted so no customer is scored by a model that saw them, and kept between 0.01 and 0.99. It relies on the same no-unmeasured-confounders assumption as the effect estimate.
3. **`expected_list_value`.** Approved as proposed: the customer's `avg_order_value_past`. On the simulated data the truth file lets us measure the error (by construction the true expected list value is about 3% above `avg_order_value_past`). That error is reported, not hidden.
4. **Effect modifiers.** Approved as the starting setup: all 8 attributes in X, with `region` one-hot encoded. Day 8 may change this and must record why.
5. **Response size.** Approved with one change: `POST /analyze` returns the summary and a `run_id`. Customers are read with `GET /results/{run_id}/customers?offset=0&limit=100` (limit at most 1000), and the full table is a CSV download.

## 5. Viva questions
1. Why is `baseline_purchase_prob` in the output when the question is about the discount effect?
2. Why must true effects never be returned for uploaded data?
3. Why are `order_value` and `discount_cost` not model inputs?
