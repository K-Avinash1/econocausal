"""EconoCausal REST API (Day 11: /health, /validate, /analyze, /demo, /results, /refute).

Run from the project root:
    python -m uvicorn --app-dir backend api.main:app --port 8000
Then open http://127.0.0.1:8000/health

Contract: docs/api_contract.md. Expected failures (bad file, unknown run) are HTTP 200 with
{"ok": false, "errors": [...]}, like /validate.

The analysis code needs scikit-learn (and EconML for the DML estimators). It is imported only when an
analysis endpoint is called, so /health and /validate keep working in a lighter environment.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from econocausal.upload_service import validate_csv_bytes

API_VERSION = "0.2.0"

app = FastAPI(title="EconoCausal API", version=API_VERSION)

# The React dev server (Vite) runs on port 5173 and must be allowed to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_MISSING_LIBS = {
    "ok": False,
    "errors": [{
        "code": "model_unavailable",
        "column": None,
        "message": "The analysis libraries are not installed in this Python environment. "
                   "Run: pip install -r backend/requirements.txt "
                   "(for the simple baseline model only: pip install scikit-learn scipy).",
    }],
    "warnings": [], "summary": {}, "columns": [], "preview": [],
}


def _service():
    """Return (analysis_service, None), or (None, error answer) if its libraries are missing."""
    try:
        from econocausal import analysis_service
        return analysis_service, None
    except ImportError:
        return None, _MISSING_LIBS


@app.get("/health")
def health():
    return {"status": "ok", "service": "econocausal", "version": API_VERSION}


@app.post("/validate")
async def validate(request: Request):
    """Body = the raw CSV file. Always answers 200 with the validation report."""
    raw = await request.body()
    return validate_csv_bytes(raw)


@app.post("/analyze")
async def analyze(request: Request, estimator: str = "causal_forest", quick: bool = True):
    """Body = the raw CSV file. Validates, estimates effects, returns summary + first 100 customers + run_id."""
    raw = await request.body()
    service, problem = _service()
    if problem:
        return problem
    return await run_in_threadpool(service.analyze_csv_bytes, raw, estimator, quick)


@app.get("/demo")
async def demo(estimator: str = "causal_forest", quick: bool = True):
    """Run on the generated simulation data (includes a labelled simulation-only evaluation)."""
    service, problem = _service()
    if problem:
        return problem
    return await run_in_threadpool(service.demo_run, estimator, quick)


@app.get("/results/{run_id}/customers")
def customers(run_id: str, offset: int = 0, limit: int = 100):
    service, problem = _service()
    if problem:
        return problem
    return service.get_customers(run_id, offset, limit)


@app.post("/refute/{run_id}")
async def refute(run_id: str, n_sims: int = 3):
    """Run the refutation tests on a stored run. Can take about a minute."""
    service, problem = _service()
    if problem:
        return problem
    return await run_in_threadpool(service.refute_run, run_id, n_sims)
