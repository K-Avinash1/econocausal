# Testing: instructions and ACTUAL status

Only results that someone has run and seen are listed as passed. A test file existing is not a pass.

## How to run
```
pytest                                   # backend unit tests (project root, venv active)
python scripts/smoke_test_api.py         # needs the backend running; checks /health, /validate, CORS
```
Backend start command: `python -m uvicorn --app-dir backend api.main:app --port 8000`

## Status
| Check | Where run | Date | Result |
|---|---|---|---|
| `pytest`: 46 tests (causal graph 7, EDA 5, generator 11, upload service 7, validation 16) | Avinash's PC, Python 3.11.9, pytest 9.1.1 | 20 Oct 2026 and 21 Oct 2026 | 46 passed both times (4.06 s on 20 Oct, 4.29 s on 21 Oct; output pasted by Avinash) |
| `scripts/check_causal_graph.py` (DoWhy identification) | Avinash's PC | 20 Oct 2026 | ran; DoWhy found a backdoor estimand adjusting for all 8 attributes; saved in `docs/dowhy_identification.txt` |
| `GET /health` | Avinash's PC | 20 Oct 2026 | 200 OK (server log) |
| `POST /validate` with `invalid_bad_region.csv` and `sample_valid.csv` | Avinash's PC (PowerShell) | 20 Oct 2026 | responses matched the contract |
| Upload page with `sample_valid.csv`, `invalid_bad_region.csv`, `invalid_empty.csv` against the real backend | Zahra's PC (screenshots seen) | 21 Oct 2026 | messages matched `docs/upload_feedback.md` |
| `scripts/smoke_test_api.py` | 20 passed, 0 failed,| Avinash’s PC,| 21 Oct 2026 |
| Data reproducibility: `generate_data.py` run twice, SHA-256 of `data/generated/campaign_data.csv` | Avinash's PC | 21 Oct 2026 | both hashes identical: 057B594515CF30F4EA92B95D1364CADCAFAAF244608170FD9E098DCE4DB56937 (reported by Avinash) |
| Clean-start test from a fresh clone | NOT YET RUN | | Day 7 task for Zahra |
| Automated frontend tests | none exist yet | | |
| DML model, refutation, uplift, PSM, optimizer | not built yet | | |

## Known gaps
- The other 9 sample files through the page were checked only in Claude's workspace (headless browser, stand-in server), not by Zahra.
