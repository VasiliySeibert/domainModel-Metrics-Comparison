import sys
from pathlib import Path

# Add parent directory (Metrik-1) to path so Parser module can be found
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Parser.models import (
    ParsedModel,
    ParsedClass,
    ParsedEnum,
    ParsedRelationship,
    RelationshipType,
)


def isValidModel(model: ParsedModel) -> bool:
    """
    Validate that a parsed model adheres to structural invariants.
    """
    # Check that model adheres to the ParsedModel dataclass structure
    if not isinstance(model, ParsedModel):
        return False

    # Check that every class in model.classes is a ParsedClass instance
    if not all(isinstance(c, ParsedClass) for c in model.classes):
        return False

    # Check that every enum in model.enums is a ParsedEnum instance
    if not all(isinstance(e, ParsedEnum) for e in model.enums):
        return False

    # Check that every relationship in model.relationships is a ParsedRelationship instance
    if not all(isinstance(r, ParsedRelationship) for r in model.relationships):
        return False

    # Invariant 1: class names are unique within M
    class_names = [c.name for c in model.classes]
    if len(class_names) != len(set(class_names)):
        return False

    # Invariant 2: enumeration names are unique within M (standalone + nested)
    all_enum_names = [e.name for e in model.enums] + [
        e.name for c in model.classes for e in c.nested_enums
    ]
    if len(all_enum_names) != len(set(all_enum_names)):
        return False

    # Invariant 3: every relation references explicitly defined classes that exist in M
    # explicit_names = set(class_names)
    # for rel in model.relationships:
    #     if rel.source not in explicit_names or rel.target not in explicit_names:
    #         return False

    # Invariant 4: every attribute belongs to exactly one class in M
    # Structurally guaranteed by the data model — attributes live inside ParsedClass,
    # so they cannot be orphaned as long as the ParsedClass instances are valid.

    return True


if __name__ == "__main__":
    from Parser import PlantUMLParser
    from example import student_model

    parser = PlantUMLParser(strict=True)
    parsed_student = parser.parse(student_model)

    print(isValidModel(parsed_student))
