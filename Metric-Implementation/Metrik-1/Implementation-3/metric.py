"""
metric — Orchestrates the Metrik-1 pipeline (normalized version).

Pipeline
--------
1. mapping = mapClasses(instructor_model, student_model)
2. mapping = mapRelationships(instructor_model, student_model, mapping)
3. mistakes  = checkClasses(mapping, instructor_model, student_model)
4. mistakes += checkRelations(mapping, instructor_model, student_model)
5. mistakes += checkMissing(mapping, instructor_model, student_model)
6. result = normalize(mistakes, instructor_model, student_model)
7. return result
"""

import icontract
import sys
from pathlib import Path
from typing import List

_D4 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_D4))
sys.path.insert(0, str(_D4 / "Implementation"))
sys.path.insert(0, str(_D4 / "Testset"))
sys.path.insert(0, str(_D4.parent.parent))  # workspace root for metric_interface

from metric_interface import MetricResult

from isValidModel import isValidModel, ParsedModel
from isValidMapping import isValidMapping, ParsedMapping
from isValidMistakes import isValidMistakes, ParsedMistake
from isValidNormalize import isValidNormalize

from mapClasses import mapClasses
from mapRelationships import mapRelationships
from checkClasses import checkClasses
from checkRelations import checkRelations
from checkMissing import checkMissing
from normalize import normalize


@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.ensure(lambda result: isValidNormalize(result))
def metric(
    instructor_model: ParsedModel,
    student_model: ParsedModel,
) -> MetricResult:
    """
    Compare an instructor domain model against a student domain model and
    return a normalized MetricResult with three scores in [0.0, 1.0].

    Pipeline
    --------
    1. mapping = mapClasses(instructor_model, student_model)
    2. mapping = mapRelationships(instructor_model, student_model, mapping)
    3. mistakes  = checkClasses(mapping, instructor_model, student_model)
    4. mistakes += checkRelations(mapping, instructor_model, student_model)
    5. mistakes += checkMissing(mapping, instructor_model, student_model)
    6. result = normalize(mistakes, instructor_model, student_model)
    7. return result

    requires:
        isValidModel(instructor_model)
        isValidModel(student_model)
    ensures:
        isValidNormalize(result)
    """
    mapping: ParsedMapping = mapClasses(instructor_model, student_model)
    mapping = mapRelationships(instructor_model, student_model, mapping)

    mistakes: List[ParsedMistake] = checkClasses(mapping, instructor_model, student_model)
    mistakes += checkRelations(mapping, instructor_model, student_model)
    mistakes += checkMissing(mapping, instructor_model, student_model)

    # Deduplicate exact (mistake_id, description) duplicates to satisfy
    # isValidMistakes invariant while keeping all unique mistake instances.
    seen: set = set()
    unique_mistakes: List[ParsedMistake] = []
    for m in mistakes:
        key = (m.mistake_id, m.description.strip())
        if key not in seen:
            seen.add(key)
            unique_mistakes.append(m)

    result: MetricResult = normalize(unique_mistakes, instructor_model, student_model)
    return result