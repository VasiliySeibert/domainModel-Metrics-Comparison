import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidGraph import isValidGraph
from Testset.isValidMapping import isValidMapping
from Testset.s1_types import Graph, Mapping


@icontract.require(lambda instructor_graph: isValidGraph(instructor_graph))
@icontract.require(lambda student_graph: isValidGraph(student_graph))
@icontract.ensure(lambda result: isValidMapping(result))
@icontract.ensure(
    lambda result: all(0.0 <= v <= 1.0 for v in result.relation_cost_matrix.values())
)
@icontract.ensure(
    lambda result: all(
        v == 0.0
        for (i, j), v in result.relation_cost_matrix.items()
        if i == j
    )
)
# Note: the post-condition "matrix is symmetric when models are swapped" is a
# meta-property across two function invocations and cannot be expressed as a
# single-run contract; it is documented in the docstring below.
def computeRelationMapping(instructor_graph: Graph, student_graph: Graph) -> Mapping:
    r"""
    Compute the intra-level relation cost matrix for the Graph Edit Distance
    (GED) pipeline.

    This function implements the *intra-level* distance computation for the
    **inter-element** (relational) perspective of the class-model GED framework
    described in the S1 specification (``s1.md``, § "Decompose functions") and
    in Čech (2019), *Expert Systems With Applications* 130 (2019) 206–224.

    What the function does
    ----------------------
    For every pair of graph edges ``(e, e')`` — where ``e`` is an edge of the
    ``instructor_graph`` and ``e'`` is an edge of the ``student_graph`` — the
    function evaluates the tree distance ``δ(R_mn, R_m'n')`` between the two
    relation subsets ``ρ(e) = R_mn`` and ``ρ(e') = R_m'n'``.  The distance
    measures how dissimilar the two sets of relationships are when the
    endpoints of the edges are aligned.  All computed distances are stored in
    ``mapping.relation_cost_matrix`` so that the downstream
    :func:`computeOptimalMapping` step can use them as edge-substitution
    costs.

    The function **only** populates ``mapping.relation_cost_matrix``; the
    remaining fields of the returned :class:`Mapping` instance keep their
    default (empty) values because the optimal bijection is not yet known.

    Parameters
    ----------
    instructor_graph : Graph
        The attributed undirected multigraph ``G = (V, E, μ, ρ)`` representing
        the instructor model.  Must satisfy ``isValidGraph``.
    student_graph : Graph
        The attributed undirected multigraph representing the student model.
        Must satisfy ``isValidGraph``.

    Returns
    -------
    Mapping
        A fresh ``Mapping`` instance whose ``relation_cost_matrix`` field
        contains every pairwise distance ``δ(R_mn, R_m'n')`` for
        ``e ∈ instructor_graph`` and ``e' ∈ student_graph``.  The returned
        mapping also satisfies ``isValidMapping``.

    Algorithm and theory (deterministic)
    ------------------------------------
    Each relation subset assigned to an edge is represented as a tree.  The
    matching follows the recursive vertex-matching strategy:

    * **Root vertex** – the set of all relations ``R_mn = ρ(e)`` mapped to
      the edge ``e``.

    * **Set matching** – The set of relations is matched with the Hungarian
      algorithm on ε-padded extended sets (pairing with ε costs ``1.0``).
      The result is normalised by ``max(|R|, |R'|)``.

    * **Single relation distance** – For two ``ParsedRelationship`` instances
      ``r`` and ``r'``:

      .. math::
          \delta_{rel}(r, r') = 0.4 \cdot \delta_{kind} + 0.3 \cdot \delta_{source} + 0.3 \cdot \delta_{target}

      where
          - ``δ_kind``   – distance between ``relationship_type`` values.
          - ``δ_source`` – relation-end distance for the source end.
          - ``δ_target`` – relation-end distance for the target end.

    * **Relation-end distance** – For two relation ends:

      .. math::
          \delta_{end}(b, b') = 0.4 \cdot \delta_{role} + 0.4 \cdot \delta_{card} + 0.2 \cdot \delta_{nav}

      where
          - ``δ_role`` – normalised Levenshtein distance on ``label``
            (empty string if ``None``).
          - ``δ_card`` – Jaccard distance on parsed multiplicity sets.
            Multiplicity strings are parsed into sets of integers: ``"1..*"``
            → ``{1, 2, ..., 100}`` (cap ``*`` at 100), ``"0..1"`` → ``{0, 1}``,
            comma-separated parts are unioned.  If either cardinality is
            ``None`` and the other is not, distance is ``1.0``.
          - ``δ_nav``  – navigability proxy: ``0.0`` if both ``source_cardinality``
            are ``None`` or both are not ``None``; ``1.0`` otherwise.

    * **Relation-kind distance table** – Exact semantic distances:

      .. list-table::
         :header-rows: 1

         * - Pair
           - Distance
         * - Identical kinds
           - 0.0
         * - ``association`` ↔ ``directed_association``
           - 0.25
         * - ``composition`` ↔ ``aggregation``
           - 0.25
         * - ``inheritance`` ↔ ``composition`` / ``aggregation``
           - 0.50
         * - ``association`` / ``directed`` ↔ ``composition`` / ``aggregation``
           - 0.50
         * - ``inheritance`` ↔ ``association`` / ``directed``
           - 0.50
         * - Any pair involving ``dependency`` (not identical)
           - 0.75
         * - All other distinct pairs
           - 1.00

    Consequently the overall edge-substitution cost satisfies

    .. math::
        c((u,v) \to (u',v')) = \delta(\rho(u,v), \rho(u',v')) \in [0, 1]

    Insertion and deletion of an edge are assigned a constant cost of 1.

    Preconditions (requires)
    ----------------------
    * ``isValidGraph(instructor_graph)``
    * ``isValidGraph(student_graph)``

    Postconditions (ensures)
    ------------------------
    * ``isValidMapping(mapping)``
    * Every value stored in ``mapping.relation_cost_matrix`` lies in the
      closed interval ``[0, 1]``.
    * Diagonal entries — pairs ``(edge_id, edge_id)`` where the same edge
      identifier appears on both sides — are exactly ``0`` (identity of
      indiscernibles).
    * *Symmetry*: if the two graphs are swapped and the function is invoked
      again, the resulting matrix is the transpose of the original one.
      This meta-property is guaranteed by the symmetric distance definitions
      and the framework's definitiveness property.
    """
    ...
