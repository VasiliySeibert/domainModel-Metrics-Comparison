"""
mapClasses — Class mapping: greedy name match, then greedy attribute match.

Algorithm
---------
1. Initialise every class in both models as *unmatched*.
2. Stage 1 – Name-driven matching (HIGH/MEDIUM tiers, then LOW tier).
3. Stage 2 – Attribute-driven matching.
4. Remainders → unmapped lists.
5. Return the mapping wrapped in a ParsedMapping.
"""

import icontract
import sys
from pathlib import Path
from typing import List, Set, Tuple

_D4 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_D4))
sys.path.insert(0, str(_D4 / "Testset"))

from isValidModel import isValidModel, ParsedModel
from isValidMapping import (
    isValidMapping,
    ParsedMapping,
    ClassMapping,
    MappedClass,
    MappingType,
    MappedAttributes,
    MappedAttribute,
)
from Parser.models import ParsedClass, ParsedAttribute, ParsedRelationship, RelationshipType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def levenshtein_distance(a: str, b: str) -> int:
    """Classic DP implementation using O(min(m,n)) space."""
    m, n = len(a), len(b)
    if m < n:
        return levenshtein_distance(b, a)
    previous = list(range(n + 1))
    current = [0] * (n + 1)
    for i in range(1, m + 1):
        current[0] = i
        ai = a[i - 1]
        for j in range(1, n + 1):
            cost = 0 if ai == b[j - 1] else 1
            current[j] = min(
                current[j - 1] + 1,
                previous[j] + 1,
                previous[j - 1] + cost,
            )
        previous, current = current, previous
    return previous[n]


def _attribute_overlap(ic: ParsedClass, sc: ParsedClass) -> float:
    """
    Percentage of ic's attributes whose name occurs in sc.
    Returns 0.0 when ic has no attributes to avoid division by zero.
    """
    if not ic.attributes:
        return 0.0
    sc_names = {a.name for a in sc.attributes}
    matches = sum(1 for a in ic.attributes if a.name in sc_names)
    return (matches / len(ic.attributes)) * 100.0


def _name_tier(ic_name: str, sc_name: str) -> str:
    """Return 'HIGH', 'MEDIUM', 'LOW', or 'NONE' for a class-name pair."""
    dist = levenshtein_distance(ic_name, sc_name)
    if dist == 0:
        return "HIGH"
    if 1 <= dist <= 2:
        return "MEDIUM"
    # LOW: one name is a strict substring of the other
    if ic_name in sc_name or sc_name in ic_name:
        return "LOW"
    return "NONE"


def _build_attribute_mappings(
    ic: ParsedClass, sc: ParsedClass
) -> MappedAttributes:
    """
    Build attribute-level mappings between a matched instructor and
    student class.

    - Exact name matches → EXACT
    - Remaining student attrs with no instructor match → EXTRA
    - Remaining instructor attrs with no student match → not emitted here
      (they will be detected as mistake 3 by checkClasses)
    - For any matched pair where names differ but both are non-None → RENAME
      (reserved for future fuzzy attribute matching; current implementation
       only does exact name matches, so this branch won't fire)
    """
    sc_matched: Set[str] = set()
    mappings: List[MappedAttribute] = []

    # Pass 1: exact name matches
    ic_attr_by_name = {a.name: a for a in ic.attributes}
    sc_attr_by_name = {a.name: a for a in sc.attributes}

    common_names = set(ic_attr_by_name.keys()) & set(sc_attr_by_name.keys())
    for name in sorted(common_names):
        mappings.append(
            MappedAttribute(
                student_attr=name,
                instructor_attr=name,
                mapping_type=MappingType.EXACT,
            )
        )
        sc_matched.add(name)

    # Pass 2: student attributes with no match → EXTRA
    for attr in sc.attributes:
        if attr.name not in sc_matched:
            mappings.append(
                MappedAttribute(
                    student_attr=attr.name,
                    instructor_attr=None,
                    mapping_type=MappingType.EXTRA,
                )
            )

    return MappedAttributes(mappings=mappings)


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.ensure(lambda result: isValidMapping(result))
def mapClasses(
    instructor_model: ParsedModel,
    student_model: ParsedModel,
) -> ParsedMapping:
    """Map instructor classes to student classes using a two-stage greedy
    algorithm.  See module docstring for full algorithm description."""

    ic_list = list(instructor_model.classes)
    sc_list = list(student_model.classes)

    matched_ic: Set[str] = set()   # instructor class names already matched
    matched_sc: Set[str] = set()   # student class names already matched
    mapped_classes: List[MappedClass] = []

    # ------------------------------------------------------------------
    # Stage 1: Name-driven matching — HIGH and MEDIUM tiers
    # ------------------------------------------------------------------
    high_med_candidates: List[Tuple[int, float, str, str, ParsedClass, ParsedClass]] = []
    for ic in ic_list:
        for sc in sc_list:
            tier = _name_tier(ic.name, sc.name)
            if tier in ("HIGH", "MEDIUM"):
                dist = levenshtein_distance(ic.name, sc.name)
                overlap = _attribute_overlap(ic, sc)
                # sort: distance asc, overlap desc, sc name asc, ic name asc
                high_med_candidates.append(
                    (dist, -overlap, sc.name, ic.name, ic, sc)
                )

    high_med_candidates.sort(key=lambda t: (t[0], t[1], t[2], t[3]))

    for dist, neg_overlap, sc_name, ic_name, ic, sc in high_med_candidates:
        if ic.name not in matched_ic and sc.name not in matched_sc:
            mapping_type = MappingType.EXACT if dist == 0 else MappingType.RENAME
            attr_mappings = _build_attribute_mappings(ic, sc)
            mapped_classes.append(
                MappedClass(
                    student_class=sc.name,
                    instructor_classes=[ic.name],
                    mapping_type=mapping_type,
                    mapped_attributes=attr_mappings,
                )
            )
            matched_ic.add(ic.name)
            matched_sc.add(sc.name)

    # ------------------------------------------------------------------
    # Stage 1b: Name-driven matching — LOW tier (substring match)
    # ------------------------------------------------------------------
    low_candidates: List[Tuple[int, float, str, str, ParsedClass, ParsedClass]] = []
    for ic in ic_list:
        for sc in sc_list:
            tier = _name_tier(ic.name, sc.name)
            if tier == "LOW":
                dist = levenshtein_distance(ic.name, sc.name)
                overlap = _attribute_overlap(ic, sc)
                low_candidates.append(
                    (dist, -overlap, sc.name, ic.name, ic, sc)
                )

    low_candidates.sort(key=lambda t: (t[0], t[1], t[2], t[3]))

    for dist, neg_overlap, sc_name, ic_name, ic, sc in low_candidates:
        if ic.name not in matched_ic and sc.name not in matched_sc:
            # LOW tier matches are always renames
            attr_mappings = _build_attribute_mappings(ic, sc)
            mapped_classes.append(
                MappedClass(
                    student_class=sc.name,
                    instructor_classes=[ic.name],
                    mapping_type=MappingType.RENAME,
                    mapped_attributes=attr_mappings,
                )
            )
            matched_ic.add(ic.name)
            matched_sc.add(sc.name)

    # ------------------------------------------------------------------
    # Stage 2: Attribute-driven matching
    # ------------------------------------------------------------------
    attr_candidates: List[Tuple[float, int, str, str, ParsedClass, ParsedClass]] = []
    for ic in ic_list:
        if ic.name in matched_ic:
            continue
        for sc in sc_list:
            if sc.name in matched_sc:
                continue
            overlap = _attribute_overlap(ic, sc)
            if not ic.attributes or overlap < 50.0:
                continue
            dist = levenshtein_distance(ic.name, sc.name)
            # sort: overlap desc (negated), distance asc, sc name asc, ic name asc
            attr_candidates.append(
                (-overlap, dist, sc.name, ic.name, ic, sc)
            )

    attr_candidates.sort(key=lambda t: (t[0], t[1], t[2], t[3]))

    for neg_overlap, dist, sc_name, ic_name, ic, sc in attr_candidates:
        if ic.name not in matched_ic and sc.name not in matched_sc:
            attr_mappings = _build_attribute_mappings(ic, sc)
            mapped_classes.append(
                MappedClass(
                    student_class=sc.name,
                    instructor_classes=[ic.name],
                    mapping_type=MappingType.RENAME,
                    mapped_attributes=attr_mappings,
                )
            )
            matched_ic.add(ic.name)
            matched_sc.add(sc.name)

    # ------------------------------------------------------------------
    # Remainders
    # ------------------------------------------------------------------
    unmapped_instructor_classes = sorted(
        ic.name for ic in ic_list if ic.name not in matched_ic
    )
    unmapped_student_classes = sorted(
        sc.name for sc in sc_list if sc.name not in matched_sc
    )

    # ------------------------------------------------------------------
    # Build ParsedMapping
    # ------------------------------------------------------------------
    class_mapping = ClassMapping(
        mapped_classes=mapped_classes,
        unmapped_instructor_classes=unmapped_instructor_classes,
        unmapped_student_classes=unmapped_student_classes,
    )

    return ParsedMapping(
        class_mapping=class_mapping,
        relationship_mapping=RelationshipMapping(),
        raw_source="",
    )


# Need RelationshipMapping import for the empty default
from isValidMapping import RelationshipMapping