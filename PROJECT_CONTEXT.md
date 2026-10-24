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

---

## Checkpoint 4 - 20 October 2026 (catch-up: original Days 2-3 closed, Days 4-5 delivered)

(This checkpoint supersedes the "awaiting verification / not yet committed" status in Checkpoint 3.)

### Schedule status
- The 19 Oct package (Days 4+5) was delivered on 19 Oct evening but not worked on that day, so work starts on 20 Oct: we are one day behind the catch-up table above.
- Per the standing rule, the slip is absorbed by the buffer on 25-26 Oct. Revised plan (needs Avinash's OK):
  20 Oct Day 4+5 (Day 6 is largely covered because /health and /validate exist), 21 Oct Day 7+8, 22 Oct Day 9+10,
  23 Oct Day 11+12, 24 Oct Day 13+14, 25 Oct Day 15+16, 26 Oct Day 17 (status, rehearsal). Mid-review 27-29 Oct unchanged. No buffer is left after this.

### Verified (evidence seen in pasted output / screenshots)
- Avinash's machine: `pytest` 32 passed; data, EDA and sample files generated; commits a131042 and eff5eb6 pushed to avinash-dev.
- PR #1 (avinash-dev -> main) merged ("Merge pull request #1 from K-Avinash1/avinash-dev", main at bf92890).
- Zahra: `docs/upload_feedback.md` committed (ca727a8) and pushed. PR #2 "Day2&Day3" (4 commits, zahra-dev -> main; files frontend_setup.md, upload_feedback.md, upload_requirements.md) is merged. It was merged from Zahra's own account, not by Avinash.
- Original Days 2 and 3 are complete for both members.

### Implemented and tested only in Claude's workspace (NOT yet run on the team's machines)
- `backend/econocausal/causal_graph.py`, `docs/causal_graph.md` (draft assumptions for Avinash's review)
- `backend/econocausal/upload_service.py`, `backend/api/main.py` (/health, /validate), `docs/api_contract.md`
- Tests: with pytest unavailable, the test functions were called directly: causal graph 7, upload service 7, plus the earlier 32 (46 in total) all passed on Python 3.13. One causal-graph test needs pytest's `monkeypatch`; it was run with a hand-made stand-in. `pytest` itself has NOT been run on these.
- Frontend: Zahra's paste-ready code (ZAHRA_DAY4_5.md) was bundled with esbuild (React 19.2.8) and opened in headless Chromium against a Starlette stand-in server that calls the real `validate_csv_bytes` (FastAPI is not installable in Claude's workspace). All 12 sample files, a non-CSV file and the "server not running" case showed the messages in `docs/upload_feedback.md`; no JavaScript errors. This found and fixed one bug (page scrolled sideways on narrow screens).
- NOT verified anywhere: `backend/api/main.py` under real FastAPI/uvicorn, `scripts/check_causal_graph.py` (needs DoWhy), a Vite install on Zahra's machine.

### Decisions
- /validate takes the raw CSV body (no multipart dependency) and pulls part of Day 6 forward so the upload page shows the validator's real messages.
- Upload size limit 10 MB: proposed, awaiting Avinash's confirmation.
- Graph: all 8 attributes are confounders and effect modifiers; `order_value`, `discount_cost`, `customer_id` excluded.

### Known issues / limitations
- Dashboard timezone for commit days and the 14-day mid-review window: not confirmed.
- Node.js not installed on Avinash's machine (not needed until he runs the frontend).
- Main has no frontend app yet; the React app is created on zahra-dev.
- The "Run analysis" button only shows a "not connected yet" notice; analysis is built in later phases.

### Next step - Avinash
- Sync avinash-dev with main, apply the update, run pytest, run `scripts/check_causal_graph.py`, start the API, check /health and /validate, review docs/causal_graph.md, commit, push, open PR, merge, tell Zahra.

### Next step - Zahra
- Day 4: create the React app and layout, commit. Day 5: upload page, commit, then test against the real backend once Avinash has merged, open PR "Day4&Day5" (Avinash merges).

### Questions requiring approval
- Revised schedule above (uses the buffer). 10 MB upload limit. Attribute-to-attribute edges in the causal graph.

---

## Checkpoint 5 - 21 October 2026 (catch-up: Day 4+5 delivered, Day 6+7 package prepared)

### Verified (evidence seen in pasted output / screenshots)
- Avinash, 20 Oct: `pytest` 46 passed in 4.06 s (Python 3.11.9); `scripts/check_causal_graph.py` ran and DoWhy produced a backdoor estimand adjusting for all 8 attributes; `/health` returned 200; `/validate` responses for `invalid_bad_region.csv` and `sample_valid.csv` matched the contract. Commit 733e4f8; PR #3 merged into main (f739579).
- Avinash approved on 20 Oct: the attribute-to-attribute edges in `docs/causal_graph.md` and the 10 MB upload limit. (To be recorded in the repo files with his next commit.)
- Zahra, 21 Oct: React app (Vite) created in `frontend/`; upload page works against the real backend (screenshots for `sample_valid.csv`, `invalid_bad_region.csv`, `invalid_empty.csv`). Commits edb666c and 3afd224 on zahra-dev. Her pull request into main had NOT been opened when last checked (GitHub showed 0 open PRs); GitHub shows 4 closed PRs, of which only 3 are known.

### Prepared 21 Oct, not yet run on the team's machines
- `docs/model_interface.md` (draft for Avinash), `docs/testing.md`, `README.md` (run instructions), `scripts/smoke_test_api.py` (20 checks; run only in Claude's workspace against a stand-in server and against a deliberately broken one, where it correctly failed).

### Schedule status (revised plan, uses the 25-26 Oct buffer)
- Days 4+5 close when Zahra's PR is merged. Day 6 is mostly done (`/health`, `/validate`, frontend connection); remaining Day 6 item is Avinash's interface definition (`docs/model_interface.md`). Day 7 = clean-start test and data/causal validation. Day 8 (DML workflow) and Day 9 (first EconML model) follow.
- Mid-review 27-29 Oct unchanged (the Infotact dashboard date takes precedence).

### Known issues / limitations
- Dashboard timezone for commit days and the 14-day mid-review window: still not confirmed.
- Zahra's Python is 3.13.0; the full pinned requirements are tested only with Python 3.11.9.
- Zahra has no separate "Day 4" commit message (layout and upload page are in her two Day 5 commits).

### Next
- Avinash: review and merge Zahra's PR; run the smoke test; reproducibility check; approve or edit `docs/model_interface.md`.
- Zahra: clean-start test in a fresh clone, record it in `docs/clean_start_test.md`.

## Checkpoint 6 (23 Oct 2026, Day 8+9 delivered by Claude, NOT yet run on Avinash's PC)
- Added `backend/econocausal/effect_model.py`, `scripts/run_first_model.py`, tests
  `test_effect_model.py` (15, no EconML needed) and `test_effect_model_econml.py` (skipped without EconML),
  `docs/dml_workflow.md`, decision record 3 in `docs/methodology.md`.
- Verified in Claude's sandbox only: T-learner path end to end (no EconML there), 15 tests via a stand-in runner.
- NOT verified: every EconML call. Day 9 is done only when Avinash pastes the `--quick` run output.
- `data/demo/analysis_demo.json` is a development fixture from the T-learner, not EconML. Replace it
  with the real export (`--export-demo causal_forest`).
