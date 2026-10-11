# EconoCausal: Dynamic Pricing via Double Machine Learning

Infotact Solutions project, 10 Oct - 10 Nov 2026.
Team: Avinash (team lead, data science) and Zahra (frontend).

**Goal:** estimate how a discount changes each customer's purchase behaviour
(Double/Debiased ML via EconML), validate it (DoWhy, PSM, uplift/Qini), and
allocate a fixed promotion budget (SciPy), shown in a React + Plotly dashboard
backed by a Python REST API.

> Status: project skeleton only (Day 1). No model, data or app exists yet.
> This README is updated as features are built and verified.

## Repository layout
| Folder | Owner | Contents |
|---|---|---|
| `backend/econocausal/` | Avinash | data generator, causal, uplift, PSM, optimizer, drift |
| `backend/api/` | Avinash | REST API (FastAPI) |
| `backend/tests/` | Avinash | Python tests |
| `frontend/` | Zahra | React dashboard |
| `data/generated/` | Avinash | observed data the app sees |
| `data/evaluation/` | Avinash | true effects, kept separate from observed data |
| `docs/` | both | architecture, schema, methodology, API, testing |
| `scripts/` | both | helper scripts |

## Branches
- `main` - reviewed work only; Avinash reviews and merges.
- `avinash-dev` - backend / data science work.
- `zahra-dev` - frontend work.

## Setup
Setup and run instructions will be added here as each part becomes runnable.
Planned versions: Python 3.12 (pending compatibility test), Node.js LTS.
