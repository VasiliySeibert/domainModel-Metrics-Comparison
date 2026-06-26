import icontract
import sys
from pathlib import Path
from typing import List, Set, Tuple

_D4 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_D4))
sys.path.insert(0, str(_D4 / "Testset"))
sys.path.insert(0, str(_D4 / "Parser"))

from isValidModel import isValidModel, ParsedModel
from isValidMapping import isValidMapping, ParsedMapping, MappedRelationship, MappingType
from isValidMistakes import isValidMistakes, ParsedMistake, KNOWN_MISTAKE_IDS
from models import ParsedRelationship


@icontract.require(lambda mapping: isValidMapping(mapping))
@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.ensure(lambda result: isValidMistakes(result))
def checkRelations(
    mapping: ParsedMapping, instructor_model: ParsedModel, student_model: ParsedModel
) -> List[ParsedMistake]:
    """
    mistakes = checkRelations(mapping, instructor_model, student_model):
       for each mapped relationship pair:
           if mapping_type == TYPE_CHANGE:     emit mistake 14
           if is_inverted == True:             emit mistake 9
           if cardinalities differ:             emit mistake 8
       return mistakes
    """
    mistakes: List[ParsedMistake] = []

    for mr in mapping.relationship_mapping.mapped_relationships:
        s_rel = student_model.relationships[mr.student_rel_index]
        i_rel = instructor_model.relationships[mr.instructor_rel_index]

        if mr.mapping_type == MappingType.TYPE_CHANGE:
            mistakes.append(
                ParsedMistake(
                    14,
                    f"Wrong relationship type between '{i_rel.source}' and '{i_rel.target}': "
                    f"student has '{s_rel.relationship_type.value}', "
                    f"instructor expects '{i_rel.relationship_type.value}'",
                )
            )

        if mr.is_inverted:
            mistakes.append(
                ParsedMistake(
                    9,
                    f"Inverted relationship direction between '{i_rel.source}' and '{i_rel.target}'",
                )
            )

        if (
            s_rel.source_cardinality != i_rel.source_cardinality
            or s_rel.target_cardinality != i_rel.target_cardinality
        ):
            mistakes.append(
                ParsedMistake(
                    8,
                    f"Wrong cardinality for relationship between '{i_rel.source}' and '{i_rel.target}'",
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
