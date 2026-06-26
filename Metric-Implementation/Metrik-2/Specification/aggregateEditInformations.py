import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidEditInformations import isValidEditInformations
from Testset.s1_types import EditInformations


@icontract.require(lambda vertex_edit_informations, edge_edit_informations: (
    isValidEditInformations(vertex_edit_informations)
))
@icontract.require(lambda vertex_edit_informations, edge_edit_informations: (
    isValidEditInformations(edge_edit_informations)
))
@icontract.ensure(lambda result: isValidEditInformations(result))
def aggregateEditInformations(
    vertex_edit_informations: EditInformations,
    edge_edit_informations: EditInformations,
) -> EditInformations:
    """
    Aggregate vertex-level and edge-level edit operations into a single edit path.

    In the graph-edit-distance (GED) pipeline this function is the *composition*
    step that follows :func:`extractVertexEditInformations` and
    :func:`extractEdgeEditInformations`.  The two partial edit-information objects
    (one containing only vertex operations, the other only edge operations)
    are merged into one :class:`EditInformations` instance that represents the
    complete edit path λ(G₁, G₂) transforming the instructor graph into the
    student graph.

    Parameters
    ----------
    vertex_edit_informations : EditInformations
        Edit operations for all vertices (substitutions, deletions, insertions)
        produced by :func:`extractVertexEditInformations`.  Must satisfy
        :func:`isValidEditInformations`.
    edge_edit_informations : EditInformations
        Edit operations for all edges (substitutions, deletions, insertions)
        produced by :func:`extractEdgeEditInformations`.  Must satisfy
        :func:`isValidEditInformations`.

    Returns
    -------
    EditInformations
        A single combined edit-information object whose ``operations`` list
        contains the concatenation of vertex operations and edge operations,
        sorted according to the order implied by the optimal mapping.  The
        ``total_scaled_distance`` field is initialised to ``0.0`` because
        scaling is performed later by :func:`scaleEditCosts`.

    Algorithm
    ---------
    1. Concatenate ``vertex_edit_informations.operations`` and
       ``edge_edit_informations.operations``.
    2. Sort the combined list by the operation order implied by the optimal
       mapping discovered by :func:`computeOptimalMapping`.
    3. Compute the total raw cost as the sum of ``raw_cost`` of all
       operations (the field is not stored directly in the result; instead
       ``total_scaled_distance`` is set to ``0.0``).
    4. Return ``EditInformations(operations=combined_operations,
       total_scaled_distance=0.0)``.

    Formal specification (s1.md)
    ----------------------------

    ::

        edit_informations = aggregateEditInformations(vertex_edit_informations, edge_edit_informations):
            combined_operations = vertex_edit_informations.operations + edge_edit_informations.operations
            sort combined_operations by operation order implied by the optimal mapping
            total_raw = sum(op.raw_cost for op in combined_operations)
            return EditInformations(operations=combined_operations, total_scaled_distance=0.0)

            requires:
                isValidEditInformations(vertex_edit_informations),
                isValidEditInformations(edge_edit_informations)
            ensures:
                isValidEditInformations(edit_informations)

    Theory & context
    ----------------
    Graph edit distance (GED) measures the dissimilarity between two attributed
    graphs by the minimum cost of edit operations needed to transform the
    source graph into the target graph (Riesen, 2015).  The elementary edit
    operations are vertex/edge insertion, deletion and substitution.
    A *complete edit path* is a set of operations that transforms every
    vertex and edge of the source graph into the target graph.  The
    :func:`aggregateEditInformations` function assembles the complete edit path from
    the separately extracted vertex and edge operation sets.

    Invariants enforced by the contract
    -----------------------------------
    Pre-conditions (``requires``):
        * ``vertex_edit_informations`` satisfies :func:`isValidEditInformations`.
        * ``edge_edit_informations`` satisfies :func:`isValidEditInformations`.

    Post-condition (``ensures``):
        * The returned :class:`EditInformations` satisfies :func:`isValidEditInformations`.
    """
    pass
