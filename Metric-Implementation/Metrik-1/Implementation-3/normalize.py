import icontract
import re
import sys
from pathlib import Path
from typing import List, Set, Tuple

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


def _extract_affected_pairs(mistakes: List[ParsedMistake]) -> Set[Tuple[str, str]]:
    """
    Extract unique (source, target) class pairs affected by association mistakes.

    Descriptions follow patterns like:
        "Missing relationship between 'X' and 'Y'"
        "Wrong cardinality for relationship between 'X' and 'Y'"
        "Inverted relationship direction between 'X' and 'Y'"
    """
    pairs: Set[Tuple[str, str]] = set()
    # Match quoted identifiers after "between " and the second quoted identifier
    pattern = re.compile(r"between\s+'([^']+)'\s+and\s+'([^']+)'")
    for m in mistakes:
        if m.mistake_id in MISTAKE_GROUPS["association"]:
            match = pattern.search(m.description)
            if match:
                a, b = match.group(1), match.group(2)
                # Normalise order so (A,B) and (B,A) count as the same pair
                pair = tuple(sorted((a, b)))
                pairs.add(pair)
    return pairs


def _extract_affected_attrs(mistakes: List[ParsedMistake]) -> Set[Tuple[str, str]]:
    """
    Extract unique (class_name, attr_name) pairs affected by attribute mistakes.

    Descriptions follow patterns like:
        "Missing attribute 'X' in class 'Y'"
        "Extra attribute 'X' in class 'Y'"
        "Wrong type for attribute 'X' in class 'Y'"
    """
    pairs: Set[Tuple[str, str]] = set()
    patterns = [
        re.compile(r"attribute\s+'([^']+)'\s+.*in\s+class\s+'([^']+)"),
        re.compile(r"type\s+for\s+attribute\s+'([^']+)'\s+.*in\s+class\s+'([^']+)"),
    ]
    for m in mistakes:
        if m.mistake_id in MISTAKE_GROUPS["attribute"]:
            for pat in patterns:
                match = pat.search(m.description)
                if match:
                    attr_name, class_name = match.group(1), match.group(2)
                    pairs.add((class_name, attr_name))
                    break
    return pairs


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
    class_count = _count_mistakes(mistakes, MISTAKE_GROUPS["class"])
    attr_count = len(_extract_affected_attrs(mistakes))
    assoc_count = len(_extract_affected_pairs(mistakes))

    # Denominator = union of instructor and student elements
    denom_classes = max(1, len(instructor_model.classes) + len(student_model.classes))
    denom_attrs = max(
        1,
        sum(len(c.attributes) for c in instructor_model.classes)
        + sum(len(c.attributes) for c in student_model.classes),
    )
    denom_assocs = max(
        1,
        len(instructor_model.relationships) + len(student_model.relationships),
    )

    class_score = max(0.0, 1.0 - class_count / denom_classes)
    attribute_score = max(0.0, 1.0 - attr_count / denom_attrs)
    association_score = max(0.0, 1.0 - assoc_count / denom_assocs)

    return MetricResult(
        class_score=class_score,
        attribute_score=attribute_score,
        association_score=association_score,
    )
