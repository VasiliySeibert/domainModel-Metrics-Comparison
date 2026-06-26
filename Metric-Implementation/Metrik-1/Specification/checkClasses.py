import icontract
import sys
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Testset"))

from isValidModel import isValidModel, ParsedModel, ParsedClass
from Parser.models import ParsedAttribute
from isValidMapping import (
    isValidMapping,
    ParsedMapping,
    MappedClass,
    MappedAttribute,
    MappingType,
)
from isValidMistakes import isValidMistakes, ParsedMistake


@icontract.require(lambda mapping: isValidMapping(mapping))
@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.ensure(lambda result: isValidMistakes(result))
def checkClasses(
    mapping: ParsedMapping,
    instructor_model: ParsedModel,
    student_model: ParsedModel,
) -> List[ParsedMistake]:
    """
    Detect mistakes in mapped classes and their attributes.

    Checks performed
    ----------------
    1. Renamed class
       – mapping_type of a MappedClass is RENAME.
       – mistake_id 12.

    2. Missing attribute
       – an instructor attribute that does not appear in the
         MappedAttributes of the corresponding MappedClass.
       – mistake_id 3.

    3. Extra attribute
       – a MappedAttribute with mapping_type EXTRA
         (i.e. instructor_attr is None).
       – mistake_id 4.

    4. Wrong attribute type
       – an attribute that is matched (instructor_attr == student_attr)
         but the ParsedAttribute.type values differ between the
         instructor and student class.
       – mistake_id 5.

    5. Renamed attribute
       – instructor_attr != student_attr while both are non-None.
         (Currently the attribute-mapping phase only performs exact
         name matches, so this branch is reserved for future
         fuzzy attribute matching.)
       – mistake_id 13.

    Parameters
    ----------
    mapping:
        The complete mapping produced by mapClasses (and optionally
        mapRelationships).
    instructor_model, student_model:
        The original parsed models (needed to look up actual attribute
        types for "wrong attribute type" checks).

    Returns
    -------
    List[ParsedMistake]
        One entry per detected mistake.  The list may contain multiple
        entries with the same mistake_id because a student can have
        several missing classes, extra attributes, etc.
    """
    


