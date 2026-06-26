import icontract
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Testset"))

from Parser.models import RelationshipType
from isValidModel import isValidModel, ParsedModel
from isValidMapping import (
    isValidMapping,
    ParsedMapping,
)
from isValidMistakes import isValidMistakes, ParsedMistake


@icontract.require(lambda mapping: isValidMapping(mapping))
@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.ensure(lambda result: isValidMistakes(result))
def checkMissing(
    mapping: ParsedMapping,
    instructor_model: ParsedModel,
    student_model: ParsedModel,
) -> List[ParsedMistake]:
    """
    Detect mistakes caused by unmatched (unmapped) model elements.

    An element that appears in the instructor model but has no counterpart
    in the student model is considered *missing*.  Conversely, an element
    that appears in the student model but has no counterpart in the
    instructor model is considered *extra*.

    The relationship type determines which mistake-id is emitted:

    Instructor unmapped relationship
    --------------------------------
    • INHERITANCE  → mistake_id 10  (Missing inheritance)
    • COMPOSITION or AGGREGATION
                     → mistake_id 15  (Missing composition/aggregation)
    • otherwise    → mistake_id 6   (Missing relationship)

    Student unmapped relationship
    ---------------------------
    • INHERITANCE  → mistake_id 11  (Extra inheritance)
    • COMPOSITION or AGGREGATION
                     → mistake_id 16  (Extra composition/aggregation)
    • otherwise    → mistake_id 7   (Extra relationship)

    Unmapped classes
    ----------------
    • Instructor class → mistake_id 1 (Missing class)
    • Student  class   → mistake_id 2 (Extra class)

    Parameters
    ----------
    mapping:
        The complete mapping produced by earlier pipeline stages.
    instructor_model, student_model:
        Original parsed models (needed to resolve relationship types for
        unmapped indices).

    Returns
    -------
    List[ParsedMistake]
    """
    
