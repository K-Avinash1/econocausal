# PROJECT_CONTEXT.md - EconoCausal

## Checkpoint 3 - 18 Oct 2026 (catch-up: original Day 2 + Day 3)

**Project:** EconoCausal: Dynamic Pricing via Double Machine Learning (Infotact Solutions)
**Objective:** per-customer discount effects (EconML DML), validation (DoWhy, PSM, uplift/Qini),
budget allocation (SciPy), React + Plotly dashboard over a Python REST API.
**Team:** Avinash (lead, data science, review/merge), Zahra (frontend, React beginner)
**Repository:** https://github.com/K-Avinash1/econocausal (public). Branches: main, avinash-dev, zahra-dev.

### Schedule status
- Days 2-7 of the original schedule were not done on their dates (Avinash busy with academic work).
- Mid-review is 27-29 Oct (as reported by Avinash; the Infotact dashboard date takes precedence).
- Approved recovery: two original days per calendar day, everything else unchanged.

| Calendar date | Original days covered |
|---|---|
| 18 Oct | Day 2 + Day 3 |
| 19 Oct | Day 4 + Day 5 |
| 20 Oct | Day 6 + Day 7 |
| 21 Oct | Day 8 + Day 9 |
| 22 Oct | Day 10 + Day 11 |
| 23 Oct | Day 12 + Day 13 |
| 24 Oct | Day 14 + Day 15 |
| 25 Oct | Day 16 (PSM) + buffer |
| 26 Oct | Day 17 (mid-review status, rehearsal) + buffer |
| 27-29 Oct | Mid-review (Day 18 equivalent) |
| 29 Oct onward | Phase 3 and Phase 4 exactly as originally scheduled (Day 19 on 29 Oct) |

If a day slips, 25-26 Oct are the buffer. Any scope cut needs Avinash's approval first.

### Completed and verified
- Day 1 (see Checkpoint 2): repo, branches, tools, dashboard connection (dashboard items reported by Avinash).
- EconML/DoWhy environment check passed on Avinash's PC (Python 3.11.9): numpy 2.4.6, pandas 3.0.6,
  scikit-learn 1.9.1, scipy 1.15.3, econml 0.17.0, dowhy 0.14, plotly 7.1.0, fastapi 0.143.0,
  uvicorn 0.54.0, pytest 9.1.1. EconML LinearDML smoke test ran.
- Commits on avinash-dev: e32e384, cf8b3a5. Commit on zahra-dev: c88197b. Nothing merged into main yet.

### Implemented, awaiting verification on Avinash's machine
Files (delivered 18 Oct, not yet committed):
- backend/econocausal/schema.py, data_generation.py, validation.py, eda.py
- backend/tests/test_generator.py, test_validation.py, test_eda.py; pytest.ini
- scripts/generate_data.py, run_eda.py, make_sample_files.py, check_environment.py
- docs/dataset_schema.md, docs/methodology.md; README.md; backend/requirements.txt (pinned)
Claude's own run: the 32 test functions were executed directly in Claude's workspace (NumPy 2.5.3,
pandas 3.0.5, Python 3.13) and passed. pytest was not available there, so `pytest` has NOT been run.
Generated CSVs, docs/eda_report.md and docs/validation_messages.md must be produced on Avinash's machine.

### Decisions
- Binary treatment, fixed 15% discount; outcome `purchased`; 20,000 customers; seed 42.
- Optimizer objective = incremental NET revenue (discount already deducted), not profit; no profit
  claim without a margin assumption (docs/methodology.md, Decision record 2).
- Schema unchanged (13 observed columns). Evaluation file adds true_propensity and
  expected_list_value, explained in docs/dataset_schema.md.
- Two upload rules looser than first proposed: past_purchases_12m >= 0 and avg_order_value_past >= 0.

### Known issues / limitations
- Simulation only; effect recovery on synthetic data is not evidence about real customers.
- Which timezone the dashboard uses for commit days is not confirmed; commit in daytime/evening.
- Node.js not installed on Avinash's machine (needed before frontend integration).
- How the dashboard defines the 14-day mid-review commit window is not confirmed.

### Next step - Avinash
- Unzip update into E:\econocausal, run pytest, generate data, run EDA and samples, commit, merge to main.

### Next step - Zahra
- Day 2 doc (docs/upload_requirements.md); after Avinash merges to main, pull main and do the Day 3 task.

### Questions requiring approval
- None open.
