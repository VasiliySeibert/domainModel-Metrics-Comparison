import sys
from pathlib import Path
from typing import List, Dict, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidUCG import isValidUCG
from Testset.s1_types import UCG, UCGEdge, UMCS


@icontract.require(lambda g1, g2: isValidUCG(g1) and isValidUCG(g2))
def computeUMCSList(g1: UCG, g2: UCG) -> List[UMCS]:
    r"""
    Search for all UCG Maximum Common Subgraphs (UMCS) between two UCGs.

    This is an exact exponential-time backtracking algorithm.  Its running
    time is acceptable in practice because the UCGs produced by this metric
    typically contain no more than 30 relationship edges.

    --------------------------------------------------------------------------
    Definitions used in this algorithm
    --------------------------------------------------------------------------
    ``E1`` — the list of relationship edges in ``g1``, deterministically sorted
             by ``(tag, source_vertex_id, target_vertex_id)``.
    ``E2`` — the list of relationship edges in ``g2``, deterministically sorted
             by ``(tag, source_vertex_id, target_vertex_id)``.

    A **partial common subgraph** is a set of matched edge pairs
    ``(e1, e2)`` with ``e1 ∈ E1``, ``e2 ∈ E2``, together with an injective
    vertex mapping ``vertex_map`` such that:
      * every matched pair has the same tag: ``e1.tag == e2.tag``,
      * the mapping is consistent: ``vertex_map[e1.source] == e2.source`` and
        ``vertex_map[e1.target] == e2.target`` for every matched pair,
      * the mapping is injective: no two ``e1`` edges map to the same ``e2``
        edge, and no two ``g1`` class vertices map to the same ``g2`` class
        vertex.

    The **size** of a partial common subgraph is the number of matched edge
    pairs.  A **UMCS** is a partial common subgraph of maximum possible size.

    --------------------------------------------------------------------------
    Algorithm (recursive backtracking)
    --------------------------------------------------------------------------
    1. Sort ``E1`` and ``E2`` deterministically.
    2. Maintain global state during the search:
       * ``best_size`` — the largest size found so far.
       * ``mcsl``      — list of all UMCS of size ``best_size``.
       * ``S``         — stack of matched edge pairs ``(e1_id, e2_id)``.
       * ``vertex_map`` — ``Dict[g1_class_id, g2_class_id]``.
       * ``inv_map``    — ``Dict[g2_class_id, g1_class_id]`` (inverse of
         ``vertex_map``; guarantees injectivity).
       * ``used_g2``    — ``Set[e2_id]`` of ``g2`` edges already consumed.
    3. Backtrack over ``E1`` index ``i`` from ``0`` to ``len(E1)``:

       *Skip branch* — call ``backtrack(i + 1)`` without using ``E1[i]``.

       *Include branch* — for every ``e2 ∈ E2`` with the same tag as ``E1[i]``
       and not yet used:
         - **Consistency check**: Let ``s1, t1`` be the source/target class
           vertices of ``E1[i]``, and ``s2, t2`` those of ``e2``.
           The inclusion is feasible iff all of the following hold:
           · ``vertex_map.get(s1)`` is either unset or equals ``s2``.
           · ``vertex_map.get(t1)`` is either unset or equals ``t2``.
           · ``inv_map.get(s2)``   is either unset or equals ``s1``.
           · ``inv_map.get(t2)``   is either unset or equals ``t1``.
         - If feasible, add the vertex mappings (only the ones that are
           newly created), push ``(E1[i].edge_id, e2.edge_id)`` onto ``S``,
           mark ``e2`` as used, recurse ``backtrack(i + 1)``, then pop and
           restore all modified state.
    4. When ``i == len(E1)`` (all edges processed), compare ``len(S)`` to
       ``best_size``:
       * If larger: set ``best_size = len(S)``, clear ``mcsl``, and store a
         new ``UMCS`` built from the current ``S`` and ``vertex_map``.
       * If equal and ``len(S) > 0``: store another ``UMCS`` if it is not
         already present in ``mcsl``.
    5. Return ``mcsl``.

    --------------------------------------------------------------------------
    Matching-pairs derivation
    --------------------------------------------------------------------------
    The ``vertex_map`` stored inside each returned ``UMCS`` directly gives
    the class-vertex matching pairs between ``g1`` and ``g2``.  This mapping is
    required by ``buildUMCSTree`` (to subtract matched edges from ``g2``) and
    by ``computeInterStructureSimilarity`` (to produce ``matching_pairs``).

    --------------------------------------------------------------------------
    Input
    --------------------------------------------------------------------------
    g1 : UCG
        Instructor UCG. Must satisfy ``isValidUCG``.
    g2 : UCG
        Student UCG. Must satisfy ``isValidUCG``.

    Output
    --------------------------------------------------------------------------
    List[UMCS]
        A list of all maximum common subgraphs.  Every ``UMCS`` has the same
        cardinality (the maximum possible).  The list may be empty if no common
        relationship edge exists.

    Preconditions (requires)
    --------------------------------------------------------------------------
    * ``isValidUCG(g1)``
    * ``isValidUCG(g2)``

    Postconditions (ensures)
    --------------------------------------------------------------------------
    * Every ``UMCS`` in the returned list contains:
      - ``edge_ids``   : a ``frozenset`` of valid relationship edge IDs from
        ``g1``.
      - ``vertex_map`` : a ``Dict[str, str]`` mapping ``g1`` class vertex IDs
        to ``g2`` class vertex IDs.  The mapping is injective and consistent
        with every matched edge.
    * All ``UMCS`` in the list have identical cardinality (maximum possible).
    * All ``UMCS`` in the list are pairwise distinct.
    * The list is empty iff ``g1`` and ``g2`` share no relationship edge with
      the same tag under any vertex mapping.
    """
    # Phase 1: Sort relationship edges deterministically
    E1 = sorted(
        g1.relationship_edges(),
        key=lambda e: (e.tag, e.source_vertex_id, e.target_vertex_id)
    )
    E2 = sorted(
        g2.relationship_edges(),
        key=lambda e: (e.tag, e.source_vertex_id, e.target_vertex_id)
    )

    if not E1 or not E2:
        return []

    # Pre-group E2 indices by tag for faster lookup
    E2_by_tag: Dict[str, List[int]] = {}
    for j, e2 in enumerate(E2):
        E2_by_tag.setdefault(e2.tag, []).append(j)

    E1_len = len(E1)
    E2_len = len(E2)

    # State for backtracking
    best_size = [0]
    mcsl: List[UMCS] = []
    S: List[Tuple[str, str]] = []
    vertex_map: Dict[str, str] = {}
    inv_map: Dict[str, str] = {}
    used_g2: set = set()

    def backtrack(i: int):
        if i == E1_len:
            current_size = len(S)
            if current_size > best_size[0]:
                best_size[0] = current_size
                mcsl.clear()
                edge_ids = frozenset(e1_id for e1_id, e2_id in S)
                vm = dict(vertex_map)
                mcsl.append(UMCS(edge_ids=edge_ids, vertex_map=vm))
            elif current_size == best_size[0] and current_size > 0:
                edge_ids = frozenset(e1_id for e1_id, e2_id in S)
                vm = dict(vertex_map)
                new_umcs = UMCS(edge_ids=edge_ids, vertex_map=vm)
                is_duplicate = False
                for existing in mcsl:
                    if existing.edge_ids == new_umcs.edge_ids and existing.vertex_map == new_umcs.vertex_map:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    mcsl.append(new_umcs)
            return

        # Pruning: remaining edges can't beat best_size
        remaining = E1_len - i
        if len(S) + remaining <= best_size[0]:
            return

        e1 = E1[i]
        s1 = e1.source_vertex_id
        t1 = e1.target_vertex_id

        # Skip branch
        backtrack(i + 1)

        # Include branch: try matching E1[i] with each compatible E2 edge
        tag_candidates = E2_by_tag.get(e1.tag, [])
        for j in tag_candidates:
            if j in used_g2:
                continue
            e2 = E2[j]
            s2 = e2.source_vertex_id
            t2 = e2.target_vertex_id

            # Consistency check
            if s1 in vertex_map and vertex_map[s1] != s2:
                continue
            if t1 in vertex_map and vertex_map[t1] != t2:
                continue
            if s2 in inv_map and inv_map[s2] != s1:
                continue
            if t2 in inv_map and inv_map[t2] != t1:
                continue
            # Injectivity: if s1 != t1 but s2 == t2, two different g1 vertices
            # would map to the same g2 vertex, violating injectivity.
            # Symmetrically, if s1 == t1 but s2 != t2, one g1 vertex would
            # need to map to two different g2 vertices, which is impossible.
            if s1 != t1 and s2 == t2:
                continue
            if s1 == t1 and s2 != t2:
                continue

            # Track newly created mappings, handling s1==t1 and s2==t2
            # When s1==t1, we require s2==t2 for consistency. The mapping
            # for the source vertex also covers the target vertex.
            s1_new = s1 not in vertex_map
            t1_new = (t1 != s1) and (t1 not in vertex_map)
            s2_new = s2 not in inv_map
            t2_new = (t2 != s2) and (t2 not in inv_map)

            if s1_new:
                vertex_map[s1] = s2
                inv_map[s2] = s1
            if t1_new:
                vertex_map[t1] = t2
                inv_map[t2] = t1

            S.append((e1.edge_id, e2.edge_id))
            used_g2.add(j)

            backtrack(i + 1)

            S.pop()
            used_g2.discard(j)
            if t1_new:
                del vertex_map[t1]
                del inv_map[t2]
            if s1_new:
                del vertex_map[s1]
                del inv_map[s2]

    backtrack(0)
    return mcsl
