# EconoCausal: Dynamic Pricing via Double Machine Learning

Infotact Solutions project, 10 Oct - 10 Nov 2026.
Team: Avinash (team lead, data science) and Zahra (frontend).

**Goal:** estimate how a discount changes each customer's purchase behaviour (Double/Debiased ML
via EconML), validate it (DoWhy, PSM, uplift/Qini), and allocate a fixed promotion budget (SciPy),
shown in a React + Plotly dashboard backed by a Python REST API.

> Status (18 Oct 2026): synthetic data generator, dataset validation and EDA code added.
> No causal model, API or dashboard exists yet. See `PROJECT_CONTEXT.md` for verified status.

## Repository layout
| Folder | Owner | Contents |
|---|---|---|
| `backend/econocausal/` | Avinash | schema, data generator, validation, EDA (later: causal, uplift, PSM, optimizer, drift) |
| `backend/api/` | Avinash | REST API (FastAPI), added later |
| `backend/tests/` | Avinash | Python tests |
| `frontend/` | Zahra | React dashboard, added later |
| `data/generated/` | Avinash | observed data the app sees (CSV is git-ignored; regenerate) |
| `data/evaluation/` | Avinash | true effects, kept separate from observed data (git-ignored) |
| `data/samples/` | both | small valid and invalid CSV files for testing uploads |
| `docs/` | both | dataset schema, methodology, EDA report, validation messages |
| `scripts/` | both | generate data, run EDA, make sample files, check environment |

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

## Generate data, run EDA, run tests
```
python scripts/generate_data.py      # data/generated/campaign_data.csv and data/evaluation/ground_truth.csv
python scripts/run_eda.py            # docs/eda_report.md
python scripts/make_sample_files.py  # data/samples/*.csv and docs/validation_messages.md
pytest                               # backend/tests
```
Test results are recorded in `docs/testing.md` only after they have been run.

## Frontend setup
To be added when the React app is created.

## Key documents
- `docs/dataset_schema.md` - columns, validation rules and the data-generation equations
- `docs/methodology.md` - treatment/outcome and optimizer-objective decisions
- `WORK_DISTRIBUTION.md` - who owns what
