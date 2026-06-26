"""
Invariants checked by isValidMapping
1. ParsedMapping and ClassMapping are valid instances
2. All items in mapped_classes are MappedClass instances
3. No student class is mapped twice
4. No instructor class is mapped twice (prevents double-counting)
5. No empty or None class names in mappings
6. No duplicates in unmapped_instructor_classes or unmapped_student_classes
7. No overlap between mapped and unmapped sets (a class can't be both mapped and unmapped)
8. Every MappedAttribute.student_attr is non-empty
9. RelationshipMapping is a valid instance
10. All items in mapped_relationships are MappedRelationship instances
11. No student_rel_index mapped twice, no instructor_rel_index mapped twice
12. No negative indices in mapped_relationships
13. No duplicates in unmapped_instructor_relationships / unmapped_student_relationships
14. No overlap between mapped and unmapped relationship index sets
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set
from enum import Enum


### MappingType
class MappingType(Enum):
    """The type of mapping between a student and an instructor element."""
    EXACT = "exact"               # Perfectly correct mapping
    RENAME = "rename"             # Student renamed the element
    SPLIT = "split"               # Student split one element into multiple
    MERGE = "merge"               # Student merged multiple elements into one
    MISSING = "missing"           # Student missed the element
    EXTRA = "extra"               # Student added an extra element
    TYPE_CHANGE = "type_change"   # Student changed a type
    CUSTOM = "custom"             # Other/uncategorized mapping


### MappedAttribute
@dataclass
class MappedAttribute:
    """Maps a student attribute to an instructor attribute."""
    student_attr: str
    instructor_attr: Optional[str] = None      # None if student attribute is unmapped (EXTRA)
    mapping_type: MappingType = MappingType.EXACT


### MappedAttributes
@dataclass
class MappedAttributes:
    """All mappings between two mapped classes."""
    mappings: List[MappedAttribute] = field(default_factory=list)


### MappedRelationship
@dataclass
class MappedRelationship:
    """Maps a student relationship to an instructor relationship."""
    student_rel_index: int              # Index into student model relationships
    instructor_rel_index: int           # Index into instructor model relationships
    mapping_type: MappingType = MappingType.EXACT
    is_inverted: bool = False           # Direction reversed


### MappedClass
@dataclass
class MappedClass:
    """Maps a student class to one or more instructor classes."""
    student_class: str
    instructor_classes: List[str]        # Can be multiple, e.g., split
    mapping_type: MappingType = MappingType.EXACT
    mapped_attributes: MappedAttributes = field(default_factory=MappedAttributes)


### ClassMapping
@dataclass
class ClassMapping:
    """
    The complete mapping between a student model and an instructor model
    at the class level.

    Contains:
    - mapped_classes: all mappings at class level
    - unmapped_instructor_classes: instructor classes the student did not map
    - unmapped_student_classes: student classes that have no counterpart
    """
    mapped_classes: List[MappedClass] = field(default_factory=list)
    unmapped_instructor_classes: List[str] = field(default_factory=list)
    unmapped_student_classes: List[str] = field(default_factory=list)


### RelationshipMapping
@dataclass
class RelationshipMapping:
    """
    The complete mapping between a student model and an instructor model
    at the relationship level.

    Contains:
    - mapped_relationships: all mapped relationship pairs
    - unmapped_instructor_relationships: indices of instructor rels with no match
    - unmapped_student_relationships: indices of student rels with no match
    """
    mapped_relationships: List[MappedRelationship] = field(default_factory=list)
    unmapped_instructor_relationships: List[int] = field(default_factory=list)
    unmapped_student_relationships: List[int] = field(default_factory=list)


### ParsedMapping
@dataclass
class ParsedMapping:
    """
    The complete mapping result.

    Contains:
    - class_mapping: ClassMapping with all class-level mappings
    - relationship_mapping: RelationshipMapping with all relationship-level mappings
    - raw_source: Optional reference to original submission
    """
    class_mapping: ClassMapping = field(default_factory=ClassMapping)
    relationship_mapping: RelationshipMapping = field(default_factory=RelationshipMapping)
    raw_source: str = ""


def isValidMapping(mapping: ParsedMapping) -> bool:
    """Validate that a mapping adheres to structural invariants."""
    if not isinstance(mapping, ParsedMapping):
        return False

    cm = mapping.class_mapping

    # Must be a ClassMapping
    if not isinstance(cm, ClassMapping):
        return False

    # Check all mapped_classes are MappedClass instances
    if not all(isinstance(m, MappedClass) for m in cm.mapped_classes):
        return False

    # Check mapped_attributes inside each MappedClass
    for mc in cm.mapped_classes:
        if not isinstance(mc.mapped_attributes, MappedAttributes):
            return False
        if not all(isinstance(a, MappedAttribute) for a in mc.mapped_attributes.mappings):
            return False

    # Invariant 1: every student class appears at most once
    student_class_names = [m.student_class for m in cm.mapped_classes]
    if len(student_class_names) != len(set(student_class_names)):
        return False

    # Invariant 2: no instructor class is mapped more than once
    all_instructor_classes = []
    for m in cm.mapped_classes:
        all_instructor_classes.extend(m.instructor_classes)
    if len(all_instructor_classes) != len(set(all_instructor_classes)):
        return False

    # Invariant 3: every mapped instructor class exists (i.e. not empty/None)
    if any(name == "" or name is None for name in all_instructor_classes):
        return False

    # Invariant 4: every mapped student class exists (i.e. not empty/None)
    if any(name == "" or name is None for name in student_class_names):
        return False

    # Invariant 5: unmapped class lists contain no duplicates
    if len(cm.unmapped_instructor_classes) != len(set(cm.unmapped_instructor_classes)):
        return False
    if len(cm.unmapped_student_classes) != len(set(cm.unmapped_student_classes)):
        return False

    # Invariant 6: no overlap between mapped and unmapped class sets
    mapped_instructor_set = set(all_instructor_classes)
    mapped_student_set = set(student_class_names)
    if mapped_instructor_set & set(cm.unmapped_instructor_classes):
        return False
    if mapped_student_set & set(cm.unmapped_student_classes):
        return False

    # Invariant 7: every MappedAttribute has a non-empty student_attr
    for mc in cm.mapped_classes:
        for attr_map in mc.mapped_attributes.mappings:
            if not attr_map.student_attr or attr_map.student_attr.strip() == "":
                return False

    # ------------------------------------------------------------------
    # Relationship-level invariants
    # ------------------------------------------------------------------
    rm = mapping.relationship_mapping

    # Invariant 9: rm is a RelationshipMapping
    if not isinstance(rm, RelationshipMapping):
        return False

    # Invariant 10: all mapped relationships are MappedRelationship instances
    if not all(isinstance(m, MappedRelationship) for m in rm.mapped_relationships):
        return False

    # Invariant 11: no student_rel_index mapped twice
    student_rel_indices = [m.student_rel_index for m in rm.mapped_relationships]
    if len(student_rel_indices) != len(set(student_rel_indices)):
        return False

    # Invariant 11b: no instructor_rel_index mapped twice
    instructor_rel_indices = [m.instructor_rel_index for m in rm.mapped_relationships]
    if len(instructor_rel_indices) != len(set(instructor_rel_indices)):
        return False

    # Invariant 12: no negative indices in mapped relationships
    if any(idx < 0 for idx in student_rel_indices + instructor_rel_indices):
        return False

    # Invariant 13: no duplicates in unmapped relationship lists
    if len(rm.unmapped_instructor_relationships) != len(set(rm.unmapped_instructor_relationships)):
        return False
    if len(rm.unmapped_student_relationships) != len(set(rm.unmapped_student_relationships)):
        return False

    # Invariant 14: no overlap between mapped and unmapped relationship index sets
    mapped_student_rel_set = set(student_rel_indices)
    mapped_instructor_rel_set = set(instructor_rel_indices)
    if mapped_student_rel_set & set(rm.unmapped_student_relationships):
        return False
    if mapped_instructor_rel_set & set(rm.unmapped_instructor_relationships):
        return False

    return True


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    from example import student_model, instructor_model
    from Parser import PlantUMLParser

    parser = PlantUMLParser(strict=True)
    parsed_student = parser.parse(student_model)
    parsed_instructor = parser.parse(instructor_model)

    ### Example mapping for testing
    mapping = ParsedMapping(
        class_mapping=ClassMapping(
            mapped_classes=[
                MappedClass(
                    student_class="PISystem",
                    instructor_classes=["PISystem"],
                    mapping_type=MappingType.EXACT,
                    mapped_attributes=MappedAttributes(mappings=[]),
                ),
                MappedClass(
                    student_class="Person",
                    instructor_classes=["Person"],
                    mapping_type=MappingType.EXACT,
                    mapped_attributes=MappedAttributes(
                        mappings=[
                            MappedAttribute("name", "name", MappingType.EXACT),
                            MappedAttribute("address", "address", MappingType.EXACT),
                        ]
                    ),
                ),
                MappedClass(
                    student_class="Victim",
                    instructor_classes=["Victim"],
                    mapping_type=MappingType.EXACT,
                ),
                MappedClass(
                    student_class="PoliceOfficer",
                    instructor_classes=["PoliceOfficer"],
                    mapping_type=MappingType.TYPE_CHANGE,
                    mapped_attributes=MappedAttributes(
                        mappings=[
                            MappedAttribute("badgeNumber", "badgeNumber", MappingType.TYPE_CHANGE),
                        ]
                    ),
                ),
                MappedClass(
                    student_class="PoliceStation",
                    instructor_classes=["PoliceStation"],
                    mapping_type=MappingType.EXACT,
                ),
                MappedClass(
                    student_class="Cases",
                    instructor_classes=["Case"],
                    mapping_type=MappingType.RENAME,
                    mapped_attributes=MappedAttributes(
                        mappings=[
                            MappedAttribute("objective", None, MappingType.EXTRA),
                            MappedAttribute("startDate", "startDate", MappingType.EXACT),
                        ]
                    ),
                ),
            ],
            unmapped_instructor_classes=["Role"],
            unmapped_student_classes=[],
        ),
        relationship_mapping=RelationshipMapping(
            mapped_relationships=[
                MappedRelationship(0, 0, MappingType.EXACT, False),
            ],
            unmapped_instructor_relationships=[],
            unmapped_student_relationships=[],
        ),
    )

    print(isValidMapping(mapping))  # Should print True
