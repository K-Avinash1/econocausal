# API contract (v0.1, Day 4-5)

Code: `backend/api/main.py`, `backend/econocausal/upload_service.py`.
Run from the project root: `python -m uvicorn --app-dir backend api.main:app --port 8000`

## GET /health
Answer: `{"status": "ok", "service": "econocausal", "version": "0.1.0"}`

## POST /validate
Request: the CSV file as the raw body, header `Content-Type: text/csv`.
The server always answers HTTP 200 with a report (a bad file is a normal answer, not a server error).

```json
{
  "ok": false,
  "errors":   [{"code": "invalid_category", "column": "region", "message": "Column 'region' contains values that are not allowed (Central). Allowed: North, South, East, West."}],
  "warnings": [],
  "summary":  {"n_rows": 1000, "n_treated": 497, "n_untreated": 503, "treated_share": 0.497, "purchase_rate": 0.31},
  "columns":  ["customer_id", "age", "..."],
  "preview":  [{"customer_id": 1, "age": 44, "...": "..."}]
}
```
- `ok` is true when `errors` is empty. Warnings do not block.
- `summary` only has the keys that could be computed; for a file that failed early it can be `{}`.
- `preview` holds at most 10 rows and is `[]` when no rows could be read.
- Page-level failures (empty, over 10 MB, not text, not readable as CSV) use the same shape with one error and codes `empty_file`, `file_too_large`, `unreadable_file`.
- CORS allows the React dev server at `http://localhost:5173` and `http://127.0.0.1:5173`.

## Quick check without the frontend (PowerShell, backend running)
```
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod -Uri http://127.0.0.1:8000/validate -Method Post -ContentType "text/csv" -InFile data\samples\invalid_bad_region.csv | ConvertTo-Json -Depth 5
```
