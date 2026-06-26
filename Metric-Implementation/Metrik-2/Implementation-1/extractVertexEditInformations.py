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
def extractVertexEditInformations(mapping: Mapping) -> EditInformations:
    operations = []
    for entry in mapping.vertex_mappings:
        operations.append(
            EditInformation(
                operation_type=OperationType.VERTEX_SUBSTITUTION,
                source_ref=entry.instructor_vertex_id,
                target_ref=entry.student_vertex_id,
                raw_cost=entry.raw_cost,
                scaled_cost=0.0,
            )
        )
    for vid in mapping.unmapped_instructor_vertices:
        operations.append(
            EditInformation(
                operation_type=OperationType.VERTEX_DELETION,
                source_ref=vid,
                target_ref=None,
                raw_cost=1.0,
                scaled_cost=0.0,
            )
        )
    for vid in mapping.unmapped_student_vertices:
        operations.append(
            EditInformation(
                operation_type=OperationType.VERTEX_INSERTION,
                source_ref=None,
                target_ref=vid,
                raw_cost=1.0,
                scaled_cost=0.0,
            )
        )
    return EditInformations(operations=operations, total_scaled_distance=0.0)
