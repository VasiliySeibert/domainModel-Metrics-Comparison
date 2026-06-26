"""
Invariants checked by isValidMistakes:
1. Input is a list
2. Every item is a ParsedMistake instance
3. Every mistake_id is in the KNOWN_MISTAKE_IDS set
4. Every description is a non-empty string (after strip())
5. No duplicate mistake_ids in the list
"""


from dataclasses import dataclass
from typing import List


### Known mistake IDs (from Table 2)
# These are the mistake types the metric recognises.
KNOWN_MISTAKE_IDS = {
    1,   # Missing class
    2,   # Extra class
    3,   # Missing attribute
    4,   # Extra attribute
    5,   # Wrong attribute type
    6,   # Missing relationship
    7,   # Extra relationship
    8,   # Wrong relationship cardinality
    9,   # Inverted relationship direction
    10,  # Missing inheritance
    11,  # Extra inheritance
    12,  # Renamed class
    13,  # Renamed attribute
    14,  # Wrong relationship type
    15,  # Missing composition/aggregation
    16,  # Extra composition/aggregation
}


@dataclass
class ParsedMistake:
    """
    Represents one mistake identified in a student submission.

    Fields:
        mistake_id   -- int from the known mistake taxonomy (Table 2)
        description  -- human-readable description of the mistake
    """
    mistake_id: int
    description: str


def isValidMistakes(mistakes: List[ParsedMistake]) -> bool:
    """
    Validate that a list of mistakes adheres to structural invariants.

    Checks:
    1) mistakes is a list
    2) every item is a ParsedMistake instance
    3) every mistake_id is a known ID from Table 2
    4) every description is a non-empty string
    5) no duplicate mistake_ids exist within the list
    """
    # Must be a list
    if not isinstance(mistakes, list):
        return False

    # Check every item is a ParsedMistake
    if not all(isinstance(m, ParsedMistake) for m in mistakes):
        return False

    ids_seen: set = set()
    for m in mistakes:
        # Known mistake ID
        if m.mistake_id not in KNOWN_MISTAKE_IDS:
            return False

        # Non-empty description
        desc = m.description.strip() if isinstance(m.description, str) else ""
        if not desc:
            return False

        # No duplicate (mistake_id, description) pairs
        key = (m.mistake_id, desc)
        if key in ids_seen:
            return False
        ids_seen.add(key)

    return True


if __name__ == "__main__":
    # --- Valid example ---
    valid_mistakes = [
        ParsedMistake(1, "Student missed the 'Role' class"),
        ParsedMistake(12, "Student renamed 'Case' to 'Cases'"),
        ParsedMistake(5, "Wrong type for badgeNumber: String instead of int"),
    ]
    print("Valid mistakes:", isValidMistakes(valid_mistakes))   # True

    # --- Invalid: unknown ID ---
    invalid_unknown = [
        ParsedMistake(99, "Unknown mistake type"),
    ]
    print("Unknown ID:", isValidMistakes(invalid_unknown))       # False

    # --- Invalid: duplicate IDs ---
    invalid_dup = [
        ParsedMistake(1, "Missing class A"),
        ParsedMistake(1, "Missing class B"),
    ]
    print("Duplicate IDs:", isValidMistakes(invalid_dup))        # False

    # --- Invalid: empty description ---
    invalid_desc = [
        ParsedMistake(2, "   "),
    ]
    print("Empty desc:", isValidMistakes(invalid_desc))          # False
