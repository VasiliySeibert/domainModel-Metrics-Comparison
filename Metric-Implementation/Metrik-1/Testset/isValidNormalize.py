"""
Invariants checked by isValidNormalize:
1. result is a dict (MetricResult)
2. result contains exactly three keys: class_score, attribute_score, association_score
3. Every value is a float or int in the range [0.0, 1.0]
"""

from typing import Any, Dict


REQUIRED_KEYS = {"class_score", "attribute_score", "association_score"}


def isValidNormalize(result: Any) -> bool:
    """
    Validate that a normalization result adheres to the MetricResult
    structure required by the MetricInterface workflow.

    Checks:
    1) result is a dict
    2) result contains exactly the three required keys
    3) each value is a number in [0.0, 1.0]
    """
    if not isinstance(result, dict):
        return False

    if set(result.keys()) != REQUIRED_KEYS:
        return False

    for key in REQUIRED_KEYS:
        value = result[key]
        if not isinstance(value, (int, float)):
            return False
        if not (0.0 <= value <= 1.0):
            return False

    return True


if __name__ == "__main__":
    # --- Valid example ---
    valid = {
        "class_score": 0.75,
        "attribute_score": 0.5,
        "association_score": 1.0,
    }
    print("Valid normalize:", isValidNormalize(valid))  # True

    # --- Invalid: missing key ---
    invalid_missing = {
        "class_score": 0.9,
        "attribute_score": 0.8,
    }
    print("Missing key:", isValidNormalize(invalid_missing))  # False

    # --- Invalid: extra key ---
    invalid_extra = {
        "class_score": 0.9,
        "attribute_score": 0.8,
        "association_score": 0.7,
        "bonus": 0.5,
    }
    print("Extra key:", isValidNormalize(invalid_extra))  # False

    # --- Invalid: out of range ---
    invalid_range = {
        "class_score": 1.5,
        "attribute_score": 0.8,
        "association_score": 0.7,
    }
    print("Out of range:", isValidNormalize(invalid_range))  # False

    # --- Invalid: wrong type ---
    invalid_type = {
        "class_score": "good",
        "attribute_score": 0.8,
        "association_score": 0.7,
    }
    print("Wrong type:", isValidNormalize(invalid_type))  # False

    # --- Invalid: not a dict ---
    invalid_not_dict = [0.5, 0.6, 0.7]
    print("Not a dict:", isValidNormalize(invalid_not_dict))  # False
