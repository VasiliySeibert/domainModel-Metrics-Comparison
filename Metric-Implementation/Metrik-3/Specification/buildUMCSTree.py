import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidUCG import isValidUCG
from Testset.isValidUMCSTree import isValidUMCSTree
from Testset.s1_types import UCG, UMCSNode, UMCS, UCGEdge

from Specification.computeUMCSList import computeUMCSList


@icontract.require(lambda g1, g2: isValidUCG(g1) and isValidUCG(g2))
@icontract.ensure(lambda result: isValidUMCSTree(result))
def buildUMCSTree(g1: UCG, g2: UCG) -> UMCSNode:
    r"""
    Build the UMCS (UCG Maximum Common Subgraph) Tree between two UCGs.

    --------------------------------------------------------------------------
    Definitions
    --------------------------------------------------------------------------
    A **UMCS Tree** is a rooted tree of ``UMCSNode`` instances.  Each node
    stores a list of UMCS (``mcsl``) found at that recursion depth, and each
    child corresponds to one UMCS in the parent's ``mcsl``.

    A **remainder graph** is the result of removing from a UCG all
    relationship edges that participate in a matched UMCS.  Class vertices,
    attribute vertices, attribute edges, operation vertices, operation edges,
    parameter vertices, and parameter edges are **never** removed, even if a
    class vertex ends up with zero remaining relationship edges.

    --------------------------------------------------------------------------
    Algorithm (deterministic, recursive)
    --------------------------------------------------------------------------
    1. Create an empty root ``UMCSNode``.
    2. Call ``computeUMCSList(g1, g2)`` to obtain ``mcsl``.
    3. If ``mcsl`` is empty, return the root node (leaf).
    4. Otherwise:
       * assign ``mcsl`` to ``root.mcsl``,
       * for each ``umcs`` in ``mcsl`` (in the order returned by
         ``computeUMCSList``):
         a) **Subtract from ``g1``**: remove every relationship edge whose
            ``edge_id`` is in ``umcs.edge_ids``.
         b) **Subtract from ``g2``**: for each ``e1_id`` in ``umcs.edge_ids``,
            look up the corresponding ``e1`` edge in ``g1``, then use
            ``umcs.vertex_map`` to translate ``e1.source`` and ``e1.target``
            into ``g2`` class vertex IDs.  In ``g2``, find the unique
            relationship edge ``e2`` with:
              - ``e2.source`` == mapped source,
              - ``e2.target`` == mapped target,
              - ``e2.tag``    == ``e1.tag``.
            Remove ``e2`` from ``g2``.  (If multiple ``g2`` edges satisfy the
            triple, the deterministic tie-breaker ``(source_id, target_id)``
            chooses the smallest one; however ``computeUMCSList`` guarantees
            injectivity, so at most one such edge exists.)
         c) recursively call ``buildUMCSTree`` on the two remainder graphs,
         d) append the returned subtree as a child of ``root``.
    5. Return ``root``.

    --------------------------------------------------------------------------
    Termination proof
    --------------------------------------------------------------------------
    Each recursion removes at least one relationship edge from both ``g1`` and
    ``g2``.  Because the number of relationship edges is finite and non-negative,
    the recursion depth is bounded by ``min(|RE_g1|, |RE_g2|) + 1``.

    --------------------------------------------------------------------------
    Input
    --------------------------------------------------------------------------
    g1 : UCG
        Instructor UCG. Must satisfy ``isValidUCG``.
    g2 : UCG
        Student UCG. Must satisfy ``isValidUCG``.

    Output
    --------------------------------------------------------------------------
    UMCSNode
        The root of the UMCS Tree.  All subtrees correspond to progressively
        smaller common subgraphs found after removing previous UMCS layers.

    Preconditions (requires)
    --------------------------------------------------------------------------
    * ``isValidUCG(g1)``
    * ``isValidUCG(g2)``

    Postconditions (ensures)
    --------------------------------------------------------------------------
    * ``isValidUMCSTree(result)`` — the tree satisfies:
      - every node is a ``UMCSNode`` instance,
      - at each node, all UMCS in ``mcsl`` have the same cardinality,
      - all UMCS in a node's ``mcsl`` are pairwise distinct,
      - along every root-to-leaf path, UMCS cardinalities are strictly
        decreasing (or non-increasing if an empty ``mcsl`` is considered
        size 0).
    """
    ...
    return UMCSNode()
