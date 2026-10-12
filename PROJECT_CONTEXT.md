# PROJECT_CONTEXT.md - EconoCausal

## Checkpoint 2 - end of Day 1 (11-12 Oct 2026, Phase 1: Foundations)

**Project:** EconoCausal: Dynamic Pricing via Double Machine Learning (Infotact Solutions)
**Objective:** per-customer discount effects (EconML DML), validation (DoWhy, PSM, uplift/Qini),
budget allocation (SciPy), React + Plotly dashboard over a Python REST API.
**Team:** Avinash (lead, data science, review/merge), Zahra (frontend, React beginner)
**Schedule:** 11 Oct - 10 Nov 2026. Official review dates to be confirmed on the Infotact dashboard.

### Completed work (verified from terminal output)
- Project started from scratch; no earlier files, code or repository existed.
- Repository: https://github.com/K-Avinash1/econocausal (public).
- Avinash's local copy: E:\econocausal. Zahra's local copy: C:\Projects\econocausal.
- Commits (verified with git log):
  - c66da8a  Avinash K  2026-10-11 18:25 +0530  "Initial project skeleton" (on main; 14 files)
  - e32e384  Avinash K  "Day 1: record verified repository and environment status" (on avinash-dev, pushed)
  - c88197b  zfathima353-byte  2026-10-11 23:57 +0400  "Day 1: document frontend environment and setup" (on zahra-dev, pushed)
- Branches main, avinash-dev, zahra-dev exist locally and on origin. Nothing merged into main yet
  beyond the initial commit.

### Environments (verified)
- Avinash (Windows): Git 2.53.0, VS Code 1.141.0, Python 3.11.9. Node.js not installed yet.
- Zahra (Windows): Git 2.56.0, Node v24.21.0, npm 11.19.0. PowerShell script policy set to
  RemoteSigned for the current user so npm runs.
- Zahra's computer clock is UTC+4; Avinash's is UTC+5:30. Commit dates near midnight can
  fall on different days depending on timezone.

### Decisions and assumptions
- Repository public. Branches: main (reviewed work), avinash-dev, zahra-dev.
- Python 3.11.9 proposed as project version (instead of 3.12); compatibility with
  EconML/DoWhy to be tested on Day 2, not yet confirmed.
- Dataset: synthetic first, fixed seed, true effects in data/evaluation/, separate from observed data.
- Frontend app is created when frontend work starts (Day 4 layout); no practice starter.

### Tests
- None run yet.

### Known issues / limitations
- Node.js not yet installed on Avinash's machine (needed later for integration testing).
- Not yet verified: Infotact dashboard connection and branch detection for both branches.
- Not yet verified: that Zahra's Git email is linked to her GitHub account (commit avatar).
- Which timezone the dashboard uses to assign commits to days is unknown.

### Remaining tasks
- Connect avinash-dev and zahra-dev to the Infotact dashboard and confirm both are detected.
- Day 2: dataset schema and reproducible synthetic data generator.

### Next step - Avinash
- Confirm the dashboard shows both branches; confirm Python 3.11.9 as the project version;
  finalise the dataset schema decisions for Day 2.

### Next step - Zahra
- Connect zahra-dev to the dashboard; read the Day 2 task block when sent.

### Questions requiring approval
- Confirm Python 3.11.9 as the project version.