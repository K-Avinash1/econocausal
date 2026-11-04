"""Analysis workflow behind the API (Day 11): upload -> validate -> estimate -> store -> page/refute.

The API (backend/api/main.py) is a thin wrapper around these functions, so everything can be
tested without starting a server.

Every function returns a plain dict. Expected problems (bad file, unknown run, missing data) come
back as {"ok": False, "errors": [{"code", "column", "message"}]}, the same shape as /validate.
Results of a run are kept in memory only (last MAX_RUNS runs); restarting the server clears them.
"""
import io
import threading
import uuid
from collections import OrderedDict
from pathlib import Path
from typing import Callable, Dict, Optional

import numpy as np
import pandas as pd

from .effect_model import (
    ESTIMATORS, EffectModelConfig, EffectResult, ModelDependencyError, ModelInputError,
    customer_rows, estimate_effects, evaluate_recovery, to_jsonable,
)
from .refutation import run_refutations
from .upload_service import MAX_UPLOAD_BYTES, validate_csv_bytes

MAX_RUNS = 5
MAX_ANALYSIS_ROWS = 50_000      # larger files are refused with a clear message (run time)
FIRST_PAGE = 100
MAX_PAGE = 500
HIST_BINS = 20

ROOT = Path(__file__).resolve().parents[2]
DEMO_DATA = ROOT / "data" / "generated" / "campaign_data.csv"
DEMO_TRUTH = ROOT / "data" / "evaluation" / "ground_truth.csv"


def failure(code: str, message: str, column: Optional[str] = None) -> Dict:
    return {"ok": False, "errors": [{"code": code, "column": column, "message": message}],
            "warnings": [], "summary": {}, "columns": [], "preview": []}


class RunStore:
    """Thread-safe in-memory store of the most recent analysis runs."""

    def __init__(self, max_runs: int = MAX_RUNS):
        self.max_runs = max_runs
        self._runs: "OrderedDict[str, Dict]" = OrderedDict()
        self._lock = threading.Lock()

    def add(self, record: Dict) -> str:
        run_id = uuid.uuid4().hex[:12]
        with self._lock:
            self._runs[run_id] = record
            while len(self._runs) > self.max_runs:
                self._runs.popitem(last=False)
        return run_id

    def get(self, run_id: str) -> Optional[Dict]:
        with self._lock:
            return self._runs.get(run_id)

    def __len__(self) -> int:
        with self._lock:
            return len(self._runs)


STORE = RunStore()


def _config(estimator: str, quick: bool) -> EffectModelConfig:
    return EffectModelConfig.quick(estimator) if quick else EffectModelConfig(estimator=estimator)


def _histogram(effect: np.ndarray) -> Dict:
    counts, edges = np.histogram(effect, bins=HIST_BINS)
    return {"bin_edges": edges, "counts": counts,
            "note": "Number of customers per range of estimated effect (probability points)."}


def _package(run_id: str, result: EffectResult, evaluation: Optional[Dict], warnings: list) -> Dict:
    out = result.to_dict(max_customers=FIRST_PAGE, evaluation=evaluation)
    out.update({"ok": True, "run_id": run_id, "warnings": warnings,
                "chart_data": {"effect_histogram": to_jsonable(_histogram(result.customers["effect"].to_numpy()))}})
    return out


def _read_csv(raw: bytes) -> pd.DataFrame:
    return pd.read_csv(io.StringIO(raw.decode("utf-8-sig")))


def analyze_csv_bytes(raw: bytes, estimator: str = "causal_forest", quick: bool = True,
                      store: RunStore = STORE, max_rows: int = MAX_ANALYSIS_ROWS,
                      estimator_factory: Optional[Callable] = None) -> Dict:
    """Validate an uploaded CSV, estimate effects, store the run, return summary + first customers.

    No ground truth is ever used or returned for uploaded data.
    """
    if estimator not in ESTIMATORS:
        return failure("invalid_estimator", f"Unknown estimator '{estimator}'. Choose one of: {', '.join(ESTIMATORS)}.")
    report = validate_csv_bytes(raw)
    if not report["ok"]:
        return report
    df = _read_csv(raw)
    if len(df) > max_rows:
        return failure("too_many_rows",
                       f"This file has {len(df):,} rows. The analysis accepts up to {max_rows:,} rows; please upload a smaller file.")
    config = _config(estimator, quick)
    try:
        result = estimate_effects(df, config, estimator_factory, data_source="upload")
    except ModelInputError as exc:
        return failure("model_input", " ".join(exc.messages))
    except ModelDependencyError as exc:
        return failure("model_unavailable", str(exc))
    except Exception as exc:  # never leak a traceback to the page
        return failure("analysis_failed", f"The analysis could not be completed ({type(exc).__name__}). "
                                          "Check the server terminal for details.")
    run_id = store.add({"df": df, "result": result, "config": config, "refutation": None})
    return _package(run_id, result, None, report["warnings"])


def demo_run(estimator: str = "causal_forest", quick: bool = True, store: RunStore = STORE,
             data_path: Path = DEMO_DATA, truth_path: Path = DEMO_TRUTH,
             estimator_factory: Optional[Callable] = None) -> Dict:
    """Run on the generated simulation data. Adds a clearly labelled evaluation block (simulation only)."""
    if estimator not in ESTIMATORS:
        return failure("invalid_estimator", f"Unknown estimator '{estimator}'. Choose one of: {', '.join(ESTIMATORS)}.")
    if not Path(data_path).exists() or not Path(truth_path).exists():
        return failure("demo_data_missing", "The demo data has not been generated. Run: python scripts/generate_data.py")
    df = pd.read_csv(data_path)
    truth = pd.read_csv(truth_path)
    config = _config(estimator, quick)
    try:
        result = estimate_effects(df, config, estimator_factory, data_source="synthetic")
        evaluation = evaluate_recovery(df, truth, config, estimator_factory)
    except ModelDependencyError as exc:
        return failure("model_unavailable", str(exc))
    except Exception as exc:
        return failure("analysis_failed", f"The demo analysis could not be completed ({type(exc).__name__}). "
                                          "Check the server terminal for details.")
    run_id = store.add({"df": df, "result": result, "config": config, "refutation": None})
    return _package(run_id, result, evaluation, [])


def get_customers(run_id: str, offset: int = 0, limit: int = FIRST_PAGE, store: RunStore = STORE) -> Dict:
    record = store.get(run_id)
    if record is None:
        return failure("run_not_found", "This analysis is no longer available. Run the analysis again.")
    customers = record["result"].customers.sort_values("customer_id").reset_index(drop=True)
    total = len(customers)
    offset = max(0, int(offset))
    limit = min(max(1, int(limit)), MAX_PAGE)
    page = customers.iloc[offset:offset + limit]
    return to_jsonable({"ok": True, "run_id": run_id, "total": total, "offset": offset,
                        "limit": limit, "customers": customer_rows(page)})


def refute_run(run_id: str, n_sims: int = 3, store: RunStore = STORE,
               estimator_factory: Optional[Callable] = None) -> Dict:
    """Run the refutation tests on a stored run (same data, estimator and settings). Cached per run."""
    record = store.get(run_id)
    if record is None:
        return failure("run_not_found", "This analysis is no longer available. Run the analysis again.")
    if not 1 <= int(n_sims) <= 10:
        return failure("invalid_n_sims", "n_sims must be between 1 and 10.")
    cached = record.get("refutation")
    if cached is not None and cached["settings"]["n_sims"] == int(n_sims):
        return {"ok": True, "run_id": run_id, "refutation": cached, "cached": True}
    try:
        refutation = run_refutations(record["df"], record["config"], n_sims=int(n_sims),
                                     estimator_factory=estimator_factory)
    except Exception as exc:
        return failure("refutation_failed", f"The refutation tests could not be completed ({type(exc).__name__}). "
                                            "Check the server terminal for details.")
    record["refutation"] = refutation
    return {"ok": True, "run_id": run_id, "refutation": refutation, "cached": False}
