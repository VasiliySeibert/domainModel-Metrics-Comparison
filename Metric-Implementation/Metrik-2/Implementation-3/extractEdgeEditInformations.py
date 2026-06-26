import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidMapping import isValidMapping
from Testset.isValidEditInformations import isValidEditInformations
from Testset.s1_types import Mapping, EditInformations, EditInformation, OperationType


@icontract.require(lambda mapping: isValidMapping(mapping))
@icontract.ensure(lambda result: isValidEditInformations(result))
@icontract.ensure(
    lambda mapping, result: len(result.operations)
    == len(mapping.edge_mappings)
    + len(mapping.unmapped_instructor_edges)
    + len(mapping.unmapped_student_edges)
)
@icontract.ensure(
    lambda mapping, result: all(
        op.operation_type == OperationType.EDGE_SUBSTITUTION
        for op in result.operations
        if op.source_ref is not None and op.target_ref is not None
    )
)
@icontract.ensure(
    lambda mapping, result: all(
        op.operation_type == OperationType.EDGE_DELETION and op.raw_cost == 1.0
        for op in result.operations
        if op.source_ref is not None and op.target_ref is None
    )
)
@icontract.ensure(
    lambda mapping, result: all(
        op.operation_type == OperationType.EDGE_INSERTION and op.raw_cost == 1.0
        for op in result.operations
        if op.source_ref is None and op.target_ref is not None
    )
)
def extractEdgeEditInformations(mapping: Mapping) -> EditInformations:
    """
    Extract atomic edge-level edit operations from an optimal GED mapping.

    This function converts the inter-level edge bijection produced by
    :func:`computeOptimalMapping` into a concrete list of edge edit
    operations.  Together with the vertex-level operations produced by
    :func:`extractVertexEditInformations`, the resulting operations form a
    complete edit path that transforms the instructor graph into the student
    graph.

    Algorithm
    ---------
    For every paired edge in ``mapping.edge_mappings`` an
    **edge_substitution** operation is emitted carrying the intra-level
    relation distance ``raw_cost`` (computed earlier by
    :func:`computeRelationMapping`).

    For every instructor edge that remains unmapped
    (``mapping.unmapped_instructor_edges``) an **edge_deletion**
    operation ``(e → ε)`` is emitted with constant cost ``1``.

    For every student edge that remains unmapped
    (``mapping.unmapped_student_edges``) an **edge_insertion**
    operation ``(ε → e')`` is emitted with constant cost ``1``.

    The constant insertion / deletion cost of ``1`` follows the GED
    conditions given in the framework (Eq. 18 in ``metric-information.txt``)
    and guarantees that ``c(e) > 0`` for insertion and deletion, satisfying
    the non-negativity and triangle-inequality requirements of a proper
    graph-edit metric (Riesen, 2015; Čech, 2019).

    Parameters
    ----------
    mapping : Mapping
        A valid mapping instance containing the optimal edge bijection
        (``edge_mappings``), unmapped instructor edges
        (``unmapped_instructor_edges``), unmapped student edges
        (``unmapped_student_edges``), and the accumulated raw cost.

    Returns
    -------
    EditInformations
        An edit-informations instance whose ``operations`` list contains
        exactly:

        * one ``EDGE_SUBSTITUTION`` for each mapped edge pair,
        * one ``EDGE_DELETION``  for each unmapped instructor edge,
        * one ``EDGE_INSERTION`` for each unmapped student edge.

        The ``total_scaled_distance`` field is left at ``0.0`` because
        scaling is performed later by :func:`scaleEditCosts`.

    Formal specification (from ``s1.md``)
    -----------------------------------
    ::

        edit_informations = extractEdgeEditInformations(mapping):
            for each edge_mapping_entry in mapping.edge_mappings:
                create EditInformation with:
                    operation_type = edge_substitution
                    source_ref = instructor_edge_id
                    target_ref = student_edge_id
                    raw_cost   = raw_cost from entry
            for each unmapped_instructor_edge in mapping.unmapped_instructor_edges:
                create EditInformation with:
                    operation_type = edge_deletion
                    source_ref = instructor_edge_id
                    target_ref = None   (ε)
                    raw_cost   = 1
            for each unmapped_student_edge in mapping.unmapped_student_edges:
                create EditInformation with:
                    operation_type = edge_insertion
                    source_ref = None   (ε)
                    target_ref = student_edge_id
                    raw_cost   = 1
            return edit_informations

            requires:
                isValidMapping(mapping)
            ensures:
                isValidEditInformations(edit_informations)

    Invariants enforced by the contracts
    ------------------------------------
    Pre-condition:
        * ``mapping`` satisfies :func:`~Testset.isValidMapping.isValidMapping`.

    Post-condition:
        * The returned ``EditInformations`` satisfies
          :func:`~Testset.isValidEditInformations.isValidEditInformations`.
        * The number of returned operations equals the sum of mapped,
          unmapped instructor, and unmapped student edges.
        * Every operation with two non-``None`` references is an
          ``EDGE_SUBSTITUTION``.
        * Every operation with only a source reference is an
          ``EDGE_DELETION`` with ``raw_cost == 1``.
        * Every operation with only a target reference is an
          ``EDGE_INSERTION`` with ``raw_cost == 1``.
    """
    operations = []
    for entry in mapping.edge_mappings:
        operations.append(
            EditInformation(
                operation_type=OperationType.EDGE_SUBSTITUTION,
                source_ref=entry.instructor_edge_id,
                target_ref=entry.student_edge_id,
                raw_cost=entry.raw_cost,
            )
        )
    for eid in mapping.unmapped_instructor_edges:
        operations.append(
            EditInformation(
                operation_type=OperationType.EDGE_DELETION,
                source_ref=eid,
                target_ref=None,
                raw_cost=1.0,
            )
        )
    for eid in mapping.unmapped_student_edges:
        operations.append(
            EditInformation(
                operation_type=OperationType.EDGE_INSERTION,
                source_ref=None,
                target_ref=eid,
                raw_cost=1.0,
            )
        )
    return EditInformations(operations=operations, total_scaled_distance=0.0)
