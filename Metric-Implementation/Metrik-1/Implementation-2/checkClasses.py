import icontract
import sys
from pathlib import Path
from typing import List, Set

_D4 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_D4))
sys.path.insert(0, str(_D4 / "Testset"))
sys.path.insert(0, str(_D4 / "Parser"))

from isValidModel import isValidModel, ParsedModel
from isValidMapping import isValidMapping, ParsedMapping, MappedClass, MappingType
from isValidMistakes import isValidMistakes, ParsedMistake, KNOWN_MISTAKE_IDS
from models import ParsedClass, ParsedAttribute


@icontract.require(lambda mapping: isValidMapping(mapping))
@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.ensure(lambda result: isValidMistakes(result))
def checkClasses(
    mapping: ParsedMapping, instructor_model: ParsedModel, student_model: ParsedModel
) -> List[ParsedMistake]:
    """
    mistakes = checkClasses(mapping, instructor_model, student_model):
       for each mapped class pair:
           if mapping_type == RENAME:        emit mistake 12
           for each missing instructor attribute: emit mistake 3
           for each extra student attribute:      emit mistake 4
           for each renamed attribute:          emit mistake 13
           for each wrong attribute type:       emit mistake 5
       return mistakes
    """
    mistakes: List[ParsedMistake] = []

    for mc in mapping.class_mapping.mapped_classes:
        student_cls = student_model.get_class(mc.student_class)
        if not mc.instructor_classes:
            continue
        instructor_cls = instructor_model.get_class(mc.instructor_classes[0])
        if student_cls is None or instructor_cls is None:
            continue

        if mc.mapping_type == MappingType.RENAME:
            mistakes.append(
                ParsedMistake(
                    12,
                    f"Student renamed class '{mc.instructor_classes[0]}' to '{mc.student_class}'",
                )
            )

        s_attr_by_name = {a.name: a for a in student_cls.attributes}
        i_attr_by_name = {a.name: a for a in instructor_cls.attributes}

        covered_i_attrs: Set[str] = set()

        for attr_map in mc.mapped_attributes.mappings:
            if attr_map.instructor_attr is None:
                mistakes.append(
                    ParsedMistake(
                        4,
                        f"Extra attribute '{attr_map.student_attr}' in class '{mc.student_class}'",
                    )
                )
            else:
                covered_i_attrs.add(attr_map.instructor_attr)
                if attr_map.mapping_type == MappingType.RENAME:
                    mistakes.append(
                        ParsedMistake(
                            13,
                            f"Student renamed attribute '{attr_map.instructor_attr}' to "
                            f"'{attr_map.student_attr}' in class '{mc.student_class}'",
                        )
                    )
                elif attr_map.mapping_type == MappingType.TYPE_CHANGE:
                    s_type = s_attr_by_name.get(attr_map.student_attr, ParsedAttribute(attr_map.student_attr)).type
                    i_type = i_attr_by_name.get(attr_map.instructor_attr, ParsedAttribute(attr_map.instructor_attr)).type
                    mistakes.append(
                        ParsedMistake(
                            5,
                            f"Wrong type for attribute '{attr_map.student_attr}' in class "
                            f"'{mc.student_class}': student has '{s_type or 'unspecified'}', "
                            f"instructor expects '{i_type or 'unspecified'}'",
                        )
                    )

        for i_attr in instructor_cls.attributes:
            if i_attr.name not in covered_i_attrs:
                mistakes.append(
                    ParsedMistake(
                        3,
                        f"Missing attribute '{i_attr.name}' in class '{mc.student_class}'",
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
