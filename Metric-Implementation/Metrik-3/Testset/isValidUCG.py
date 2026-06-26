import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Testset.s1_types import UCG, UCGVertex, UCGEdge


# Valid vertex types and tags per Table 1 in the paper
VALID_VERTEX_TYPES = {"class", "attribute", "operation", "parameter"}

VALID_EDGE_TYPES = {"attribute", "operation", "parameter", "relationship"}
VALID_EDGE_TAGS = {
    "ea",                      # attribute edge
    "eo",                      # operation edge
    "ep",                      # parameter edge
    "e1", "e2", "e3", "e4", "e5", "e6"   # relationship edges
}

# Allowed endpoint types per edge type (source_type, target_type)
_ALLOWED_ENDPOINTS = {
    "attribute":     ("class", "attribute"),
    "operation":     ("class", "operation"),
    "parameter":     ("operation", "parameter"),
    "relationship":  ("class", "class"),
}


def isValidUCG(graph: UCG) -> bool:
    """
    Validate that a UCG adheres to the structure defined in the paper.

    A UCG is defined as (V, E, L) where:
      V = CV U AV U OV U PV
      E = AE U OE U PE U RE
    """
    # 1. Must be a UCG instance
    if not isinstance(graph, UCG):
        return False

    # 2. Every vertex must be a UCGVertex instance with valid type
    if not all(isinstance(v, UCGVertex) for v in graph.vertices):
        return False
    if not all(v.vertex_type in VALID_VERTEX_TYPES for v in graph.vertices):
        return False

    # 3. Every edge must be a UCGEdge instance with valid type and tag
    if not all(isinstance(e, UCGEdge) for e in graph.edges):
        return False
    if not all(e.edge_type in VALID_EDGE_TYPES for e in graph.edges):
        return False
    if not all(e.tag in VALID_EDGE_TAGS for e in graph.edges):
        return False

    # 4. Vertex IDs must be unique
    vertex_ids = [v.vertex_id for v in graph.vertices]
    if len(vertex_ids) != len(set(vertex_ids)):
        return False

    # 5. Edge IDs must be unique
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

    # 7. Endpoint types must match the edge type constraints
    vertex_type_map = {v.vertex_id: v.vertex_type for v in graph.vertices}
    for e in graph.edges:
        allowed = _ALLOWED_ENDPOINTS.get(e.edge_type)
        if allowed is None:
            return False
        src_type = vertex_type_map.get(e.source_vertex_id)
        tgt_type = vertex_type_map.get(e.target_vertex_id)
        if src_type != allowed[0] or tgt_type != allowed[1]:
            return False

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Testset.s1_types import UCG, UCGVertex, UCGEdge


# Valid vertex types and tags per Table 1 in the paper
VALID_VERTEX_TYPES = {"class", "attribute", "operation", "parameter"}

VALID_EDGE_TYPES = {"attribute", "operation", "parameter", "relationship"}
VALID_EDGE_TAGS = {
    "ea",                      # attribute edge
    "eo",                      # operation edge
    "ep",                      # parameter edge
    "e1", "e2", "e3", "e4", "e5", "e6"   # relationship edges
}

# Allowed endpoint types per edge type (source_type, target_type)
_ALLOWED_ENDPOINTS = {
    "attribute":     ("class", "attribute"),
    "operation":     ("class", "operation"),
    "parameter":     ("operation", "parameter"),
    "relationship":  ("class", "class"),
}

# Allowed tags per edge type
_ALLOWED_TAGS_PER_EDGE_TYPE = {
    "attribute":    {"ea"},
    "operation":    {"eo"},
    "parameter":    {"ep"},
    "relationship": {"e1", "e2", "e3", "e4", "e5", "e6"},
}


def isValidUCG(graph: UCG) -> bool:
    """
    Validate that a UCG adheres to the structure defined in the paper.

    A UCG is defined as (V, E, L) where:
      V = CV U AV U OV U PV
      E = AE U OE U PE U RE

    Checks are organised into three groups:
      A. Type-level checks (instances, tags, IDs, references)
      B. Structural topology checks (orphans, tree-shape, duplicates)
      C. Semantic correlation checks (tag vs. edge_type)
    """
    # =====================================================================
    # A. Type-level checks
    # =====================================================================

    # 1. Must be a UCG instance
    if not isinstance(graph, UCG):
        return False

    # 2. Every vertex must be a UCGVertex instance with valid type
    if not all(isinstance(v, UCGVertex) for v in graph.vertices):
        return False
    if not all(v.vertex_type in VALID_VERTEX_TYPES for v in graph.vertices):
        return False

    # 3. Every edge must be a UCGEdge instance with valid type and tag
    if not all(isinstance(e, UCGEdge) for e in graph.edges):
        return False
    if not all(e.edge_type in VALID_EDGE_TYPES for e in graph.edges):
        return False
    if not all(e.tag in VALID_EDGE_TAGS for e in graph.edges):
        return False

    # 4. Vertex IDs must be unique
    vertex_ids = [v.vertex_id for v in graph.vertices]
    if len(vertex_ids) != len(set(vertex_ids)):
        return False

    # 5. Edge IDs must be unique
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

    # 7. Endpoint types must match the edge type constraints
    vertex_type_map = {v.vertex_id: v.vertex_type for v in graph.vertices}
    for e in graph.edges:
        allowed = _ALLOWED_ENDPOINTS.get(e.edge_type)
        if allowed is None:
            return False
        src_type = vertex_type_map.get(e.source_vertex_id)
        tgt_type = vertex_type_map.get(e.target_vertex_id)
        if src_type != allowed[0] or tgt_type != allowed[1]:
            return False

    # 8. Labels must be non-empty strings
    for v in graph.vertices:
        if not isinstance(v.label, str) or not v.label:
            return False

    # =====================================================================
    # B. Structural topology checks
    # =====================================================================

    # Build adjacency / incidence helpers
    out_edges: dict[str, list[UCGEdge]] = {vid: [] for vid in valid_vertex_ids}
    in_edges:  dict[str, list[UCGEdge]] = {vid: [] for vid in valid_vertex_ids}
    for e in graph.edges:
        out_edges[e.source_vertex_id].append(e)
        in_edges[e.target_vertex_id].append(e)

    # 9. Orphaned non-class vertices
    #    Every attribute/operation/parameter vertex must have at least one
    #    incident edge.  (Class vertices may legitimately have zero edges.)
    for v in graph.vertices:
        if v.vertex_type == "class":
            continue
        total_incident = len(out_edges[v.vertex_id]) + len(in_edges[v.vertex_id])
        if total_incident == 0:
            return False

    # 10. Tree-shape constraints (exactly one parent edge per leaf vertex)
    #     Attribute vertex  : exactly 1 incoming attribute edge, 0 outgoing.
    #     Operation vertex  : exactly 1 incoming operation  edge, 0 outgoing.
    #     Parameter vertex  : exactly 1 incoming parameter  edge, 0 outgoing.
    for v in graph.vertices:
        if v.vertex_type == "attribute":
            ae_in = [e for e in in_edges[v.vertex_id] if e.edge_type == "attribute"]
            if len(ae_in) != 1:
                return False
            if out_edges[v.vertex_id]:
                return False

        elif v.vertex_type == "operation":
            oe_in = [e for e in in_edges[v.vertex_id] if e.edge_type == "operation"]
            if len(oe_in) != 1:
                return False
            if out_edges[v.vertex_id]:
                return False

        elif v.vertex_type == "parameter":
            pe_in = [e for e in in_edges[v.vertex_id] if e.edge_type == "parameter"]
            if len(pe_in) != 1:
                return False
            if out_edges[v.vertex_id]:
                return False

    # 11. Duplicate edge prevention
    #     No two edges may share the same ordered 4-tuple
    #     (source_vertex_id, target_vertex_id, edge_type, tag).
    edge_signatures = set()
    for e in graph.edges:
        sig = (e.source_vertex_id, e.target_vertex_id, e.edge_type, e.tag)
        if sig in edge_signatures:
            return False
        edge_signatures.add(sig)

    # =====================================================================
    # C. Semantic correlation checks
    # =====================================================================

    # 12. Tag must be consistent with edge_type
    for e in graph.edges:
        if e.tag not in _ALLOWED_TAGS_PER_EDGE_TYPE.get(e.edge_type, set()):
            return False

    return True


if __name__ == "__main__":
    # Minimal smoke test
    cv1 = UCGVertex(vertex_id="cv1", vertex_type="class", label="Teacher")
    cv2 = UCGVertex(vertex_id="cv2", vertex_type="class", label="Professor")
    av11 = UCGVertex(vertex_id="av11", vertex_type="attribute", label="name")
    e1 = UCGEdge(edge_id="e1", source_vertex_id="cv1", target_vertex_id="cv2",
                 edge_type="relationship", tag="e2")
    ea1 = UCGEdge(edge_id="ea1", source_vertex_id="cv1", target_vertex_id="av11",
                  edge_type="attribute", tag="ea")
    g = UCG(vertices=[cv1, cv2, av11], edges=[e1, ea1])
    print(isValidUCG(g))  # Expected: True
