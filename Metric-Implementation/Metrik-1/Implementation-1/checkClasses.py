"""
checkClasses — Detect class/attribute mistakes.

Checks performed
----------------
1. Renamed class  – mapping_type == RENAME → mistake_id 12
2. Missing attribute – instructor attr not in mapped attributes → mistake_id 3
3. Extra attribute  – MappedAttribute with mapping_type EXTRA → mistake_id 4
4. Wrong attribute type – matched name but different ParsedAttribute.type → mistake_id 5
5. Renamed attribute – instructor_attr != student_attr (both non-None) → mistake_id 13
"""

import icontract
import sys
from pathlib import Path
from typing import List, Optional

_D4 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_D4))
sys.path.insert(0, str(_D4 / "Testset"))
sys.path.insert(0, str(_D4 / "Parser"))

from isValidModel import isValidModel, ParsedModel
from isValidMapping import (
    isValidMapping,
    ParsedMapping,
    MappedClass,
    MappedAttribute,
    MappingType,
)
from isValidMistakes import isValidMistakes, ParsedMistake
from models import ParsedClass, ParsedAttribute, ParsedRelationship, RelationshipType


def _find_class(model: ParsedModel, name: str) -> Optional[ParsedClass]:
    """Look up a class by name in a parsed model."""
    for c in model.classes:
        if c.name == name:
            return c
    return None


def _check_class(
    mc: MappedClass,
    instructor_model: ParsedModel,
    student_model: ParsedModel,
    mistakes: List[ParsedMistake],
) -> None:
    """Check a single mapped-class pair for mistakes and append them to *mistakes*."""

    # 1. Renamed class
    if mc.mapping_type == MappingType.RENAME:
        ic_name = mc.instructor_classes[0] if mc.instructor_classes else "?"
        mistakes.append(
            ParsedMistake(
                mistake_id=12,
                description=f"Class '{ic_name}' renamed to '{mc.student_class}'",
            )
        )

    # Look up the actual class objects for attribute-type comparison
    ic = _find_class(instructor_model, mc.instructor_classes[0]) if mc.instructor_classes else None
    sc = _find_class(student_model, mc.student_class)

    # Build lookup dicts for attribute types
    ic_attr_types = {a.name: a.type for a in ic.attributes} if ic else {}
    sc_attr_types = {a.name: a.type for a in sc.attributes} if sc else {}

    # Collect which instructor attributes have been matched in the mapping
    matched_instructor_attrs = set()
    matched_student_attrs = set()

    for ma in mc.mapped_attributes.mappings:
        matched_student_attrs.add(ma.student_attr)

        if ma.mapping_type == MappingType.EXTRA:
            # 3. Extra attribute
            mistakes.append(
                ParsedMistake(
                    mistake_id=4,
                    description=f"Extra attribute '{ma.student_attr}' in class '{mc.student_class}'",
                )
            )
            continue

        if ma.instructor_attr is not None:
            matched_instructor_attrs.add(ma.instructor_attr)

            # 5. Renamed attribute
            if ma.student_attr != ma.instructor_attr:
                mistakes.append(
                    ParsedMistake(
                        mistake_id=13,
                        description=(
                            f"Attribute '{ma.instructor_attr}' renamed to "
                            f"'{ma.student_attr}' in class '{mc.student_class}'"
                        ),
                    )
                )

            # 4. Wrong attribute type
            ic_type = ic_attr_types.get(ma.instructor_attr)
            sc_type = sc_attr_types.get(ma.student_attr)
            # Both must have a type, and they must differ
            # Also consider the case where one has a type and the other doesn't
            if ic_type != sc_type:
                # Only report if at least one side has a type (to avoid
                # false positives when both are None)
                if ic_type is not None or sc_type is not None:
                    ic_type_str = ic_type if ic_type else "None"
                    sc_type_str = sc_type if sc_type else "None"
                    mistakes.append(
                        ParsedMistake(
                            mistake_id=5,
                            description=(
                                f"Wrong type for attribute '{ma.student_attr}' "
                                f"in class '{mc.student_class}': "
                                f"expected '{ic_type_str}', got '{sc_type_str}'"
                            ),
                        )
                    )

    # 2. Missing instructor attributes (not matched in mapping at all)
    if ic:
        for attr in ic.attributes:
            if attr.name not in matched_instructor_attrs:
                mistakes.append(
                    ParsedMistake(
                        mistake_id=3,
                        description=(
                            f"Missing attribute '{attr.name}' "
                            f"in class '{mc.student_class}'"
                        ),
                    )
                )


@icontract.require(lambda mapping: isValidMapping(mapping))
@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.ensure(lambda result: isValidMistakes(result))
def checkClasses(
    mapping: ParsedMapping,
    instructor_model: ParsedModel,
    student_model: ParsedModel,
) -> List[ParsedMistake]:
    """Detect mistakes in mapped classes and their attributes."""

    mistakes: List[ParsedMistake] = []

    for mc in mapping.class_mapping.mapped_classes:
        _check_class(mc, instructor_model, student_model, mistakes)

    # Sort deterministically by (mistake_id, description)
    mistakes.sort(key=lambda m: (m.mistake_id, m.description))

    return mistakes