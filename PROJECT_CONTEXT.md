# PROJECT_CONTEXT.md - EconoCausal

## Checkpoint 1 - 11 Oct 2026 (Day 1, Phase 1: Foundations)

**Project:** EconoCausal: Dynamic Pricing via Double Machine Learning (Infotact Solutions)
**Objective:** per-customer discount effects (EconML DML), validation (DoWhy, PSM, uplift/Qini),
budget allocation (SciPy), React + Plotly dashboard over a Python REST API.
**Team:** Avinash (lead, data science, review/merge), Zahra (frontend, React beginner)
**Schedule:** 11 Oct - 10 Nov 2026. Official review dates to be confirmed on the Infotact dashboard.

### Completed work (verified from terminal output)
- Project started from scratch; no earlier files, code or repository existed.
- Local repository created at E:\econocausal on Avinash's machine.
- Initial commit c66da8a "Initial project skeleton" (14 files) pushed to GitHub.
- Branches main, avinash-dev and zahra-dev exist locally and on origin.
- Repository: https://github.com/K-Avinash1/econocausal (public).

### Files
README.md, PROJECT_CONTEXT.md, WORK_DISTRIBUTION.md, .gitignore,
backend/ (econocausal/, api/, tests/, requirements.txt), frontend/, data/generated/,
data/evaluation/, docs/, scripts/ (README placeholders only; no code yet).

### Decisions and assumptions
- Repository public. Branches: main (reviewed work), avinash-dev, zahra-dev.
- Avinash's tools: Git 2.53.0, VS Code 1.141.0, Python 3.11.9. Node.js not installed yet.
- Python 3.11.9 proposed as project version (instead of 3.12); compatibility with
  EconML/DoWhy to be tested on Day 2, not yet confirmed.
- Dataset: synthetic first, fixed seed, true effects stored separately in data/evaluation/.
- Frontend app is created when frontend work starts (Day 4 layout); no practice starter.

### Tests
- None run yet.

### Known issues / limitations
- Node.js missing on Avinash's machine (needed later for integration testing).
- Zahra's setup (GitHub invite, Node, clone) not yet verified.
- Infotact dashboard connection and branch detection not yet verified.

### Git status
- Verified: HEAD on avinash-dev at c66da8a; all three branches at c66da8a; remote origin set.
- Nothing merged yet beyond the initial commit on main.

### Remaining tasks
- Zahra: accept invite, install Node LTS, clone repo, switch to zahra-dev, record versions.
- Avinash: connect repo/branch to Infotact dashboard and check both branches are detected.
- Day 2: dataset schema and reproducible synthetic data generator.

### Next step - Avinash
- Commit this file on avinash-dev, then connect to the dashboard and report what it shows.
- Install Node.js LTS before Day 4.

### Next step - Zahra
- Complete Day 1 setup (see Remaining tasks) and send her version outputs.

### Questions requiring approval
- Confirm Python 3.11.9 as the project version.