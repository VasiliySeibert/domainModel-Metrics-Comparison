import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidModel import isValidModel
from Testset.isValidGraph import isValidGraph
from Testset.s1_types import Graph, GraphVertex, GraphEdge


@icontract.require(lambda model: isValidModel(model))
@icontract.ensure(lambda result: isValidGraph(result))
def createGraph(model) -> Graph:
    """
    Convert a ParsedModel into an attributed undirected multigraph.

    Algorithm (deterministic)
    -------------------------
    1. **Vertices** – For every class ``c`` in ``model.classes`` create exactly
       one ``GraphVertex`` with deterministic ID:

           vertex_id = f"v_{c.name}"

       The vertex carries the class as its ``element`` (μ).

    2. **Edge grouping** – Group all ``ParsedRelationship`` instances by the
       *unordered* pair of their endpoint vertex IDs.  Only relationships whose
       both ``source`` and ``target`` class names exist in ``model.classes``
       are kept.

    3. **Edge direction (lexicographic normalisation)** – For every group
       with endpoint pair ``(a, b)`` store the endpoints in lexicographic
       order:

           source_vertex_id = min(a, b)
           target_vertex_id = max(a, b)

       This makes the graph truly undirected: ``(a,b)`` and ``(b,a)``
       collapse to the same edge.

    4. **Edge IDs** – For every distinct pair create exactly one
       ``GraphEdge`` with deterministic ID:

           edge_id = f"e_{min_vid}_{max_vid}"

       where ``min_vid`` and ``max_vid`` are the lexicographically sorted
       vertex IDs.  The edge carries the full list of ``ParsedRelationship``
       instances between that pair as ``relations`` (ρ).

    Formal Definitions
    ------------------
    A graph G ∈ G is an attributed undirected multigraph

        G = (V, E, μ, ρ)

    where
        V  – finite set of vertices (one per class / interface in the model)
        E ⊆ V × V – finite set of edges (one per distinct pair of elements
            that share at least one relationship)

    Assignment functions
        μ : V → M   bijection mapping each vertex to a unique model element
        ρ : E → Z   bijection mapping each edge to a unique subset of relations
                    between the two elements; Z is the set of all distinct
                    subsets of the relation multiset R.

    Model element (class or interface)
        m = (ν_m, φ_m, k_m, A, O)

        ν_m  – element name      (unique inside the model, ν_m ∈ L_M)
        φ_m  – scope variant     (φ_m ∈ S_M)
        k_m  – element kind      (k_m ∈ {class, interface})
        A    – set of attributes
        O    – set of operations

    Attribute
        a = (ν_a, τ_a, φ_a)

        ν_a  – attribute name    (ν_a ∈ L_A)
        τ_a  – data type         (τ_a ∈ T_A)
        φ_a  – scope variant     (φ_a ∈ S_A)

    Operation
        o = (ν_o, τ_o, φ_o, P)

        ν_o  – operation name    (ν_o ∈ L_O)
        τ_o  – return type       (τ_o ∈ T_O)
        φ_o  – scope variant     (φ_o ∈ S_O)
        P    – set of parameters

    Parameter
        p = (ν_p, τ_p)

        ν_p  – parameter name    (ν_p ∈ L_P)
        τ_p  – parameter type     (τ_p ∈ T_P)

    Relation (binary, exactly two ends)
        r = (k_r, b_s, b_t)

        k_r  – relation kind     (k_r ∈ T_R)
        b_s  – source relation end
        b_t  – target relation end

    Relation end
        b = (ν_b, ψ, h)

        ν_b  – role name
        ψ    – multiplicity constraint
        h    – navigability flag

    Invariants enforced by the contract
    -----------------------------------
    Pre-condition  (requires):
        • `model` satisfies `isValidModel` – unique class / enum names,
          every relation references existing classes, every attribute and
          operation belongs to exactly one element.

    Post-condition (ensures):
        • The returned `Graph` satisfies `isValidGraph` – valid vertex /
          edge IDs, μ and ρ are bijections, every edge references
          existing vertices, every relation is a `ParsedRelationship`.
    """
    from collections import defaultdict
    from Parser.models import ParsedRelationship

    class_names = {c.name for c in model.classes}
    vertices = []
    name_to_vertex = {}
    for c in model.classes:
        vid = f"v_{c.name}"
        vertices.append(GraphVertex(vertex_id=vid, element=c))
        name_to_vertex[c.name] = vid

    groups = defaultdict(list)
    for rel in model.relationships:
        if rel.source not in class_names or rel.target not in class_names:
            continue
        v1 = name_to_vertex[rel.source]
        v2 = name_to_vertex[rel.target]
        min_vid = min(v1, v2)
        max_vid = max(v1, v2)
        groups[(min_vid, max_vid)].append(rel)

    edges = []
    for (min_vid, max_vid), rels in groups.items():
        edge_id = f"e_{min_vid}_{max_vid}"
        edges.append(
            GraphEdge(
                edge_id=edge_id,
                source_vertex_id=min_vid,
                target_vertex_id=max_vid,
                relations=rels,
            )
        )

    return Graph(vertices=vertices, edges=edges)
