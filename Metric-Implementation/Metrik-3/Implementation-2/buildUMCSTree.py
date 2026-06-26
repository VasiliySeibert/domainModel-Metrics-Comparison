import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidUCG import isValidUCG
from Testset.isValidUMCSTree import isValidUMCSTree
from Testset.s1_types import UCG, UMCSNode, UMCS, UCGEdge

from computeUMCSList import computeUMCSList


@icontract.require(lambda g1, g2: isValidUCG(g1) and isValidUCG(g2))
@icontract.ensure(lambda result: isValidUMCSTree(result))
def buildUMCSTree(g1: UCG, g2: UCG) -> UMCSNode:
    r"""
    Build the UMCS (UCG Maximum Common Subgraph) Tree between two UCGs.
    """
    root = UMCSNode()

    mcsl = computeUMCSList(g1, g2)

    if not mcsl:
        return root

    root.mcsl = mcsl

    # Pre-index g1 edges by edge_id and g2 edges by (source, target, tag)
    g1_edge_by_id = {e.edge_id: e for e in g1.edges}
    g2_rel_edges = [e for e in g2.edges if e.edge_type == "relationship"]

    for umcs in mcsl:
        # Subtract from g1: remove relationship edges in umcs.edge_ids
        g1_remaining_edges = [
            e for e in g1.edges if not (e.edge_type == "relationship" and e.edge_id in umcs.edge_ids)
        ]
        g1_rem = UCG(vertices=list(g1.vertices), edges=g1_remaining_edges)

        # Subtract from g2: find corresponding edges via vertex_map
        g2_edges_to_remove = set()
        for e1_id in umcs.edge_ids:
            e1 = g1_edge_by_id[e1_id]
            s1 = e1.source_vertex_id
            t1 = e1.target_vertex_id
            s2 = umcs.vertex_map[s1]
            t2 = umcs.vertex_map[t1]
            tag = e1.tag

            # Find unique matching edge in g2
            matches = [
                e for e in g2_rel_edges
                if e.source_vertex_id == s2 and e.target_vertex_id == t2 and e.tag == tag
            ]
            # Deterministic tie-breaker (source_id, target_id) - smallest
            matches.sort(key=lambda e: (e.source_vertex_id, e.target_vertex_id))
            if matches:
                g2_edges_to_remove.add(matches[0].edge_id)

        g2_remaining_edges = [
            e for e in g2.edges if not (e.edge_type == "relationship" and e.edge_id in g2_edges_to_remove)
        ]
        g2_rem = UCG(vertices=list(g2.vertices), edges=g2_remaining_edges)

        child = buildUMCSTree(g1_rem, g2_rem)
        root.children.append(child)

    return root
