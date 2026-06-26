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
    """
    # Build vertices from model classes
    class_names = {c.name for c in model.classes}
    vertices = []
    vertex_by_name = {}
    for c in model.classes:
        vid = f"v_{c.name}"
        gv = GraphVertex(vertex_id=vid, element=c)
        vertices.append(gv)
        vertex_by_name[c.name] = gv

    # Build edges from relationships
    # Group by unordered pair of vertex IDs, only keep relationships
    # where both source and target class names exist in model.classes
    from collections import defaultdict
    edge_groups = defaultdict(list)  # key: (min_vid, max_vid), value: list of ParsedRelationship

    for rel in model.relationships:
        if rel.source not in class_names or rel.target not in class_names:
            continue
        source_vid = f"v_{rel.source}"
        target_vid = f"v_{rel.target}"
        min_vid = min(source_vid, target_vid)
        max_vid = max(source_vid, target_vid)
        edge_groups[(min_vid, max_vid)].append(rel)

    edges = []
    for (min_vid, max_vid), rels in sorted(edge_groups.items()):
        edge_id = f"e_{min_vid}_{max_vid}"
        edge = GraphEdge(
            edge_id=edge_id,
            source_vertex_id=min_vid,
            target_vertex_id=max_vid,
            relations=rels,
        )
        edges.append(edge)

    return Graph(vertices=vertices, edges=edges)