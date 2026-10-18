"""Check that the EconoCausal Python environment is usable.

Run from the project root, with the virtual environment active:
    python scripts/check_environment.py

It prints the installed version of each required package and runs a tiny
EconML Double ML fit on random toy data. The toy data is only a smoke test of
the installation. It says nothing about discounts or real causal effects.
"""
import importlib
import sys

REQUIRED = [
    "numpy", "pandas", "sklearn", "scipy",
    "econml", "dowhy", "plotly", "fastapi", "uvicorn", "pytest",
]


def check_imports():
    ok = True
    for name in REQUIRED:
        try:
            module = importlib.import_module(name)
            print(f"  OK       {name:<9} {getattr(module, '__version__', 'unknown version')}")
        except Exception as exc:  # report every failure, do not stop at the first
            ok = False
            print(f"  MISSING  {name:<9} {type(exc).__name__}: {str(exc)[:100]}")
    return ok


def econml_smoke_test():
    import numpy as np
    from econml.dml import LinearDML
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

    rng = np.random.default_rng(0)
    n = 500
    X = rng.normal(size=(n, 3))
    T = rng.binomial(1, 0.5, size=n)
    Y = 0.5 * T + X[:, 0] + rng.normal(size=n)  # toy data only

    est = LinearDML(
        model_y=RandomForestRegressor(n_estimators=20, random_state=0),
        model_t=RandomForestClassifier(n_estimators=20, random_state=0),
        discrete_treatment=True,
        random_state=0,
    )
    est.fit(Y, T, X=X)
    effects = est.effect(X)
    print(f"  EconML LinearDML fit OK; produced {len(effects)} effect estimates")


def main():
    print(f"Python {sys.version.split()[0]}")
    print("Package check:")
    imports_ok = check_imports()
    if not imports_ok:
        print("\nRESULT: FAILED - install the missing packages, then run this again.")
        return 1
    print("EconML smoke test:")
    try:
        econml_smoke_test()
    except Exception as exc:
        print(f"  FAILED   {type(exc).__name__}: {str(exc)[:200]}")
        print("\nRESULT: FAILED - EconML is installed but did not run.")
        return 1
    print("\nRESULT: OK - environment is usable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
