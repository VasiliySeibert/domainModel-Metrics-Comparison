"""
Test for isValidParsedModel (formerly isValidModel)

Reuses the canonical isValidParsedModel implementation from
Testset.metric_invariants against real parser output.
"""

import sys
from pathlib import Path

# Add parent directory (Metrik-5) to path so Parser module can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Testset.metric_invariants import isValidParsedModel
from Parser import PlantUMLParser
from Parser.example import student_model


def test_isValidParsedModel_real_model():
    """
    Parse the example student model and assert that isValidParsedModel
    reports it as structurally valid.
    """
    parser = PlantUMLParser(strict=True)
    parsed_student = parser.parse(student_model)
    print(isValidParsedModel(parsed_student))


if __name__ == "__main__":
    test_isValidParsedModel_real_model()
