import sys
from pathlib import Path
from typing import List, Tuple, Set

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidUCG import isValidUCG
from Testset.isValidSimilarity import isValidSimilarity
from Testset.s1_types import UCG


# Default weights for intra-structure components.
# Because the concrete parser does not extract operations or parameters,
# simOper and simParam always evaluate to 1.0 (zero edit cost).  The
# effective formula therefore reduces to:
#     sim_intra = ALPHA * simAttr + BETA * 1.0 + GAMMA * 1.0
ALPHA: float = 0.4   # weight of attribute component
BETA:  float = 0.5   # weight of operation component (always 1.0 here)
GAMMA: float = 0.1   # weight of parameter component (always 1.0 here)

# Edit costs (all set to 1; the edit distance is measured by operation count)
IC1: int = 1   # insertion/deletion cost for one attribute vertex + edge
IC2: int = 1   # insertion/deletion cost for one operation vertex + edge
IC3: int = 1   # insertion/deletion cost for one parameter vertex + edge


@icontract.require(lambda g1, g2, matching_pairs: (
    isValidUCG(g1) and isValidUCG(g2)
))
@icontract.ensure(lambda result: isValidSimilarity(result))
def computeIntraStructureSimilarity(
    g1: UCG, g2: UCG, matching_pairs: Set[Tuple[str, str]]
) -> float:
    r"""
    Calculate intra-structure similarity between two matched UCGs.

    --------------------------------------------------------------------------
    Definitions
    --------------------------------------------------------------------------
    The **intra-structure** of a class vertex is the set of attribute,
    operation, and parameter vertices directly attached to it, together with
    the edges connecting them.

    For each matched class-vertex pair ``(cvi, cvj)`` in ``matching_pairs``:
      * ``AVi`` = attribute vertices attached to ``cvi`` via attribute edges
        (edge_type ``"attribute"``, tag ``"ea"``).
      * ``AVj`` = attribute vertices attached to ``cvj`` via attribute edges.
      * ``OVi`` = operation vertices attached to ``cvi`` via operation edges
        (edge_type ``"operation"``, tag ``"eo"``).
      * ``OVj`` = operation vertices attached to ``cvj`` via operation edges.
      * ``PVik`` = parameter vertices attached to operation ``ovi_k`` via
        parameter edges (edge_type ``"parameter"``, tag ``"ep"``).
      * ``PVjw`` = parameter vertices attached to operation ``ovj_w`` via
        parameter edges.

    The **edit distance** between the intra-structures of ``cvi`` and ``cvj``
    is the minimum number of insertions and deletions required to transform
    one into the other.  Only the counts of surplus/missing elements matter;
    vertex labels are ignored because structural similarity is based on
    topology, not semantics.

    --------------------------------------------------------------------------
    Algorithm
    --------------------------------------------------------------------------
    For each matched pair ``(cvi, cvj)`` in ``matching_pairs``:

      1. Count attribute insertion/deletion cost:
         * ``na_i = |AVi|``, ``na_j = |AVj|``
         * Attribute edit cost = ``|na_i - na_j| * IC1``
         * If both are zero, cost is 0.
         * The numerator contribution: ``(x1 + y1) * IC1``
           where ``x1 = max(0, na_j - na_i)`` (insertions) and
           ``y1 = max(0, na_i - na_j)`` (deletions).

      2. Count operation insertion/deletion cost:
         * ``no_i = |OVi|``, ``no_j = |OVj|``
         * Operation edit cost = ``|no_i - no_j| * IC2``
         * In practice, because the parser does not extract operations,
           ``no_i = no_j = 0`` for all classes, so this cost is always 0.

      3. Count parameter insertion/deletion cost:
         * For each matched operation pair ``(ovi_k, ovj_w)``:
           - ``np_ik = |PVik|``, ``np_jw = |PVjw|``
           - Parameter edit cost = ``sum(|np_ik - np_jw|) * IC3``
         * In practice, because the parser does not extract operations or
           parameters, this cost is always 0.

    Compute per-component similarity:

      simAttr  = 1 - sum(x1 + y1) * IC1 / sum(max(na_i, na_j))
      simOper  = 1 - sum(x2 + y2) * IC2 / sum(max(no_i, no_j))
      simParam = 1 - sum(x3 + y3) * IC3 / sum(max(np_ik, np_jw))

    where each summation ranges over all matched class/operation pairs.
    When both denominator terms are zero for a pair, that pair contributes
    nothing to the sum (treated as 0 / 0 = 0 for that pair).

    Combine:

      sim_intra = ALPHA * simAttr + BETA * simOper + GAMMA * simParam

    --------------------------------------------------------------------------
    Scope limitation (concrete parser)
    --------------------------------------------------------------------------
    Because the concrete PlantUML parser used in this project does not
    extract operations or method parameters, the UCGs produced by
    ``transformUCDtoUCG`` never contain operation vertices, operation edges,
    parameter vertices, or parameter edges.  Consequently:
      * ``simOper`` always evaluates to ``1.0`` (zero edit cost).
      * ``simParam`` always evaluates to ``1.0`` (zero edit cost).
    The effective intra-structure similarity reduces to:
        sim_intra = ALPHA * simAttr + BETA * 1.0 + GAMMA * 1.0
    which simplifies to:
        sim_intra = 0.4 * simAttr + 0.5 + 0.1 = 0.4 * simAttr + 0.6

    --------------------------------------------------------------------------
    Input
    --------------------------------------------------------------------------
    g1 : UCG
        Instructor UCG.
    g2 : UCG
        Student UCG.
    matching_pairs : Set[Tuple[str, str]]
        Set of ``(instructor_class_vertex_id, student_class_vertex_id)``
        pairs derived from the inter-structure similarity step.

    Output
    --------------------------------------------------------------------------
    float
        Intra-structure similarity in ``[0, 1]``.

    Preconditions (requires)
    --------------------------------------------------------------------------
    * ``isValidUCG(g1)``
    * ``isValidUCG(g2)``
    * Every ID in ``matching_pairs`` refers to an existing class vertex in
      ``g1`` (first item) and ``g2`` (second item).

    Postconditions (ensures)
    --------------------------------------------------------------------------
    * ``isValidSimilarity(result)`` holds.
    * ``result == ALPHA * simAttr + BETA * simOper + GAMMA * simParam``
      with the component similarities defined above.
    """
    # Build attribute adjacency maps: class_vertex_id -> set of attribute vertex IDs
    g1_attr_map: dict[str, set[str]] = {}
    g2_attr_map: dict[str, set[str]] = {}

    for e in g1.edges:
        if e.edge_type == "attribute":
            g1_attr_map.setdefault(e.source_vertex_id, set()).add(e.target_vertex_id)
    for e in g2.edges:
        if e.edge_type == "attribute":
            g2_attr_map.setdefault(e.source_vertex_id, set()).add(e.target_vertex_id)

    # Compute attribute similarity
    # For each matched pair (cvi, cvj), compute |AVi| and |AVj|
    # simAttr = 1 - sum(|na_i - na_j|) * IC1 / sum(max(na_i, na_j))
    # When both are zero for a pair, that pair contributes nothing.

    total_attr_diff = 0  # sum of |na_i - na_j| * IC1
    total_attr_max = 0   # sum of max(na_i, na_j)

    for cvi, cvj in matching_pairs:
        na_i = len(g1_attr_map.get(cvi, set()))
        na_j = len(g2_attr_map.get(cvj, set()))
        total_attr_diff += abs(na_i - na_j) * IC1
        total_attr_max += max(na_i, na_j)

    if total_attr_max == 0:
        simAttr = 1.0
    else:
        simAttr = 1.0 - (total_attr_diff / total_attr_max)

    # simOper and simParam are always 1.0 (parser doesn't extract operations/parameters)
    simOper = 1.0
    simParam = 1.0

    # Combined intra-structure similarity
    sim_intra = ALPHA * simAttr + BETA * simOper + GAMMA * simParam

    # Clamp to [0, 1]
    return max(0.0, min(1.0, sim_intra))
