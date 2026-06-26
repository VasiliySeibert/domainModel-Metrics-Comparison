"""
checkRelations — Detect relationship mistakes.

Checks performed
----------------
1. Wrong relationship type – mapping_type == TYPE_CHANGE → mistake_id 14
2. Inverted relationship direction – is_inverted == True → mistake_id 9
3. Wrong relationship cardinality – cardinalities differ after direction resolve → mistake_id 8
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
    MappedRelationship,
    MappingType,
)
from isValidMistakes import isValidMistakes, ParsedMistake
from models import ParsedClass, ParsedAttribute, ParsedRelationship, RelationshipType


@icontract.require(lambda mapping: isValidMapping(mapping))
@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.ensure(lambda result: isValidMistakes(result))
def checkRelations(
    mapping: ParsedMapping,
    instructor_model: ParsedModel,
    student_model: ParsedModel,
) -> List[ParsedMistake]:
    """Detect mistakes in mapped relationships."""

    mistakes: List[ParsedMistake] = []

    for mr in mapping.relationship_mapping.mapped_relationships:
        ir = instructor_model.relationships[mr.instructor_rel_index]
        sr = student_model.relationships[mr.student_rel_index]

        # 1. Wrong relationship type
        if mr.mapping_type == MappingType.TYPE_CHANGE:
            mistakes.append(
                ParsedMistake(
                    mistake_id=14,
                    description=(
                        f"Wrong relationship type between '{ir.source}' and "
                        f"'{ir.target}': expected '{ir.relationship_type.value}', "
                        f"got '{sr.relationship_type.value}'"
                    ),
                )
            )

        # 2. Inverted relationship direction
        if mr.is_inverted:
            mistakes.append(
                ParsedMistake(
                    mistake_id=9,
                    description=(
                        f"Inverted relationship direction between "
                        f"'{ir.source}' and '{ir.target}'"
                    ),
                )
            )

        # 3. Wrong relationship cardinality
        # Resolve direction: if inverted, compare ir.src↔sr.tgt and ir.tgt↔sr.src
        if mr.is_inverted:
            src_match = ir.source_cardinality == sr.target_cardinality
            tgt_match = ir.target_cardinality == sr.source_cardinality
        else:
            src_match = ir.source_cardinality == sr.source_cardinality
            tgt_match = ir.target_cardinality == sr.target_cardinality

        if not src_match or not tgt_match:
            # Build a readable cardinality description
            if mr.is_inverted:
                expected = f"({ir.source_cardinality}, {ir.target_cardinality})"
                got = f"({sr.target_cardinality}, {sr.source_cardinality})"
            else:
                expected = f"({ir.source_cardinality}, {ir.target_cardinality})"
                got = f"({sr.source_cardinality}, {sr.target_cardinality})"
            mistakes.append(
                ParsedMistake(
                    mistake_id=8,
                    description=(
                        f"Wrong cardinality for relationship between "
                        f"'{ir.source}' and '{ir.target}': "
                        f"expected {expected}, got {got}"
                    ),
                )
            )

    # Sort deterministically by (mistake_id, description)
    mistakes.sort(key=lambda m: (m.mistake_id, m.description))

    return mistakes