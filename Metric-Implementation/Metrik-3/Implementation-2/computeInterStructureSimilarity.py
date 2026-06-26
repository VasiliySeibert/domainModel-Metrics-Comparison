import sys
from pathlib import Path
from typing import List, Tuple, Set

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidUCG import isValidUCG
from Testset.isValidUMCSTree import isValidUMCSTree
from Testset.s1_types import UCG, UMCSNode, UMCS


def _has_relationship_edges(g: UCG) -> bool:
    return any(e.edge_type == "relationship" for e in g.edges)


@icontract.require(lambda g1, g2, umcs_tree: (
    isValidUCG(g1) and isValidUCG(g2) and isValidUMCSTree(umcs_tree)
))
@icontract.require(lambda g1, g2: (
    _has_relationship_edges(g1) and _has_relationship_edges(g2)
))
def computeInterStructureSimilarity(
    g1: UCG, g2: UCG, umcs_tree: UMCSNode
) -> List[Tuple[float, Set[Tuple[str, str]]]]:
    r"""
    Calculate inter-structure similarity candidates from a UMCS Tree.
    """
    re_g1 = len([e for e in g1.edges if e.edge_type == "relationship"])
    re_g2 = len([e for e in g2.edges if e.edge_type == "relationship"])
    min_re = min(re_g1, re_g2)
    if min_re == 0:
        return []

    # Pre-index g1 edges by edge_id
    g1_edge_by_id = {e.edge_id: e for e in g1.edges}

    candidates: List[Tuple[float, Set[Tuple[str, str]]]] = []

    def _traverse(node: UMCSNode, path: List[UMCS]):
        # If leaf (no children), finalize path
        if not node.children:
            total_size = sum(len(umcs.edge_ids) for umcs in path)
            sim_inter = total_size / min_re
            matching_pairs: Set[Tuple[str, str]] = set()
            for umcs in path:
                for e1_id in umcs.edge_ids:
                    e1 = g1_edge_by_id[e1_id]
                    s1 = e1.source_vertex_id
                    t1 = e1.target_vertex_id
                    s2 = umcs.vertex_map[s1]
                    t2 = umcs.vertex_map[t1]
                    matching_pairs.add((s1, s2))
                    matching_pairs.add((t1, t2))
            candidates.append((sim_inter, matching_pairs))
            return

        # Pre-order: for each child, extend path with corresponding UMCS
        for idx, child in enumerate(node.children):
            if idx < len(node.mcsl):
                umcs = node.mcsl[idx]
                _traverse(child, path + [umcs])
            else:
                # Inconsistent tree, but shouldn't happen with valid tree
                _traverse(child, path)

    _traverse(umcs_tree, [])
    return candidates
