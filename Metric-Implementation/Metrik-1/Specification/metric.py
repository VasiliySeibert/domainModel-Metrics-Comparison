import icontract
import sys
from pathlib import Path
from typing import List

# ------------------------------------------------------------------
# Path setup so that the metric root, Implementation and Testset resolve
# ------------------------------------------------------------------
_D4 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_D4))
sys.path.insert(0, str(_D4 / "Implementation"))
sys.path.insert(0, str(_D4 / "Testset"))

from isValidModel import isValidModel, ParsedModel
from isValidMapping import isValidMapping, ParsedMapping
from isValidMistakes import isValidMistakes, ParsedMistake

from mapClasses import mapClasses
from mapRelationships import mapRelationships
from checkClasses import checkClasses
from checkRelations import checkRelations
from checkMissing import checkMissing


@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.ensure(lambda result: isValidMistakes(result))
def metric(
    instructor_model: ParsedModel,
    student_model: ParsedModel,
) -> List[ParsedMistake]:
    """
    Compare an instructor domain model against a student domain model and
    return the list of detected modeling mistakes.

    Pipeline
    --------
    1. mapping = mapClasses(instructor_model, student_model)
    2. mapping = mapRelationships(instructor_model, student_model, mapping)
    3. mistakes  = checkClasses(mapping, instructor_model, student_model)
    4. mistakes += checkRelations(mapping, instructor_model, student_model)
    5. mistakes += checkMissing(mapping, instructor_model, student_model)
    6. return mistakes

    requires:
        isValidModel(instructor_model)
        isValidModel(student_model)
    ensures:
        isValidMistakes(result)
    """
    mapping: ParsedMapping = mapClasses(instructor_model, student_model)
    mapping = mapRelationships(instructor_model, student_model, mapping)

    mistakes: List[ParsedMistake] = checkClasses(mapping, instructor_model, student_model)
    mistakes += checkRelations(mapping, instructor_model, student_model)
    mistakes += checkMissing(mapping, instructor_model, student_model)

    return mistakes
