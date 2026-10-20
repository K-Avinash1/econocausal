"""Check the causal graph, then ask DoWhy to identify the discount effect.

Run from the project root (venv active):
    python scripts/check_causal_graph.py

Writes docs/dowhy_identification.txt (what DoWhy printed) so the result is evidence in the repo.
This needs DoWhy, so it runs on Avinash's machine (Python 3.11.9 environment).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from econocausal import causal_graph as cg                      # noqa: E402
from econocausal.data_generation import generate_campaign_data  # noqa: E402


def main() -> int:
    problems = cg.check_graph_definition()
    if problems:
        print("Graph definition problems:")
        for p in problems:
            print(" -", p)
        return 1
    print(f"Graph definition OK: {len(cg.graph_nodes())} nodes, {len(cg.graph_edges())} edges, no cycles.")

    observed, _truth = generate_campaign_data(n=5000, seed=42)
    model = cg.build_causal_model(observed)
    estimand = model.identify_effect(proceed_when_unidentifiable=False)

    text = str(estimand)
    print()
    print(text)
    out = ROOT / "docs" / "dowhy_identification.txt"
    out.write_text(
        "DoWhy identification of the effect of discount_offered on purchased\n"
        f"(graph from backend/econocausal/causal_graph.py, 5000 simulated customers, seed 42)\n\n{text}\n",
        encoding="utf-8",
    )
    print(f"\nSaved to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
