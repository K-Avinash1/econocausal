"""Refutation tests for the estimated average discount effect (Day 10).

A refutation test does NOT prove the causal assumptions. It changes the data in a way whose
correct answer is known, re-runs the same estimator, and checks that the estimate behaves
accordingly. A test that passes means "this check found no problem"; a test that fails is a
warning that the result should not be trusted until understood.

Three tests, following the definitions of DoWhy's refuters but run on EconoCausal's own
estimation pipeline (the same features, estimator and settings as the real analysis):

  placebo_treatment   Shuffle who got the discount. The true effect of a shuffled discount is 0,
                      so the re-estimated average effect should be close to 0.
  random_common_cause Add a column of random noise as an extra customer attribute. It cannot
                      matter, so the average effect should barely move.
  data_subset         Re-estimate on random 80% subsets of the customers. A stable result should
                      not change much.

Pass rule (fixed in docs/methodology.md, Decision record 4, before any result was seen; it is a
practical rule of thumb, NOT a statistical test):
  tolerance = 25% of the size of the original average effect.
  placebo: every placebo average effect has |value| <= tolerance.
  random common cause / subset: every re-estimate is within tolerance of the original.
If the original average effect is smaller than 0.005 the relative rule is meaningless and the
test is reported as inconclusive (passed = None).

Not done (documented limitation): sensitivity to an UNMEASURED confounder. No test on the data
can rule one out.
"""
import time
from typing import Callable, Dict, List, Optional

import numpy as np
import pandas as pd

from .effect_model import (
    EffectModelConfig, _check_usable, build_features, make_estimator, to_jsonable,
)
from .schema import OUTCOME_COL, TREATMENT_COL

TOLERANCE = 0.25            # fraction of the original average effect
MIN_EFFECT_FOR_RELATIVE = 0.005
TESTS = ("placebo_treatment", "random_common_cause", "data_subset")
SUBSET_FRACTION = 0.8

DISCLAIMER = (
    "Passing these tests does not prove the causal assumptions. They can reveal problems "
    "(for example an unstable estimate) but cannot rule out unmeasured confounders."
)


def _average_effect(X: np.ndarray, Y: np.ndarray, T: np.ndarray, config: EffectModelConfig,
                    estimator_factory: Optional[Callable]) -> float:
    estimator = (estimator_factory or make_estimator)(config)
    estimator.fit(Y, T, X=X, W=None)
    return float(np.mean(np.asarray(estimator.effect(X), dtype=float)))


def _result(name: str, title: str, what: str, expected: str, original: float,
            values: List[float], deviations: List[float], passed: Optional[bool],
            criterion: str, seconds: float) -> Dict:
    return {
        "name": name, "title": title, "what_it_does": what, "expected": expected,
        "original_average_effect": original, "re_estimates": values,
        "deviations": deviations, "passed": passed, "criterion": criterion,
        "seconds": round(seconds, 1),
    }


def run_refutations(df: pd.DataFrame, config: Optional[EffectModelConfig] = None,
                    n_sims: int = 3, seed: int = 7, tests: Optional[List[str]] = None,
                    estimator_factory: Optional[Callable] = None) -> Dict:
    """Run the refutation tests on `df` (which must pass validation) and return a JSON-safe dict."""
    config = config or EffectModelConfig.quick("linear")
    if n_sims < 1 or n_sims > 20:
        raise ValueError("n_sims must be between 1 and 20")
    tests = list(tests) if tests else list(TESTS)
    unknown = [t for t in tests if t not in TESTS]
    if unknown:
        raise ValueError(f"unknown test(s): {unknown}; choose from {list(TESTS)}")
    _check_usable(df)

    X = build_features(df).to_numpy(dtype=float)
    Y = df[OUTCOME_COL].to_numpy(dtype=float)
    T = df[TREATMENT_COL].to_numpy(dtype=int)
    n = len(df)
    rng = np.random.default_rng(seed)

    started = time.perf_counter()
    original = _average_effect(X, Y, T, config, estimator_factory)
    relative_ok = abs(original) >= MIN_EFFECT_FOR_RELATIVE
    tolerance = TOLERANCE * abs(original)

    results = []
    for name in tests:
        t0 = time.perf_counter()
        values: List[float] = []
        if name == "placebo_treatment":
            for _ in range(n_sims):
                values.append(_average_effect(X, Y, rng.permutation(T), config, estimator_factory))
            deviations = [abs(v) for v in values]
            passed = (all(d <= tolerance for d in deviations) if relative_ok else None)
            results.append(_result(
                name, "Placebo treatment",
                "Randomly shuffles which customers were offered the discount, then re-estimates the average effect.",
                "A shuffled discount has no real effect, so the estimate should be close to 0.",
                original, values, deviations, passed,
                f"every placebo average effect must be within +/-{tolerance:.4f} of 0 "
                f"({int(TOLERANCE * 100)}% of the original effect)", time.perf_counter() - t0))
        elif name == "random_common_cause":
            for _ in range(n_sims):
                noise = rng.normal(size=(n, 1))
                values.append(_average_effect(np.hstack([X, noise]), Y, T, config, estimator_factory))
            deviations = [abs(v - original) for v in values]
            passed = (all(d <= tolerance for d in deviations) if relative_ok else None)
            results.append(_result(
                name, "Random common cause",
                "Adds a column of random noise as an extra customer attribute, then re-estimates.",
                "Noise cannot matter, so the average effect should barely change.",
                original, values, deviations, passed,
                f"every re-estimate must be within +/-{tolerance:.4f} of the original "
                f"({int(TOLERANCE * 100)}% of the original effect)", time.perf_counter() - t0))
        else:  # data_subset
            size = max(2, int(round(SUBSET_FRACTION * n)))
            for _ in range(n_sims):
                idx = rng.choice(n, size=size, replace=False)
                values.append(_average_effect(X[idx], Y[idx], T[idx], config, estimator_factory))
            deviations = [abs(v - original) for v in values]
            passed = (all(d <= tolerance for d in deviations) if relative_ok else None)
            results.append(_result(
                name, "Data subset",
                f"Re-estimates on random {int(SUBSET_FRACTION * 100)}% subsets of the customers.",
                "A stable result should not change much when 20% of the customers are left out.",
                original, values, deviations, passed,
                f"every re-estimate must be within +/-{tolerance:.4f} of the original "
                f"({int(TOLERANCE * 100)}% of the original effect)", time.perf_counter() - t0))

    out = {
        "original_average_effect": original,
        "tolerance_absolute": tolerance if relative_ok else None,
        "settings": {"estimator": config.estimator, "n_sims": n_sims, "seed": seed,
                     "tolerance_fraction": TOLERANCE, "n_customers": int(n),
                     "n_folds": config.n_folds},
        "results": results,
        "n_passed": sum(1 for r in results if r["passed"] is True),
        "n_failed": sum(1 for r in results if r["passed"] is False),
        "n_inconclusive": sum(1 for r in results if r["passed"] is None),
        "total_seconds": round(time.perf_counter() - started, 1),
        "not_done": ["Sensitivity to an unmeasured confounder (cannot be ruled out from the data)."],
        "disclaimer": DISCLAIMER,
    }
    if not relative_ok:
        out["note"] = ("The original average effect is very close to 0, so the relative rule cannot "
                       "be applied and the tests are inconclusive.")
    return to_jsonable(out)
