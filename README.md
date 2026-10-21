# EconoCausal: Dynamic Pricing via Double Machine Learning

Infotact Solutions project, 10 Oct - 10 Nov 2026.
Team: Avinash (team lead, data science) and Zahra (frontend).

**Goal:** estimate how a discount changes each customer's purchase behaviour (Double/Debiased ML
via EconML), validate it (DoWhy, PSM, uplift/Qini), and allocate a fixed promotion budget (SciPy),
shown in a React + Plotly dashboard backed by a Python REST API.

> Status (21 Oct 2026): synthetic data generator, dataset validation, EDA, the DoWhy causal graph,
> an API with `/health` and `/validate`, and a React dashboard layout with a working CSV upload page exist.
> No DML model, results page, optimizer or charts yet. See `PROJECT_CONTEXT.md` for verified status
> and `docs/testing.md` for what has actually been run.

## Repository layout
| Folder | Owner | Contents |
|---|---|---|
| `backend/econocausal/` | Avinash | schema, data generator, validation, EDA, causal graph, upload service (later: DML, uplift, PSM, optimizer, drift) |
| `backend/api/` | Avinash | REST API (FastAPI): `GET /health`, `POST /validate` (more endpoints later) |
| `backend/tests/` | Avinash | Python tests |
| `frontend/` | Zahra | React dashboard (Vite): layout and CSV upload page |
| `data/generated/` | Avinash | observed data the app sees (CSV is git-ignored; regenerate) |
| `data/evaluation/` | Avinash | true effects, kept separate from observed data (git-ignored) |
| `data/samples/` | both | small valid and invalid CSV files for testing uploads |
| `docs/` | both | schema, methodology, causal graph, API contract, model interface, testing, EDA report |
| `scripts/` | both | generate data, run EDA, make sample files, check environment, causal check, API smoke test |

## Branches
- `main` - reviewed work only; Avinash reviews and merges.
- `avinash-dev` - backend / data science work.
- `zahra-dev` - frontend work.

## Backend setup (Windows PowerShell, Python 3.11.9)
Run from the project root, for example `E:\econocausal`:
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
python scripts/check_environment.py
```
If activation says "running scripts is disabled", run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and retry.

### Light install (frontend work only, no model libraries)
Enough to run the API for the upload page. It was used on Zahra's PC (Python 3.13.0):
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install numpy pandas fastapi uvicorn
```
The full pinned list above is for the model work and is tested only with Python 3.11.9.

## Run the backend API
Project root, venv active:
```
python -m uvicorn --app-dir backend api.main:app --port 8000
```
Open http://127.0.0.1:8000/health. Expected: `{"status":"ok","service":"econocausal","version":"0.1.0"}`.
(http://127.0.0.1:8000/ alone shows "Not Found"; that is normal.) Stop with `Ctrl+C`.
Endpoint details: `docs/api_contract.md`.

## Run the frontend
Needs Node.js 20 or newer (verified on v24.21.0 with npm 11.19.0). In a SECOND terminal:
```
cd frontend
npm install        # first time only
npm run dev
```
Open http://localhost:5173. The address must be exactly this one, because the API only allows that origin.
Choose a file from `data/samples/` to try the upload page. The backend must be running.

## Generate data, run EDA, run tests
```
python scripts/generate_data.py      # data/generated/campaign_data.csv and data/evaluation/ground_truth.csv
python scripts/run_eda.py            # docs/eda_report.md
python scripts/make_sample_files.py  # data/samples/*.csv and docs/validation_messages.md
python scripts/check_causal_graph.py # needs DoWhy; writes docs/dowhy_identification.txt
pytest                               # backend/tests
```
With the backend running, in another terminal: `python scripts/smoke_test_api.py`.
Actual results are recorded in `docs/testing.md` only after they have been run.

## Common problems
| Symptom | Fix |
|---|---|
| Page says "We could not reach the analysis server" | start the backend; check the address is `http://127.0.0.1:8000` |
| Same message, backend is running | the page must be on `http://localhost:5173`; if npm printed 5174, close old terminals and start again |
| `pytest is not recognized` or `No module named ...` | activate `.venv` first |
| `running scripts is disabled` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Git warns "LF will be replaced by CRLF" | harmless |

## Key documents
- `docs/dataset_schema.md` - columns, validation rules and the data-generation equations
- `docs/methodology.md` - treatment/outcome and optimizer-objective decisions
- `docs/causal_graph.md` - causal graph, variable roles and assumptions
- `docs/api_contract.md` - endpoints and response shapes
- `docs/model_interface.md` - model inputs and outputs (draft)
- `docs/testing.md` - how to test and the actual test status
- `WORK_DISTRIBUTION.md` - who owns what
