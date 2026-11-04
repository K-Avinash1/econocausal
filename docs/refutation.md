# Refutation tests (Day 10)

Code: `backend/econocausal/refutation.py`. Run: `python scripts/run_refutation.py`.
API: `POST /refute/{run_id}`.

## What a refutation test is
A refutation test changes the data in a way whose correct answer is known, runs the SAME estimator
again, and checks that the estimate behaves as it should. It can reveal a problem. It cannot prove
the causal assumptions (above all, "no unmeasured confounders"). **Passing is not proof.**

The tests follow the definitions of DoWhy's refuters but run on EconoCausal's own pipeline
(same features, estimator and settings as the real analysis), so they test what we actually report.

## The three tests
| test | what is done | expected result |
|---|---|---|
| Placebo treatment | randomly shuffle who got the discount | no real effect, estimate near 0 |
| Random common cause | add a column of random noise as an extra attribute | estimate barely changes |
| Data subset | re-estimate on random 80% subsets of the customers | estimate stays similar |

Each is repeated `n_sims` times (default 3) with a fixed seed (7).

## Decision record 4 (4 Nov 2026): pass rule
Fixed BEFORE seeing any result, to avoid choosing the rule to suit the answer.
- tolerance = 25% of the size of the original average effect.
- Placebo: every placebo average effect must be within +/- tolerance of 0.
- Random common cause and data subset: every re-estimate must be within +/- tolerance of the original.
- If the original average effect is smaller than 0.005 in size, the relative rule is meaningless and the
  tests are reported as INCONCLUSIVE (not passed).
- This is a practical rule of thumb, NOT a statistical test. 25% and 3 repeats are first choices
  and can be tightened if runtime allows (record any change here with the reason).

## How to read the result
- PASS: this check found no problem.
- FAIL: do not trust the average effect until you understand why (noisy forest, too few trees, a
  data problem). Report it honestly; do not tune settings until the test passes.
- INCONCLUSIVE: the effect is too close to 0 for a relative rule.

## Not done (limitation)
Sensitivity to an UNMEASURED confounder: no test on the data can rule one out. It is stated in every
report (`not_done`) and in the dashboard.

## Output shape
`original_average_effect`, `tolerance_absolute`, `settings`, `results[]` (`name`, `title`,
`what_it_does`, `expected`, `re_estimates`, `deviations`, `passed` true/false/null, `criterion`,
`seconds`), `n_passed`, `n_failed`, `n_inconclusive`, `total_seconds`, `not_done`, `disclaimer`.

## Viva questions
1. What does a refutation test do, and what can it not do?
2. Why should a shuffled discount give an effect near 0?
3. Why add random noise as an attribute, and what should happen?
4. Why was the pass rule fixed before seeing results?
5. A test fails. What do you do and not do?
6. Which assumption can no test on the data confirm?
