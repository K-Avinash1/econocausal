"""The causal graph (DAG) and variable roles for EconoCausal.

This file is the single place that says WHICH columns play WHICH role in the
causal analysis. The graph is a set of ASSUMPTIONS written down so they can be
reviewed; it is not something the data proves. See docs/causal_graph.md.

Everything here is plain Python (no DoWhy import) so it can be tested anywhere.
build_causal_model() imports DoWhy only when called.
"""
from typing import Dict, List, Tuple

from .schema import (
    COST_COL, FEATURE_COLS, ID_COL, OUTCOME_COL, REVENUE_COL, TREATMENT_COL,
)

TREATMENT = TREATMENT_COL        # discount_offered
OUTCOME = OUTCOME_COL            # purchased

# Pre-treatment customer attributes: known BEFORE the discount decision.
# They may influence who gets a discount AND who buys, so they are confounders
# (common causes). The model adjusts for all of them.
COMMON_CAUSES: Tuple[str, ...] = tuple(FEATURE_COLS)

# Columns along which the discount effect may differ between customers (CATE).
EFFECT_MODIFIERS: Tuple[str, ...] = tuple(FEATURE_COLS)

# Columns deliberately kept OUT of the graph, with the reason.
EXCLUDED: Dict[str, str] = {
    ID_COL: "identifier only; carries no causal information",
    REVENUE_COL: "measured after the offer and equal to 0 unless purchased (it is a result, not a cause)",
    COST_COL: "measured after the offer and only non-zero for treated buyers (a result, not a cause)",
}

# Edges among the customer attributes (assumed from how the business works;
# in the simulation they match the generator, on real data they would be assumptions).
_FEATURE_EDGES: Tuple[Tuple[str, str], ...] = (
    ("age", "tenure_months"),
    ("tenure_months", "is_loyalty_member"),
    ("tenure_months", "past_purchases_12m"),
    ("is_loyalty_member", "past_purchases_12m"),
    ("is_loyalty_member", "email_engagement"),
    ("past_purchases_12m", "days_since_last_purchase"),
)


def graph_nodes() -> List[str]:
    return list(COMMON_CAUSES) + [TREATMENT, OUTCOME]


def graph_edges() -> List[Tuple[str, str]]:
    """Every attribute -> discount decision, every attribute -> purchase, discount -> purchase."""
    edges: List[Tuple[str, str]] = list(_FEATURE_EDGES)
    edges += [(c, TREATMENT) for c in COMMON_CAUSES]
    edges += [(c, OUTCOME) for c in COMMON_CAUSES]
    edges.append((TREATMENT, OUTCOME))
    return edges


def check_graph_definition() -> List[str]:
    """Return a list of problems (empty list = the definition is consistent)."""
    problems: List[str] = []
    nodes = graph_nodes()
    edges = graph_edges()
    node_set = set(nodes)

    if len(nodes) != len(node_set):
        problems.append("a column appears twice in the graph")
    for a, b in edges:
        if a not in node_set or b not in node_set:
            problems.append(f"edge {a} -> {b} uses a column that is not a node")
        if a == b:
            problems.append(f"edge {a} -> {a} points at itself")
    if len(edges) != len(set(edges)):
        problems.append("an edge is listed twice")
    for col in (TREATMENT, OUTCOME):
        if col in COMMON_CAUSES or col in EFFECT_MODIFIERS:
            problems.append(f"{col} must not be used as a confounder or effect modifier")
    for col in EXCLUDED:
        if col in node_set:
            problems.append(f"{col} is excluded and must not be a node")
    if (OUTCOME, TREATMENT) in edges:
        problems.append("the outcome must not cause the treatment")

    # acyclic check (Kahn's algorithm)
    indegree = {n: 0 for n in node_set}
    for a, b in edges:
        if b in indegree:
            indegree[b] += 1
    queue = [n for n, d in indegree.items() if d == 0]
    seen = 0
    while queue:
        n = queue.pop()
        seen += 1
        for a, b in edges:
            if a == n and b in indegree:
                indegree[b] -= 1
                if indegree[b] == 0:
                    queue.append(b)
    if seen != len(node_set):
        problems.append("the graph has a cycle (it must be a DAG)")
    return problems


def to_gml() -> str:
    """The graph in GML text, the format DoWhy reads."""
    nodes = graph_nodes()
    ids = {name: i for i, name in enumerate(nodes)}
    lines = ["graph [", "  directed 1"]
    for name, i in ids.items():
        lines.append(f'  node [ id {i} label "{name}" ]')
    for a, b in graph_edges():
        lines.append(f"  edge [ source {ids[a]} target {ids[b]} ]")
    lines.append("]")
    return "\n".join(lines)


def to_mermaid() -> str:
    """The graph as Mermaid text (GitHub draws it inside a ```mermaid block)."""
    lines = ["flowchart LR", '  X["customer attributes (8 columns)"]']
    lines.append(f"  X -->|may affect| T[{TREATMENT}]")
    lines.append(f"  X -->|may affect| Y[{OUTCOME}]")
    lines.append("  T -->|effect we want| Y")
    return "\n".join(lines)


def build_causal_model(df):
    """Create the DoWhy CausalModel. Needs `dowhy` installed (Python 3.11 env)."""
    from dowhy import CausalModel

    data = df[graph_nodes()]
    return CausalModel(data=data, treatment=TREATMENT, outcome=OUTCOME, graph=to_gml())
