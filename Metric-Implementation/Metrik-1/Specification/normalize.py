import icontract
import sys
from pathlib import Path
from typing import List

# ------------------------------------------------------------------
# Path setup so that the metric root, Implementation and Testset resolve
# ------------------------------------------------------------------
_D4 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_D4))
sys.path.insert(0, str(_D4 / "Testset"))
sys.path.insert(0, str(_D4.parent.parent))  # workspace root for metric_interface

from metric_interface import MetricResult

from isValidModel import isValidModel, ParsedModel
from isValidMistakes import isValidMistakes, ParsedMistake
from isValidNormalize import isValidNormalize


MISTAKE_GROUPS = {
    "class": {1, 2, 12},
    "attribute": {3, 4, 5, 13},
    "association": {6, 7, 8, 9, 10, 11, 14, 15, 16},
}


def _count_mistakes(mistakes: List[ParsedMistake], group: set) -> int:
    """Count how many mistakes belong to the given group of mistake IDs."""
    return sum(1 for m in mistakes if m.mistake_id in group)


@icontract.require(lambda mistakes: isValidMistakes(mistakes))
@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.ensure(lambda result: isValidNormalize(result))
def normalize(
    mistakes: List[ParsedMistake],
    instructor_model: ParsedModel,
    student_model: ParsedModel,
) -> MetricResult:
    """
    Convert a list of detected mistakes into three 0.0–1.0 similarity
    scores suitable for the MetricInterface workflow.

    Changes from the original specification:
    1. Denominator = sum of instructor + student elements (union size).
    2. Association mistakes count unique affected class pairs, not raw
       error messages (prevents triple-counting one relationship with
       wrong type + inverted + wrong cardinality).
    3. Attribute mistakes count unique (class, attr_name) pairs to
       avoid double-counting an attribute that is both extra and has
       a wrong type.

    Parameters
    ----------
    mistakes:
        Validated list of ParsedMistake objects from the check stages.
    instructor_model:
        The reference (ground-truth) parsed domain model.
    student_model:
        The student's parsed domain model.

    Returns
    -------
    MetricResult
        A typed dictionary with three keys:
        - class_score       : float in [0.0, 1.0]
        - attribute_score   : float in [0.0, 1.0]
        - association_score : float in [0.0, 1.0]
    """