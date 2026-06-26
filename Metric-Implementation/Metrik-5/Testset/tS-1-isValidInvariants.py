"""
Comprehensive invariant tests for the S-1 similarity metric.

Tests the four validator functions exported by Testset.metric_invariants:
    1. isValidParsedModel  – validates ParsedModel instances
    2. isValidDiagram      – validates internal Diagram instances
    3. isValidUCG          – validates UML Common Graph (networkx.MultiDiGraph)
    4. isValidSimilarity   – validates scalar similarity scores

This module follows the same shape as Testset/tS-1-isValidModel.py (real-model
parsing) and tS-1-isValidMapping.py (exhaustive invariant checklist).
"""

import sys
from pathlib import Path

# Add the metric root to path so Parser and Testset modules are found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import networkx as nx

from Testset.metric_invariants import (
    isValidParsedModel,
    isValidDiagram,
    isValidUCG,
    isValidSimilarity,
)
from Parser import PlantUMLParser
from Parser.models import (
    ParsedModel,
    ParsedClass,
    ParsedEnum,
    ParsedAttribute,
    ParsedRelationship,
    RelationshipType,
)
from Specification.metric_models import AttributeInfo, ClassInfo, Edge, Diagram

# ---------------------------------------------------------------------------
# 1. isValidParsedModel tests
# ---------------------------------------------------------------------------

def test_isValidParsedModel_empty():
    """Empty ParsedModel should be valid."""
    assert isValidParsedModel(ParsedModel()) is True


def test_isValidParsedModel_from_real_student():
    """Parse real student model and assert validity."""
    student_model = """
    @startuml
    class Person {
      String name
      String address
    }
    class Victim
    Person <|-- Victim
    @enduml
    """
    parser = PlantUMLParser(strict=True)
    model = parser.parse(student_model)
    assert isValidParsedModel(model) is True


def test_isValidParsedModel_duplicate_class_names():
    """Duplicate class names should invalidate the model."""
    model = ParsedModel(
        classes=[
            ParsedClass(name="Person"),
            ParsedClass(name="Person"),
        ]
    )
    assert isValidParsedModel(model) is False


def test_isValidParsedModel_duplicate_enum_names():
    """Duplicate enum names should invalidate the model."""
    model = ParsedModel(
        enums=[
            ParsedEnum(name="Status", values=["Active"]),
            ParsedEnum(name="Status", values=["Inactive"]),
        ]
    )
    assert isValidParsedModel(model) is False


def test_isValidParsedModel_relation_to_nonexistent_class():
    """Relationship referencing a non-existent class should invalidate."""
    model = ParsedModel(
        classes=[ParsedClass(name="Person")],
        relationships=[
            ParsedRelationship(
                source="Person",
                target="Address",
                relationship_type=RelationshipType.ASSOCIATION,
            )
        ],
    )
    assert isValidParsedModel(model) is False


def test_isValidParsedModel_wrong_type():
    """Passing a non-ParsedModel should return False."""
    assert isValidParsedModel("not a model") is False


# ---------------------------------------------------------------------------
# 2. isValidDiagram tests
# ---------------------------------------------------------------------------

def test_isValidDiagram_empty() -> bool:
    """Empty Diagram should be valid."""
    assert isValidDiagram(Diagram()) is True


def test_isValidDiagram_basic():
    """Minimal valid Diagram with one class and one attribute."""
    diagram = Diagram(
        classes=[
            ClassInfo(
                name="Person",
                attributes=[
                    AttributeInfo(name="name", type="String", modifier=""),
                ],
            )
        ]
    )
    assert isValidDiagram(diagram) is True


def test_isValidDiagram_enum_as_class():
    """Diagram containing an enum converted to a ClassInfo."""
    diagram = Diagram(
        classes=[
            ClassInfo(
                name="Status",
                attributes=[
                    AttributeInfo(name="Active", type="enum_value", modifier="const"),
                ],
            )
        ]
    )
    assert isValidDiagram(diagram) is True


def test_isValidDiagram_with_edges():
    """Diagram with association, dependency, and generalization edges."""
    diagram = Diagram(
        classes=[
            ClassInfo(name="Person"),
            ClassInfo(name="Address"),
        ],
        associations=[
            Edge(source="Person", target="Address", name="livesAt", ownership="none"),
            Edge(source="Person", target="Address", name="", ownership="composition"),
            Edge(source="Person", target="Address", name="", ownership="aggregation"),
        ],
        dependencies=[
            Edge(source="Person", target="Address", name="uses"),
        ],
        generalizations=[
            Edge(source="Person", target="Mammal"),
        ],
    )
    assert isValidDiagram(diagram) is True


def test_isValidDiagram_duplicate_association():
    """Duplicate (source, target, ownership, name) in associations invalidates."""
    diagram = Diagram(
        classes=[ClassInfo(name="Person"), ClassInfo(name="Address")],
        associations=[
            Edge(source="Person", target="Address", name="livesAt", ownership="none"),
            Edge(source="Person", target="Address", name="livesAt", ownership="none"),
        ],
    )
    assert isValidDiagram(diagram) is False


def test_isValidDiagram_empty_class_name():
    """Empty class name should invalidate the diagram."""
    diagram = Diagram(
        classes=[ClassInfo(name="")],
    )
    assert isValidDiagram(diagram) is False


def test_isValidDiagram_empty_attribute_name():
    """Empty attribute name should invalidate the diagram."""
    diagram = Diagram(
        classes=[
            ClassInfo(
                name="Person",
                attributes=[AttributeInfo(name="", type="String")],
            )
        ],
    )
    assert isValidDiagram(diagram) is False


def test_isValidDiagram_invalid_modifier():
    """Attribute modifier other than 'const' or '' should invalidate."""
    diagram = Diagram(
        classes=[
            ClassInfo(
                name="Person",
                attributes=[AttributeInfo(name="age", modifier="readonly")],
            )
        ],
    )
    assert isValidDiagram(diagram) is False


def test_isValidDiagram_invalid_association_ownership():
    """Association ownership outside allowed set should invalidate."""
    diagram = Diagram(
        classes=[ClassInfo(name="Person"), ClassInfo(name="Address")],
        associations=[
            Edge(source="Person", target="Address", ownership="invalid"),
        ],
    )
    assert isValidDiagram(diagram) is False


def test_isValidDiagram_dependency_with_non_none_ownership():
    """Dependency with ownership != 'none' should invalidate."""
    diagram = Diagram(
        classes=[ClassInfo(name="Person"), ClassInfo(name="Address")],
        dependencies=[
            Edge(source="Person", target="Address", ownership="aggregation"),
        ],
    )
    assert isValidDiagram(diagram) is False


def test_isValidDiagram_generalization_with_non_none_ownership():
    """Generalization with ownership != 'none' should invalidate."""
    diagram = Diagram(
        classes=[ClassInfo(name="Person"), ClassInfo(name="Mammal")],
        generalizations=[
            Edge(source="Person", target="Mammal", ownership="composition"),
        ],
    )
    assert isValidDiagram(diagram) is False


# ---------------------------------------------------------------------------
# 3. isValidUCG tests
# ---------------------------------------------------------------------------

def test_isValidUCG_empty():
    """Empty MultiDiGraph should be valid (no tags to check, no dangling edges)."""
    assert isValidUCG(nx.MultiDiGraph()) is True


def test_isValidUCG_class_and_attribute():
    """UCG with one class vertex and one attribute vertex connected by e_a."""
    G = nx.MultiDiGraph()
    G.add_node("vc_Person", tag="vc")
    G.add_node("va_Person_name", tag="va")
    G.add_edge("vc_Person", "va_Person_name", tag="e_a")
    assert isValidUCG(G) is True


def test_isValidUCG_all_edge_types():
    """UCG with all six valid edge tag types."""
    G = nx.MultiDiGraph()
    G.add_node("vc_A", tag="vc")
    G.add_node("vc_B", tag="vc")
    G.add_node("va_A_x", tag="va")

    G.add_edge("vc_A", "va_A_x", tag="e_a")
    G.add_edge("vc_A", "vc_B", tag="e_1")
    G.add_edge("vc_A", "vc_B", tag="e_2")
    G.add_edge("vc_A", "vc_B", tag="e_3")
    G.add_edge("vc_A", "vc_B", tag="e_4")
    G.add_edge("vc_A", "vc_B", tag="e_5")
    assert isValidUCG(G) is True


def test_isValidUCG_invalid_node_tag():
    """Node with tag outside {'vc', 'va'} should invalidate."""
    G = nx.MultiDiGraph()
    G.add_node("vc_A", tag="vc")
    G.add_node("invalid", tag="vx")
    assert isValidUCG(G) is False


def test_isValidUCG_invalid_edge_tag():
    """Edge with tag outside allowed set should invalidate."""
    G = nx.MultiDiGraph()
    G.add_node("vc_A", tag="vc")
    G.add_node("vc_B", tag="vc")
    G.add_edge("vc_A", "vc_B", tag="e_99")
    assert isValidUCG(G) is False


def test_isValidUCG_dangling_edge():
    """Edge referencing a non-existent node should invalidate."""
    G = nx.MultiDiGraph()
    G.add_node("vc_A", tag="vc")
    # Edge points to non-existent node 'vc_B'
    G.add_edge("vc_A", "vc_B", tag="e_1")
    assert isValidUCG(G) is False


def test_isValidUCG_not_multidigraph():
    """Passing a plain DiGraph should invalidate."""
    G = nx.DiGraph()
    G.add_node("vc_A", tag="vc")
    assert isValidUCG(G) is False


# ---------------------------------------------------------------------------
# 4. isValidSimilarity tests
# ---------------------------------------------------------------------------

def test_isValidSimilarity_bounds():
    """Values exactly at 0.0 and 1.0 should be valid."""
    assert isValidSimilarity(0.0) is True
    assert isValidSimilarity(1.0) is True


def test_isValidSimilarity_midrange():
    """Typical midrange values should be valid."""
    assert isValidSimilarity(0.5) is True
    assert isValidSimilarity(0.33333) is True


def test_isValidSimilarity_negative():
    """Negative values should invalidate."""
    assert isValidSimilarity(-0.1) is False


def test_isValidSimilarity_above_one():
    """Values above 1.0 should invalidate."""
    assert isValidSimilarity(1.0001) is False


def test_isValidSimilarity_bool():
    """Booleans should invalidate (not int or float in intent)."""
    assert isValidSimilarity(True) is False
    assert isValidSimilarity(False) is False


def test_isValidSimilarity_non_numeric():
    """Non-numeric types should invalidate."""
    assert isValidSimilarity("0.5") is False
    assert isValidSimilarity(None) is False
    assert isValidSimilarity([0.5]) is False


# ---------------------------------------------------------------------------
# 5. Real-model integration test (reuses parser output)
# ---------------------------------------------------------------------------

def test_student_model_all_invariants():
    """
    Parse the canonical student model and assert that:
      * isValidParsedModel returns True
      * isValidDiagram on an empty hand-built diagram also returns True
      * isValidUCG on an empty MultiDiGraph also returns True
    """
    student_model = """
    @startuml
    class Person {
      String name
      String address
    }
    class Victim
    Person <|-- Victim
    @enduml
    """
    parser = PlantUMLParser(strict=True)
    model = parser.parse(student_model)
    assert isValidParsedModel(model) is True
    assert isValidDiagram(Diagram()) is True
    assert isValidUCG(nx.MultiDiGraph()) is True
    assert isValidSimilarity(0.7) is True


# ---------------------------------------------------------------------------
# Main entry point (print pass/fail like existing tests)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_list = [
        test_isValidParsedModel_empty,
        test_isValidParsedModel_from_real_student,
        test_isValidParsedModel_duplicate_class_names,
        test_isValidParsedModel_duplicate_enum_names,
        test_isValidParsedModel_relation_to_nonexistent_class,
        test_isValidParsedModel_wrong_type,
        test_isValidDiagram_empty,
        test_isValidDiagram_basic,
        test_isValidDiagram_enum_as_class,
        test_isValidDiagram_with_edges,
        test_isValidDiagram_duplicate_association,
        test_isValidDiagram_empty_class_name,
        test_isValidDiagram_empty_attribute_name,
        test_isValidDiagram_invalid_modifier,
        test_isValidDiagram_invalid_association_ownership,
        test_isValidDiagram_dependency_with_non_none_ownership,
        test_isValidDiagram_generalization_with_non_none_ownership,
        test_isValidUCG_empty,
        test_isValidUCG_class_and_attribute,
        test_isValidUCG_all_edge_types,
        test_isValidUCG_invalid_node_tag,
        test_isValidUCG_invalid_edge_tag,
        test_isValidUCG_dangling_edge,
        test_isValidUCG_not_multidigraph,
        test_isValidSimilarity_bounds,
        test_isValidSimilarity_midrange,
        test_isValidSimilarity_negative,
        test_isValidSimilarity_above_one,
        test_isValidSimilarity_bool,
        test_isValidSimilarity_non_numeric,
        test_student_model_all_invariants,
    ]

    passed = 0
    failed = 0
    for test in test_list:
        try:
            test()
            passed += 1
        except AssertionError as exc:
            failed += 1
            print(f"FAIL: {test.__name__} – {exc}")
        except Exception as exc:
            failed += 1
            print(f"ERROR: {test.__name__} – {exc}")

    total = passed + failed
    print(f"\n{passed}/{total} tests passed, {failed}/{total} tests failed")
