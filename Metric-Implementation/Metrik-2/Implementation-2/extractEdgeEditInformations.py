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
    """
    operations = []
    
    # Substitutions
    for entry in mapping.edge_mappings:
        operations.append(EditInformation(
            operation_type=OperationType.EDGE_SUBSTITUTION,
            source_ref=entry.instructor_edge_id,
            target_ref=entry.student_edge_id,
            raw_cost=entry.raw_cost,
            scaled_cost=0.0,
        ))
    
    # Deletions (unmapped instructor edges)
    for eid in mapping.unmapped_instructor_edges:
        operations.append(EditInformation(
            operation_type=OperationType.EDGE_DELETION,
            source_ref=eid,
            target_ref=None,
            raw_cost=1.0,
            scaled_cost=0.0,
        ))
    
    # Insertions (unmapped student edges)
    for eid in mapping.unmapped_student_edges:
        operations.append(EditInformation(
            operation_type=OperationType.EDGE_INSERTION,
            source_ref=None,
            target_ref=eid,
            raw_cost=1.0,
            scaled_cost=0.0,
        ))
    
    return EditInformations(
        operations=operations,
        total_scaled_distance=0.0,
    )