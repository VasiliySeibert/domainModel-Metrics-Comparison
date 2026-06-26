import icontract
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Testset"))

from isValidModel import isValidModel, ParsedModel, ParsedRelationship
from isValidMapping import (
    isValidMapping,
    ParsedMapping,
    MappedRelationship,
    MappingType,
)
from isValidMistakes import isValidMistakes, ParsedMistake


@icontract.require(lambda mapping: isValidMapping(mapping))
@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.ensure(lambda result: isValidMistakes(result))
def checkRelations(
    mapping: ParsedMapping,
    instructor_model: ParsedModel,
    student_model: ParsedModel,
) -> List[ParsedMistake]:
    """
    Detect mistakes in mapped relationships.

    Checks performed
    ----------------
    1. Wrong relationship type
       – mapping_type of a MappedRelationship is TYPE_CHANGE.
       – mistake_id 14.

    2. Inverted relationship direction
       – MappedRelationship.is_inverted is True.
       – mistake_id 9.

    3. Wrong relationship cardinality
       – After resolving direction (exact vs. inverted), the
         source_cardinality and/or target_cardinality of the instructor
         relationship differ from the corresponding student values.
       – mistake_id 8.

    Parameters
    ----------
    mapping:
        The complete mapping (must contain a populated RelationshipMapping).
    instructor_model, student_model:
        Original parsed models (needed to look up cardinalities by index).

    Returns
    -------
    List[ParsedMistake]
    """
