"""EconoCausal REST API (Day 4-5 starter: /health and /validate).

Run from the project root:
    python -m uvicorn --app-dir backend api.main:app --port 8000
Then open http://127.0.0.1:8000/health
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from econocausal.upload_service import validate_csv_bytes

API_VERSION = "0.1.0"

app = FastAPI(title="EconoCausal API", version=API_VERSION)

# The React dev server (Vite) runs on port 5173 and must be allowed to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "econocausal", "version": API_VERSION}


@app.post("/validate")
async def validate(request: Request):
    """Body = the raw CSV file. Always answers 200 with the validation report."""
    raw = await request.body()
    return validate_csv_bytes(raw)
