"""
checkMissing — Detect missing/extra elements mistakes.

Unmapped classes:
- Instructor class → mistake_id 1 (Missing class)
- Student  class   → mistake_id 2 (Extra class)

Unmapped instructor relationships:
- INHERITANCE           → mistake_id 10 (Missing inheritance)
- COMPOSITION/AGGREGATION → mistake_id 15 (Missing composition/aggregation)
- otherwise             → mistake_id 6  (Missing relationship)

Unmapped student relationships:
- INHERITANCE           → mistake_id 11 (Extra inheritance)
- COMPOSITION/AGGREGATION → mistake_id 16 (Extra composition/aggregation)
- otherwise             → mistake_id 7  (Extra relationship)
"""

import icontract
import sys
from pathlib import Path
from typing import List

_D4 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_D4))
sys.path.insert(0, str(_D4 / "Testset"))
sys.path.insert(0, str(_D4 / "Parser"))

from isValidModel import isValidModel, ParsedModel
from isValidMapping import (
    isValidMapping,
    ParsedMapping,
)
from isValidMistakes import isValidMistakes, ParsedMistake
from models import ParsedClass, ParsedAttribute, ParsedRelationship, RelationshipType


def _rel_type_for_unmapped_instructor(
    rel: ParsedRelationship,
) -> int:
    """Return the mistake_id for an unmapped instructor relationship."""
    if rel.relationship_type == RelationshipType.INHERITANCE:
        return 10
    if rel.relationship_type in (
        RelationshipType.COMPOSITION,
        RelationshipType.AGGREGATION,
    ):
        return 15
    return 6


def _rel_type_for_unmapped_student(
    rel: ParsedRelationship,
) -> int:
    """Return the mistake_id for an unmapped student relationship."""
    if rel.relationship_type == RelationshipType.INHERITANCE:
        return 11
    if rel.relationship_type in (
        RelationshipType.COMPOSITION,
        RelationshipType.AGGREGATION,
    ):
        return 16
    return 7


@icontract.require(lambda mapping: isValidMapping(mapping))
@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.ensure(lambda result: isValidMistakes(result))
def checkMissing(
    mapping: ParsedMapping,
    instructor_model: ParsedModel,
    student_model: ParsedModel,
) -> List[ParsedMistake]:
    """Detect mistakes caused by unmatched (unmapped) model elements."""

    mistakes: List[ParsedMistake] = []

    # --- Unmapped instructor classes → mistake 1 ---
    for ic_name in mapping.class_mapping.unmapped_instructor_classes:
        mistakes.append(
            ParsedMistake(
                mistake_id=1,
                description=f"Missing class '{ic_name}'",
            )
        )

    # --- Unmapped student classes → mistake 2 ---
    for sc_name in mapping.class_mapping.unmapped_student_classes:
        mistakes.append(
            ParsedMistake(
                mistake_id=2,
                description=f"Extra class '{sc_name}'",
            )
        )

    # --- Unmapped instructor relationships ---
    for ir_idx in mapping.relationship_mapping.unmapped_instructor_relationships:
        rel = instructor_model.relationships[ir_idx]
        mid = _rel_type_for_unmapped_instructor(rel)
        desc_prefix = {
            10: "Missing inheritance",
            15: "Missing composition/aggregation",
            6: "Missing relationship",
        }
        mistakes.append(
            ParsedMistake(
                mistake_id=mid,
                description=(
                    f"{desc_prefix[mid]} between "
                    f"'{rel.source}' and '{rel.target}'"
                ),
            )
        )

    # --- Unmapped student relationships ---
    for sr_idx in mapping.relationship_mapping.unmapped_student_relationships:
        rel = student_model.relationships[sr_idx]
        mid = _rel_type_for_unmapped_student(rel)
        desc_prefix = {
            11: "Extra inheritance",
            16: "Extra composition/aggregation",
            7: "Extra relationship",
        }
        mistakes.append(
            ParsedMistake(
                mistake_id=mid,
                description=(
                    f"{desc_prefix[mid]} between "
                    f"'{rel.source}' and '{rel.target}'"
                ),
            )
        )

    # Sort deterministically by (mistake_id, description)
    mistakes.sort(key=lambda m: (m.mistake_id, m.description))

    return mistakes