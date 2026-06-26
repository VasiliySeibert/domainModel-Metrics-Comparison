import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Testset.s1_types import Graph, GraphVertex, GraphEdge
from Parser.models import ParsedRelationship


def isValidGraph(graph: Graph) -> bool:
    """
    Validate that a graph adheres to the attributed undirected multigraph
    structure defined in the GED framework.
    """
    # 1. Must be a Graph instance
    if not isinstance(graph, Graph):
        return False

    # 2. Every vertex must be a GraphVertex instance
    if not all(isinstance(v, GraphVertex) for v in graph.vertices):
        return False

    # 3. Every edge must be a GraphEdge instance
    if not all(isinstance(e, GraphEdge) for e in graph.edges):
        return False

    # 4. Vertex IDs must be unique within the graph
    vertex_ids = [v.vertex_id for v in graph.vertices]
    if len(vertex_ids) != len(set(vertex_ids)):
        return False

    # 5. Edge IDs must be unique within the graph
    edge_ids = [e.edge_id for e in graph.edges]
    if len(edge_ids) != len(set(edge_ids)):
        return False

    # 6. Every edge must reference vertices that exist in the graph
    valid_vertex_ids = set(vertex_ids)
    for e in graph.edges:
        if e.source_vertex_id not in valid_vertex_ids:
            return False
        if e.target_vertex_id not in valid_vertex_ids:
            return False

    # 7. μ is a bijection: each element is mapped to a different vertex
    #    (verified by unique vertex_ids and each vertex having exactly one element)
    element_refs = [v.element for v in graph.vertices]
    if len(element_refs) != len(set(id(ref) for ref in element_refs)):
        return False

    # 8. ρ is a bijection: each edge maps to a unique subset of relations
    relation_subsets = [tuple(id(r) for r in e.relations) for e in graph.edges]
    if len(relation_subsets) != len(set(relation_subsets)):
        return False

    # 9. Every relation in every edge must be a ParsedRelationship instance
    for e in graph.edges:
        if not all(isinstance(r, ParsedRelationship) for r in e.relations):
            return False

    return True


if __name__ == "__main__":
    # Minimal smoke test
    from Parser.models import ParsedClass

    v1 = GraphVertex(vertex_id="v1", element=ParsedClass(name="A"))
    v2 = GraphVertex(vertex_id="v2", element=ParsedClass(name="B"))
    e1 = GraphEdge(edge_id="e1", source_vertex_id="v1", target_vertex_id="v2", relations=[])
    g = Graph(vertices=[v1, v2], edges=[e1])
    print(isValidGraph(g))  # Expected: True
