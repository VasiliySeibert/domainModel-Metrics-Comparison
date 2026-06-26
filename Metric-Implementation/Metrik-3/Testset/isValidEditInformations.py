import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Testset.s1_types import EditInformations, EditInformation, OperationType


def isValidEditInformations(edit_informations: EditInformations) -> bool:
    """
    Validate that an EditInformations instance is a well-formed,
    complete edit path with correctly bounded costs.
    """
    # 1. Must be an EditInformations instance
    if not isinstance(edit_informations, EditInformations):
        return False

    # 2. operations must be a list
    if not isinstance(edit_informations.operations, list):
        return False

    # 3. Every item must be an EditInformation instance
    if not all(isinstance(op, EditInformation) for op in edit_informations.operations):
        return False

    # 4. Every operation_type must be a known OperationType
    for op in edit_informations.operations:
        if not isinstance(op.operation_type, OperationType):
            return False

    # 5. raw_cost must be numeric and ≥ 0
    for op in edit_informations.operations:
        if not isinstance(op.raw_cost, (int, float)) or op.raw_cost < 0:
            return False

    # 6. Insertion and deletion operations must have raw_cost == 1
    for op in edit_informations.operations:
        if op.operation_type in {
            OperationType.VERTEX_DELETION,
            OperationType.VERTEX_INSERTION,
            OperationType.EDGE_DELETION,
            OperationType.EDGE_INSERTION,
        }:
            if op.raw_cost != 1.0:
                return False

    # 7. Substitution operations must have raw_cost in [0, 1]
    for op in edit_informations.operations:
        if op.operation_type in {
            OperationType.VERTEX_SUBSTITUTION,
            OperationType.EDGE_SUBSTITUTION,
        }:
            if not (0.0 <= op.raw_cost <= 1.0):
                return False

    # 8. scaled_cost must be numeric and in [0, 1]
    for op in edit_informations.operations:
        if not isinstance(op.scaled_cost, (int, float)) or not (0.0 <= op.scaled_cost <= 1.0):
            return False

    # 9. total_scaled_distance must be numeric and in [0, 1]
    if not isinstance(edit_informations.total_scaled_distance, (int, float)):
        return False
    if not (0.0 <= edit_informations.total_scaled_distance <= 1.0):
        return False

    # 10. No duplicate edit operations (same type, source_ref, target_ref)
    seen = set()
    for op in edit_informations.operations:
        key = (op.operation_type.value, op.source_ref, op.target_ref)
        if key in seen:
            return False
        seen.add(key)

    return True


if __name__ == "__main__":
    # Minimal smoke test
    ei = EditInformations(
        operations=[
            EditInformation(
                operation_type=OperationType.VERTEX_SUBSTITUTION,
                source_ref="vA",
                target_ref="vA1",
                raw_cost=0.0,
                scaled_cost=0.0,
            ),
            EditInformation(
                operation_type=OperationType.VERTEX_DELETION,
                source_ref="vB",
                target_ref=None,
                raw_cost=1.0,
                scaled_cost=0.2,
            ),
        ],
        total_scaled_distance=0.2,
    )
    print(isValidEditInformations(ei))  # Expected: True
