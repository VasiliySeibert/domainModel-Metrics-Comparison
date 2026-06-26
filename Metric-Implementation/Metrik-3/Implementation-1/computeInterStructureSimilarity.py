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

    --------------------------------------------------------------------------
    Definitions
    --------------------------------------------------------------------------
    A **UMCSS** (UMCS Sequence) is a root-to-leaf path in the UMCS Tree.
    It is an ordered list ``[UMCS_1, UMCS_2, ..., UMCS_k]`` where each
    ``UMCS_i`` is the common subgraph found at recursion depth ``i``.

    The **size** of a UMCSS is the total number of relationship edges across
    all UMCS in the path:

        |UMCSS| = sum(len(umcs.edge_ids) for umcs in UMCSS)

    --------------------------------------------------------------------------
    Algorithm
    --------------------------------------------------------------------------
    1. Perform a **pre-order traversal** of ``umcs_tree`` to enumerate all
       root-to-leaf paths.  Each path is one UMCSS.

    2. For each UMCSS:
       a) Compute its total size ``|UMCSS|`` as defined above.
       b) Compute the inter-structure similarity:

              sim_inter = |UMCSS| / min(|RE_g1|, |RE_g2|)

          where ``|RE_g1|`` and ``|RE_g2|`` are the number of relationship
          edges in ``g1`` and ``g2`` respectively.
       c) Derive the **matching pairs** from the edges in the UMCSS:
          Initialise an empty set ``matching_pairs``.
          For every ``UMCS`` in the UMCSS:
            - for every ``e1_id`` in ``UMCS.edge_ids``:
              · look up ``e1`` in ``g1`` (the edge with ``edge_id == e1_id``);
              · let ``s1 = e1.source_vertex_id``, ``t1 = e1.target_vertex_id``;
              · let ``s2 = UMCS.vertex_map[s1]``, ``t2 = UMCS.vertex_map[t1]``;
              · add ``(s1, s2)`` and ``(t1, t2)`` to ``matching_pairs``.
          Because ``matching_pairs`` is a set, duplicate pairs (which arise
          when two matched edges share a class vertex) are automatically
          deduplicated.

    3. Return the list of candidates ``[(sim_inter, matching_pairs), ...]``.

    --------------------------------------------------------------------------
    Input
    --------------------------------------------------------------------------
    g1 : UCG
        Instructor UCG. Must contain at least one relationship edge.
    g2 : UCG
        Student UCG. Must contain at least one relationship edge.
    umcs_tree : UMCSNode
        Root of the UMCS Tree produced by ``buildUMCSTree``.

    Output
    --------------------------------------------------------------------------
    List[Tuple[float, Set[Tuple[str, str]]]]
        Each tuple contains:
          * ``sim_inter`` — float in [0, 1]
          * ``matching_pairs`` — deduplicated set of
            ``(instructor_class_vertex_id, student_class_vertex_id)`` pairs
            derived from the UMCSS path.

    Preconditions (requires)
    --------------------------------------------------------------------------
    * ``isValidUCG(g1)``
    * ``isValidUCG(g2)``
    * ``isValidUMCSTree(umcs_tree)``
    * ``g1`` contains at least one relationship edge.
    * ``g2`` contains at least one relationship edge.

    Postconditions (ensures)
    --------------------------------------------------------------------------
    * Every ``sim_inter`` in the returned list is a finite float in ``[0, 1]``.
    * Every pair in ``matching_pairs`` references class vertices that exist in
      ``g1`` and ``g2`` respectively.
    * ``matching_pairs`` contains no duplicate pairs.
    * The returned list may be empty (when no common subgraph exists).
    """
    # Count relationship edges in g1 and g2
    re_g1 = g1.relationship_edges()
    re_g2 = g2.relationship_edges()
    min_re = min(len(re_g1), len(re_g2))

    if min_re == 0:
        return []

    # Build lookup for g1 edges by edge_id
    g1_edge_map = {e.edge_id: e for e in g1.edges}

    # Enumerate all root-to-leaf paths.
    # Each path is a list of UMCS objects, one per level.
    # The tree structure: node.mcsl[i] corresponds to node.children[i],
    # so we pick one UMCS per level and follow the corresponding child.
    paths: List[List[UMCS]] = []

    def _collect_paths(node: UMCSNode, current_path: List[UMCS]):
        if not node.mcsl:
            # Leaf node (no more UMCS found at this level)
            if current_path:
                paths.append(current_path)
            return
        # Each UMCS in mcsl corresponds to one child
        for i, umcs in enumerate(node.mcsl):
            new_path = current_path + [umcs]
            if i < len(node.children):
                _collect_paths(node.children[i], new_path)
            else:
                # No child for this UMCS (shouldn't happen, but handle gracefully)
                paths.append(new_path)

    _collect_paths(umcs_tree, [])

    # If no paths found (empty tree), return empty list
    if not paths:
        return []

    candidates: List[Tuple[float, Set[Tuple[str, str]]]] = []

    for umcss in paths:
        # Compute |UMCSS| = total number of matched relationship edges
        total_edges = sum(len(umcs.edge_ids) for umcs in umcss)
        sim_inter = total_edges / min_re

        # Derive matching pairs from all UMCS in the path
        matching_pairs: Set[Tuple[str, str]] = set()
        for umcs in umcss:
            for e1_id in umcs.edge_ids:
                e1 = g1_edge_map[e1_id]
                s1 = e1.source_vertex_id
                t1 = e1.target_vertex_id
                s2 = umcs.vertex_map[s1]
                t2 = umcs.vertex_map[t1]
                matching_pairs.add((s1, s2))
                matching_pairs.add((t1, t2))

        candidates.append((sim_inter, matching_pairs))

    return candidates
