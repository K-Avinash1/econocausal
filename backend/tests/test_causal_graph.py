from econocausal import causal_graph as cg
from econocausal.schema import COLUMN_NAMES, FEATURE_COLS


def test_graph_definition_is_consistent_and_acyclic():
    assert cg.check_graph_definition() == []


def test_treatment_and_outcome_are_not_covariates():
    assert cg.TREATMENT == "discount_offered"
    assert cg.OUTCOME == "purchased"
    assert cg.TREATMENT not in cg.COMMON_CAUSES
    assert cg.OUTCOME not in cg.COMMON_CAUSES


def test_post_treatment_columns_are_excluded():
    nodes = cg.graph_nodes()
    for col in ("order_value", "discount_cost", "customer_id"):
        assert col in cg.EXCLUDED
        assert col not in nodes


def test_every_node_is_a_schema_column():
    assert set(cg.graph_nodes()) <= set(COLUMN_NAMES)
    assert set(cg.COMMON_CAUSES) == set(FEATURE_COLS)


def test_every_attribute_points_to_treatment_and_outcome():
    edges = set(cg.graph_edges())
    for c in cg.COMMON_CAUSES:
        assert (c, cg.TREATMENT) in edges
        assert (c, cg.OUTCOME) in edges
    assert (cg.TREATMENT, cg.OUTCOME) in edges


def test_gml_lists_every_node_and_edge():
    gml = cg.to_gml()
    assert gml.count("node [") == len(cg.graph_nodes())
    assert gml.count("edge [") == len(cg.graph_edges())
    for name in cg.graph_nodes():
        assert f'label "{name}"' in gml


def test_a_cycle_would_be_caught(monkeypatch):
    original = cg.graph_edges
    monkeypatch.setattr(cg, "graph_edges", lambda: original() + [(cg.OUTCOME, "age")])
    problems = cg.check_graph_definition()
    assert any("cycle" in p for p in problems)
