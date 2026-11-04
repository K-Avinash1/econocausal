# Validation display spec

The Validation tab shows the results of the causal refutation tests for one analysis.

Shows, in this order:
1. A banner saying where the result comes from: a saved example, or a live result for the current analysis.
   If the estimator is the simple baseline (t_learner), say it is a development sample.
2. An "How to read this" box with the disclaimer: passing does not prove the causal assumptions.
3. A summary: how many tests passed, failed, inconclusive; the original average effect and the tolerance.
4. One card per test: title, a Passed / Failed / Inconclusive badge, what the test does,
   what is expected, the re-estimated average effects, and the rule used.
5. A "Not checked (limitations)" list that is always visible.

Rules:
- Effects are shown in percentage points, two decimals (0.0215 -> 2.15 pp).
- A failed test is shown as plainly as a passed one. Never hide or soften it.
- Never write "proven", "validated" or "confirmed". Use "passed this check".
- Never show a blank or NaN: null becomes "n/a".
- Live checks can take a minute: show a "Running..." message and disable the button.