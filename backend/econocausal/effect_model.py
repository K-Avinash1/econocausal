"""Treatment-effect estimation for EconoCausal (Day 8-9).

What this module does
  1. Turns a validated customer table into a numeric feature matrix.
  2. Fits a model of the effect of the discount (`discount_offered`) on
     `purchased` for each customer. Three estimators are available:
       "causal_forest"  CausalForestDML from EconML (default; non-linear effects, intervals)
       "linear"         LinearDML from EconML (simple, effects linear in the features)
       "t_learner"      two random forests (a simple BASELINE, not double machine learning)
  3. Estimates each customer's purchase probability WITHOUT the discount
     (needed later by the optimizer, see docs/methodology.md).
  4. Packages everything in the response shape described in docs/dml_workflow.md.

Rules enforced here
  * The model only ever sees columns from docs/causal_graph.md. `customer_id`,
    `order_value` and `discount_cost` are never model inputs.
  * Simulated "true" effects are never an input. They are used only inside
    evaluate_recovery(), which compares estimates with the truth on simulated data.
  * No number is invented: if an interval cannot be computed it is None, with a note.

EconML is imported only when a DML estimator is requested, so everything else
can be tested without it. The EconML calls themselves can only be verified on a
machine where EconML is installed (Avinash's PC).
"""
import importlib.metadata as importlib_metadata
import platform
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import KFold

from .schema import (
    ID_COL, NUMERIC_FEATURE_COLS, OUTCOME_COL, REGIONS, TREATMENT_COL,
)
from .validation import validate_campaign_data

ESTIMATORS: Tuple[str, ...] = ("causal_forest", "linear", "t_learner")
ESTIMATOR_LABELS: Dict[str, str] = {
    "causal_forest": "CausalForestDML (EconML)",
    "linear": "LinearDML (EconML)",
    "t_learner": "T-learner with random forests (simple baseline, not double machine learning)",
}

# Region becomes 0/1 columns. The first region (North) is the reference group.
REGION_DUMMIES: Tuple[str, ...] = tuple(f"region_{r}" for r in REGIONS[1:])
MODEL_FEATURES: Tuple[str, ...] = tuple(NUMERIC_FEATURE_COLS) + REGION_DUMMIES

BASELINE_CLIP = (0.01, 0.99)      # purchase probability without the discount is kept inside this range
EFFECT_LIMIT = 1.0                # an effect on a probability cannot leave [-1, 1]
CONFOUNDER_NOTE = "Estimates assume no unmeasured confounders (see docs/causal_graph.md)."
UNITS_NOTE = "Effects are changes in purchase probability: 0.07 means 7 percentage points."


class ModelInputError(ValueError):
    """The data cannot be used for effect estimation. `.messages` are plain-English reasons."""

    def __init__(self, messages: List[str]):
        self.messages = list(messages)
        super().__init__(" ".join(self.messages))


class ModelDependencyError(RuntimeError):
    """A required library (EconML) is missing from this Python environment."""


@dataclass(frozen=True)
class EffectModelConfig:
    """Every setting that changes the result. First-run values, NOT tuned (docs/dml_workflow.md)."""

    estimator: str = "causal_forest"
    n_folds: int = 5               # cross-fitting folds for the nuisance models
    nuisance_trees: int = 100      # trees in each nuisance random forest
    nuisance_min_leaf: int = 20    # minimum customers per leaf in a nuisance tree
    effect_trees: int = 200        # trees in the causal forest (must be a multiple of 4)
    effect_min_leaf: int = 20      # minimum customers per leaf in the causal forest
    confidence_level: float = 0.95
    random_state: int = 42
    n_jobs: int = -1

    def __post_init__(self):
        if self.estimator not in ESTIMATORS:
            raise ValueError(f"estimator must be one of {ESTIMATORS}, not {self.estimator!r}")
        if self.n_folds < 2:
            raise ValueError("n_folds must be at least 2")
        if self.nuisance_trees < 1 or self.effect_trees < 1:
            raise ValueError("tree counts must be at least 1")
        if self.nuisance_min_leaf < 1 or self.effect_min_leaf < 1:
            raise ValueError("min leaf sizes must be at least 1")
        if self.estimator == "causal_forest" and self.effect_trees % 4 != 0:
            raise ValueError("effect_trees must be a multiple of 4 for the causal forest")
        if not 0.0 < self.confidence_level < 1.0:
            raise ValueError("confidence_level must be between 0 and 1")

    @classmethod
    def quick(cls, estimator: str = "causal_forest", **overrides) -> "EffectModelConfig":
        """Smaller, faster settings for a first run or a test."""
        values = dict(estimator=estimator, n_folds=3, nuisance_trees=50, effect_trees=100)
        values.update(overrides)
        return cls(**values)

    def to_dict(self) -> Dict:
        return {
            "estimator": self.estimator, "n_folds": self.n_folds,
            "nuisance_trees": self.nuisance_trees, "nuisance_min_leaf": self.nuisance_min_leaf,
            "effect_trees": self.effect_trees, "effect_min_leaf": self.effect_min_leaf,
            "confidence_level": self.confidence_level, "random_state": self.random_state,
        }


# ----------------------------------------------------------------------------
# Features
# ----------------------------------------------------------------------------
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Numeric model inputs: 7 numeric attributes + 3 region 0/1 columns (10 columns)."""
    needed = list(NUMERIC_FEATURE_COLS) + ["region"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ModelInputError([f"These columns are needed to build the model inputs: {', '.join(missing)}."])
    features = df[list(NUMERIC_FEATURE_COLS)].astype(float).reset_index(drop=True)
    region = df["region"].astype(str).reset_index(drop=True)
    for name in REGIONS[1:]:
        features[f"region_{name}"] = (region == name).astype(float)
    return features[list(MODEL_FEATURES)]


def _check_usable(df: pd.DataFrame) -> None:
    report = validate_campaign_data(df)
    if not report.ok:
        raise ModelInputError([e["message"] for e in report.errors])


# ----------------------------------------------------------------------------
# Simple baseline estimator (not DML). Same interface as the EconML estimators.
# ----------------------------------------------------------------------------
class TLearner:
    """Fit one outcome model for treated and one for untreated customers; effect = difference.

    Used as an honest, simple comparison. It is NOT double machine learning and offers no intervals.
    """

    def __init__(self, n_trees: int, min_leaf: int, random_state: int, n_jobs: int = -1):
        self._params = dict(n_estimators=n_trees, min_samples_leaf=min_leaf,
                            random_state=random_state, n_jobs=n_jobs)

    def fit(self, Y, T, X=None, W=None):
        X = np.asarray(X, dtype=float)
        Y = np.asarray(Y, dtype=float)
        T = np.asarray(T)
        self._treated = RandomForestRegressor(**self._params).fit(X[T == 1], Y[T == 1])
        self._control = RandomForestRegressor(**self._params).fit(X[T == 0], Y[T == 0])
        return self

    def effect(self, X):
        X = np.asarray(X, dtype=float)
        return self._treated.predict(X) - self._control.predict(X)

    def effect_interval(self, X, alpha=0.05):
        raise NotImplementedError("The T-learner baseline does not provide intervals.")

    def ate_interval(self, X, alpha=0.05):
        raise NotImplementedError("The T-learner baseline does not provide intervals.")


def make_estimator(config: EffectModelConfig):
    """Build the estimator named in the config. DML estimators need EconML."""
    rs = config.random_state
    if config.estimator == "t_learner":
        return TLearner(config.nuisance_trees, config.nuisance_min_leaf, rs, config.n_jobs)

    try:
        from econml.dml import CausalForestDML, LinearDML
    except ImportError as exc:
        raise ModelDependencyError(
            "EconML is not installed in this Python environment. Activate the project's .venv "
            "(Python 3.11) and run: pip install -r backend/requirements.txt"
        ) from exc

    # Tree-based nuisance models: they predict the outcome and the treatment from the customer
    # attributes. Cross-fitting (cv) means no customer is predicted by a model that saw them.
    model_y = RandomForestRegressor(n_estimators=config.nuisance_trees,
                                    min_samples_leaf=config.nuisance_min_leaf,
                                    random_state=rs, n_jobs=config.n_jobs)
    model_t = RandomForestClassifier(n_estimators=config.nuisance_trees,
                                     min_samples_leaf=config.nuisance_min_leaf,
                                     random_state=rs, n_jobs=config.n_jobs)
    if config.estimator == "linear":
        return LinearDML(model_y=model_y, model_t=model_t, discrete_treatment=True,
                         cv=config.n_folds, random_state=rs)
    return CausalForestDML(model_y=model_y, model_t=model_t, discrete_treatment=True,
                           n_estimators=config.effect_trees, min_samples_leaf=config.effect_min_leaf,
                           cv=config.n_folds, random_state=rs, n_jobs=config.n_jobs)


# ----------------------------------------------------------------------------
# Fit and predict
# ----------------------------------------------------------------------------
def _flat(values, n: int, what: str) -> np.ndarray:
    array = np.asarray(values, dtype=float).reshape(-1)
    if array.shape[0] != n:
        raise ValueError(f"The model returned {array.shape[0]} {what} values for {n} customers.")
    return array


def _ate_interval(estimator, X: np.ndarray, alpha: float) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """Interval for the average effect, or (None, None, reason). Never invents a number."""
    try:
        low, high = estimator.ate_interval(X, alpha=alpha)
        return float(np.ravel(low)[0]), float(np.ravel(high)[0]), None
    except NotImplementedError:
        return None, None, "This estimator does not provide an interval for the average effect."
    except Exception as first_error:  # try one documented alternative before giving up
        try:
            summary = estimator.effect_inference(X).population_summary(alpha=alpha)
            low, high = summary.conf_int_mean(alpha=alpha)
            return float(np.ravel(low)[0]), float(np.ravel(high)[0]), None
        except Exception:
            return None, None, (
                "The interval for the average effect could not be computed "
                f"({type(first_error).__name__}: {str(first_error)[:100]})."
            )


class EffectModel:
    """A fitted estimator plus the settings used to fit it."""

    def __init__(self, config: EffectModelConfig, estimator, fit_seconds: float):
        self.config = config
        self.estimator = estimator
        self.fit_seconds = fit_seconds

    def predict(self, df: pd.DataFrame) -> Dict:
        """Per-customer effects for the rows of `df`.

        Returns {"effect", "low", "high", "ate", "ate_low", "ate_high", "notes"}; low/high and the
        ate interval are None when the estimator cannot give them.
        """
        X = build_features(df).to_numpy(dtype=float)
        n = X.shape[0]
        alpha = 1.0 - self.config.confidence_level
        notes: List[str] = []

        effect = _flat(self.estimator.effect(X), n, "effect")
        if not np.all(np.isfinite(effect)):
            raise ValueError("The model produced effects that are not finite numbers (NaN or infinity).")
        clipped = int(np.sum(np.abs(effect) > EFFECT_LIMIT))
        if clipped:
            effect = np.clip(effect, -EFFECT_LIMIT, EFFECT_LIMIT)
            notes.append(f"{clipped} effect(s) were outside -1 to 1 and were limited to that range.")

        low = high = None
        try:
            lo, hi = self.estimator.effect_interval(X, alpha=alpha)
            low, high = _flat(lo, n, "interval"), _flat(hi, n, "interval")
            if not (np.all(np.isfinite(low)) and np.all(np.isfinite(high))):
                low = high = None
                notes.append("Per-customer intervals contained invalid numbers and were left out.")
            else:
                low, high = np.minimum(low, effect), np.maximum(high, effect)
        except NotImplementedError:
            notes.append("This estimator does not provide per-customer intervals.")
        except Exception as error:
            low = high = None
            notes.append(f"Per-customer intervals could not be computed ({type(error).__name__}: {str(error)[:100]}).")

        ate = float(np.mean(effect))
        ate_low, ate_high, ate_note = _ate_interval(self.estimator, X, alpha)
        if ate_note:
            notes.append(ate_note)
        return {"effect": effect, "low": low, "high": high,
                "ate": ate, "ate_low": ate_low, "ate_high": ate_high, "notes": notes}


def fit_effect_model(df: pd.DataFrame, config: Optional[EffectModelConfig] = None,
                     estimator_factory: Optional[Callable] = None) -> EffectModel:
    """Validate `df`, then fit the estimator named in `config` on all its rows."""
    config = config or EffectModelConfig()
    _check_usable(df)
    X = build_features(df).to_numpy(dtype=float)
    Y = df[OUTCOME_COL].to_numpy(dtype=float)
    T = df[TREATMENT_COL].to_numpy(dtype=int)
    estimator = (estimator_factory or make_estimator)(config)
    started = time.perf_counter()
    estimator.fit(Y, T, X=X, W=None)
    return EffectModel(config, estimator, time.perf_counter() - started)


# ----------------------------------------------------------------------------
# Purchase probability without the discount (needed by the optimizer later)
# ----------------------------------------------------------------------------
def baseline_purchase_probabilities(df: pd.DataFrame, config: Optional[EffectModelConfig] = None) -> np.ndarray:
    """Cross-fitted estimate of P(purchase) if the customer is NOT offered the discount.

    A random forest is fitted on the UNTREATED customers of the training folds only and used to
    score the held-out fold, so no customer is scored by a model that saw them. Values are kept
    between 0.01 and 0.99. Relies on the same no-unmeasured-confounders assumption as the effect.
    """
    config = config or EffectModelConfig()
    X = build_features(df).to_numpy(dtype=float)
    Y = df[OUTCOME_COL].to_numpy(dtype=int)
    T = df[TREATMENT_COL].to_numpy(dtype=int)
    n = X.shape[0]
    overall_untreated = float(Y[T == 0].mean()) if np.any(T == 0) else 0.5
    probability = np.full(n, np.nan)
    folds = KFold(n_splits=min(config.n_folds, n), shuffle=True, random_state=config.random_state)
    for train_idx, test_idx in folds.split(X):
        control = train_idx[T[train_idx] == 0]
        if len(control) < 20 or len(np.unique(Y[control])) < 2:
            probability[test_idx] = float(Y[control].mean()) if len(control) else overall_untreated
            continue
        model = RandomForestClassifier(
            n_estimators=config.nuisance_trees, min_samples_leaf=config.nuisance_min_leaf,
            random_state=config.random_state, n_jobs=config.n_jobs,
        ).fit(X[control], Y[control])
        column = list(model.classes_).index(1)
        probability[test_idx] = model.predict_proba(X[test_idx])[:, column]
    return np.clip(probability, *BASELINE_CLIP)


# ----------------------------------------------------------------------------
# Results
# ----------------------------------------------------------------------------
def library_versions() -> Dict[str, str]:
    versions = {"python": platform.python_version()}
    for package in ("numpy", "pandas", "scikit-learn", "scipy", "econml", "dowhy"):
        try:
            versions[package] = importlib_metadata.version(package)
        except importlib_metadata.PackageNotFoundError:
            pass
    return versions


def to_jsonable(value):
    """Convert numpy numbers to Python numbers and NaN/infinity to None, recursively."""
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return [to_jsonable(v) for v in value.tolist()]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


@dataclass
class EffectResult:
    """Everything one analysis run produces. `customers` has one row per customer."""

    run: Dict
    average_effect: Dict
    effect_summary: Dict
    customers: pd.DataFrame
    notes: List[str]

    def to_dict(self, max_customers: int = 100, evaluation: Optional[Dict] = None) -> Dict:
        """JSON-safe dict (shape in docs/dml_workflow.md). Customers are the first `max_customers` by id."""
        sample = self.customers.sort_values(ID_COL).head(max_customers)
        rounding = {"effect": 5, "effect_low": 5, "effect_high": 5,
                    "baseline_purchase_prob": 5, "expected_list_value": 2}
        rows = []
        for record in sample.to_dict(orient="records"):
            rows.append({key: (round(record[key], rounding[key]) if key in rounding and pd.notna(record[key])
                               else record[key]) for key in record})
        out = {
            "run": self.run,
            "average_effect": self.average_effect,
            "effect_summary": self.effect_summary,
            "customers_total": int(len(self.customers)),
            "customers_returned": int(len(rows)),
            "customers": rows,
            "notes": self.notes,
        }
        if evaluation is not None:
            out["evaluation"] = evaluation
        return to_jsonable(out)


def _effect_summary(effect: np.ndarray) -> Dict:
    q = np.percentile(effect, [0, 5, 25, 50, 75, 95, 100])
    return {"min": q[0], "p05": q[1], "p25": q[2], "median": q[3], "p75": q[4], "p95": q[5], "max": q[6],
            "share_positive": float(np.mean(effect > 0)), "share_negative": float(np.mean(effect < 0))}


def estimate_effects(df: pd.DataFrame, config: Optional[EffectModelConfig] = None,
                     estimator_factory: Optional[Callable] = None,
                     data_source: str = "upload", model: Optional[EffectModel] = None) -> EffectResult:
    """Fit the effect model on `df` and score every customer in it.

    `df` must pass validate_campaign_data. Simulated truth is not an input of this function.
    """
    config = config or EffectModelConfig()
    _check_usable(df)
    model = model or fit_effect_model(df, config, estimator_factory)
    prediction = model.predict(df)
    baseline = baseline_purchase_probabilities(df, model.config)

    effect = prediction["effect"]
    customers = pd.DataFrame({
        ID_COL: df[ID_COL].to_numpy(dtype=int),
        "effect": effect,
        "effect_low": prediction["low"] if prediction["low"] is not None else np.nan,
        "effect_high": prediction["high"] if prediction["high"] is not None else np.nan,
        "baseline_purchase_prob": baseline,
        "expected_list_value": df["avg_order_value_past"].to_numpy(dtype=float),
    })

    notes = [CONFOUNDER_NOTE, UNITS_NOTE]
    if model.config.estimator == "t_learner":
        notes.append("This run used a simple baseline model (T-learner), not double machine learning.")
    notes += prediction["notes"]

    run = {
        "data_source": data_source,
        "n_customers": int(len(df)),
        "estimator": model.config.estimator,
        "estimator_label": ESTIMATOR_LABELS[model.config.estimator],
        "settings": model.config.to_dict(),
        "fit_seconds": round(model.fit_seconds, 2),
        "library_versions": library_versions(),
    }
    average_effect = {
        "ate": prediction["ate"], "ci_low": prediction["ate_low"], "ci_high": prediction["ate_high"],
        "confidence_level": model.config.confidence_level,
        "meaning": "average change in purchase probability if every customer were offered the discount",
    }
    return EffectResult(run, average_effect, _effect_summary(effect), customers, notes)


# ----------------------------------------------------------------------------
# Simulation-only evaluation: compare estimates with the known true effects
# ----------------------------------------------------------------------------
def _rank_correlation(a: np.ndarray, b: np.ndarray) -> Optional[float]:
    if np.std(a) == 0 or np.std(b) == 0:
        return None
    value = pd.Series(a).rank().corr(pd.Series(b).rank())
    return None if pd.isna(value) else float(value)


def recovery_metrics(estimated: np.ndarray, true: np.ndarray, low: Optional[np.ndarray] = None,
                     high: Optional[np.ndarray] = None, naive_difference: Optional[float] = None) -> Dict:
    """How close are the estimates to the known true effects? (Simulated data only.)"""
    estimated = np.asarray(estimated, dtype=float)
    true = np.asarray(true, dtype=float)
    n = len(true)
    error = estimated - true
    k = max(1, int(round(0.2 * n)))
    by_estimate = np.argsort(-estimated, kind="stable")
    pearson = None if np.std(estimated) == 0 or np.std(true) == 0 else float(np.corrcoef(estimated, true)[0, 1])
    metrics = {
        "n_evaluated": int(n),
        "true_ate": float(true.mean()),
        "estimated_ate": float(estimated.mean()),
        "ate_error": float(estimated.mean() - true.mean()),
        "rmse": float(np.sqrt(np.mean(error ** 2))),
        "mae": float(np.mean(np.abs(error))),
        "correlation": pearson,
        "rank_correlation": _rank_correlation(estimated, true),
        "top20_true_effect_mean": float(true[by_estimate[:k]].mean()),
        "bottom20_true_effect_mean": float(true[by_estimate[::-1][:k]].mean()),
        "all_true_effect_mean": float(true.mean()),
        "interval_coverage": None,
        "mean_interval_width": None,
        "naive_difference": None,
        "naive_error": None,
    }
    if low is not None and high is not None:
        low, high = np.asarray(low, dtype=float), np.asarray(high, dtype=float)
        metrics["interval_coverage"] = float(np.mean((true >= low) & (true <= high)))
        metrics["mean_interval_width"] = float(np.mean(high - low))
    if naive_difference is not None:
        metrics["naive_difference"] = float(naive_difference)
        metrics["naive_error"] = float(naive_difference - true.mean())
    return metrics


def evaluate_recovery(observed: pd.DataFrame, truth: pd.DataFrame,
                      config: Optional[EffectModelConfig] = None,
                      estimator_factory: Optional[Callable] = None,
                      test_fraction: float = 0.3, split_seed: int = 42) -> Dict:
    """Fit on a random training part of the data and compare estimates with the TRUE effects of the
    held-out part. Only possible for simulated data, where `truth` exists. This is a check that the
    method recovers known effects under the simulation's assumptions, not proof about real customers.
    """
    config = config or EffectModelConfig()
    if "true_effect" not in truth.columns or ID_COL not in truth.columns:
        raise ModelInputError(["The ground-truth table must have the columns customer_id and true_effect."])
    merged = observed.merge(truth[[ID_COL, "true_effect"]], on=ID_COL, how="inner", validate="one_to_one")
    if len(merged) != len(observed):
        raise ModelInputError(["Every customer in the data needs a row in the ground-truth table."])
    if not 0.05 <= test_fraction <= 0.95:
        raise ValueError("test_fraction must be between 0.05 and 0.95")

    rng = np.random.default_rng(split_seed)
    order = rng.permutation(len(merged))
    n_test = max(1, int(round(test_fraction * len(merged))))
    test = merged.iloc[order[:n_test]].reset_index(drop=True)
    train = merged.iloc[order[n_test:]].reset_index(drop=True)

    model = fit_effect_model(train.drop(columns=["true_effect"]), config, estimator_factory)
    prediction = model.predict(test.drop(columns=["true_effect"]))

    treated = test[TREATMENT_COL] == 1
    naive = None
    if treated.any() and (~treated).any():
        naive = test.loc[treated, OUTCOME_COL].mean() - test.loc[~treated, OUTCOME_COL].mean()
    metrics = recovery_metrics(prediction["effect"], test["true_effect"].to_numpy(),
                               prediction["low"], prediction["high"], naive)
    metrics.update({
        "label": "Simulation only: compares estimates with the known true effects.",
        "evaluated_on": f"held-out {int(round(test_fraction * 100))}% of customers ({len(test)} customers); "
                        f"the model was fitted on the other {len(train)}",
        "estimator": config.estimator,
        "fit_seconds": round(model.fit_seconds, 2),
        "notes": prediction["notes"],
    })
    return to_jsonable(metrics)
