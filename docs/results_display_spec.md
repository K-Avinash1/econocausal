# Results display spec

The results panel shows one analysis run. Source today: a sample file; later: the API.

Shows, in this order:
1. Banner if the run is a simulated or sample run (never hide it).
2. Headline: average effect as percentage points, with a 95% interval, or
   "Interval not available" when the interval is null.
3. Spread: 5th, median, 95th percentile of customer effects; share of customers with negative effect.
4. Table of the first customers: id, effect (pp), interval (pp), purchase chance without discount, typical order value.
5. Notes from the run, always visible.
6. Only if "evaluation" exists: a box labelled "Simulation only" comparing estimate with truth.

Rules:
- Effect numbers are shown as percentage points (0.07 -> 7.0 pp), one decimal.
- Never show a blank or NaN: null becomes "n/a".
- Never call the result "profit" or "proof". The effect is an estimate under assumptions.
- Uploaded files have no "evaluation" box.