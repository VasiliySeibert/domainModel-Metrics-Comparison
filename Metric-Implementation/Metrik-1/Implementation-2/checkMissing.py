import icontract
import sys
from pathlib import Path
from typing import List, Set, Tuple

_D4 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_D4))
sys.path.insert(0, str(_D4 / "Testset"))
sys.path.insert(0, str(_D4 / "Parser"))

from isValidModel import isValidModel, ParsedModel
from isValidMapping import isValidMapping, ParsedMapping
from isValidMistakes import isValidMistakes, ParsedMistake, KNOWN_MISTAKE_IDS
from models import RelationshipType


@icontract.require(lambda mapping: isValidMapping(mapping))
@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.ensure(lambda result: isValidMistakes(result))
def checkMissing(
    mapping: ParsedMapping, instructor_model: ParsedModel, student_model: ParsedModel
) -> List[ParsedMistake]:
    """
    mistakes = checkMissing(mapping, instructor_model, student_model):
       for each unmapped instructor class:          emit mistake 1
       for each unmapped student class:              emit mistake 2
       for each unmapped instructor relationship:
           if INHERITANCE:       emit mistake 10
           if COMPOSITION/AGG:   emit mistake 15
           else:                 emit mistake 6
       for each unmapped student relationship:
           if INHERITANCE:       emit mistake 11
           if COMPOSITION/AGG:   emit mistake 16
           else:                 emit mistake 7
       return mistakes
    """
    mistakes: List[ParsedMistake] = []

    for cls_name in mapping.class_mapping.unmapped_instructor_classes:
        mistakes.append(ParsedMistake(1, f"Missing class '{cls_name}'"))

    for cls_name in mapping.class_mapping.unmapped_student_classes:
        mistakes.append(ParsedMistake(2, f"Extra class '{cls_name}'"))

    for idx in mapping.relationship_mapping.unmapped_instructor_relationships:
        rel = instructor_model.relationships[idx]
        if rel.relationship_type == RelationshipType.INHERITANCE:
            mistakes.append(
                ParsedMistake(
                    10,
                    f"Missing inheritance relationship from '{rel.source}' to '{rel.target}'",
                )
            )
        elif rel.relationship_type in (RelationshipType.COMPOSITION, RelationshipType.AGGREGATION):
            mistakes.append(
                ParsedMistake(
                    15,
                    f"Missing composition/aggregation relationship from '{rel.source}' to '{rel.target}'",
                )
            )
        else:
            mistakes.append(
                ParsedMistake(
                    6,
                    f"Missing relationship from '{rel.source}' to '{rel.target}'",
                )
            )

    for idx in mapping.relationship_mapping.unmapped_student_relationships:
        rel = student_model.relationships[idx]
        if rel.relationship_type == RelationshipType.INHERITANCE:
            mistakes.append(
                ParsedMistake(
                    11,
                    f"Extra inheritance relationship from '{rel.source}' to '{rel.target}'",
                )
            )
        elif rel.relationship_type in (RelationshipType.COMPOSITION, RelationshipType.AGGREGATION):
            mistakes.append(
                ParsedMistake(
                    16,
                    f"Extra composition/aggregation relationship from '{rel.source}' to '{rel.target}'",
                )
            )
        else:
            mistakes.append(
                ParsedMistake(
                    7,
                    f"Extra relationship from '{rel.source}' to '{rel.target}'",
                )
            )

    return _deduplicate_and_sort(mistakes)


def _deduplicate_and_sort(mistakes: List[ParsedMistake]) -> List[ParsedMistake]:
    seen: Set[Tuple[int, str]] = set()
    result: List[ParsedMistake] = []
    for m in mistakes:
        key = (m.mistake_id, m.description.strip())
        if key not in seen:
            seen.add(key)
            result.append(m)
    result.sort(key=lambda m: (m.mistake_id, m.description))
    return result
