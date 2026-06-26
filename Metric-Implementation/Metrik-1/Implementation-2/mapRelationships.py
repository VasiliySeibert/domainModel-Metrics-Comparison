import icontract
import sys
from pathlib import Path
from typing import List, Tuple, Set

_D4 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_D4))
sys.path.insert(0, str(_D4 / "Testset"))
sys.path.insert(0, str(_D4 / "Parser"))

from isValidModel import isValidModel, ParsedModel
from isValidMapping import (
    isValidMapping,
    ParsedMapping,
    MappedRelationship,
    RelationshipMapping,
    MappingType,
)
from isValidMistakes import isValidMistakes, ParsedMistake, KNOWN_MISTAKE_IDS
from models import ParsedRelationship, RelationshipType


@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.require(lambda mapping: isValidMapping(mapping))
@icontract.ensure(lambda result: isValidMapping(result))
def mapRelationships(
    instructor_model: ParsedModel, student_model: ParsedModel, mapping: ParsedMapping
) -> ParsedMapping:
    """
    mapping |= mapRelations(instructor_model, student_model, mapping):
       unmatched_ir, unmatched_sr = instructor_model.relationships, student_model.relationships
       mapping += greedyRelMatch(unmatched_ir, unmatched_sr, mapping)
       mapping += greedyGenMatch(unmatched_ir, unmatched_sr, mapping)
       return mapping

       requires: isValidMapping
       ensures: isValidMapping

       Association-class relationships are IGNORED.
    """
    # Build one-to-one class map (student -> instructor)
    s_to_i: dict = {}
    for mc in mapping.class_mapping.mapped_classes:
        if mc.instructor_classes:
            s_to_i[mc.student_class] = mc.instructor_classes[0]

    # Filter out association class relationships entirely
    instructor_rels = [
        (idx, rel)
        for idx, rel in enumerate(instructor_model.relationships)
        if rel.relationship_type != RelationshipType.ASSOCIATION_CLASS
    ]
    student_rels = [
        (idx, rel)
        for idx, rel in enumerate(student_model.relationships)
        if rel.relationship_type != RelationshipType.ASSOCIATION_CLASS
    ]

    # Separate inheritance and non-inheritance
    instructor_non_gen = [
        (idx, rel) for idx, rel in instructor_rels if rel.relationship_type != RelationshipType.INHERITANCE
    ]
    student_non_gen = [
        (idx, rel) for idx, rel in student_rels if rel.relationship_type != RelationshipType.INHERITANCE
    ]
    instructor_gen = [
        (idx, rel) for idx, rel in instructor_rels if rel.relationship_type == RelationshipType.INHERITANCE
    ]
    student_gen = [
        (idx, rel) for idx, rel in student_rels if rel.relationship_type == RelationshipType.INHERITANCE
    ]

    mapped_rels: List[MappedRelationship] = []
    mapped_i_idxs: Set[int] = set()
    mapped_s_idxs: Set[int] = set()

    mapped_rels, mapped_i_idxs, mapped_s_idxs = _greedy_match(
        instructor_non_gen, student_non_gen, s_to_i, mapped_rels, mapped_i_idxs, mapped_s_idxs
    )

    mapped_rels, mapped_i_idxs, mapped_s_idxs = _greedy_match(
        instructor_gen, student_gen, s_to_i, mapped_rels, mapped_i_idxs, mapped_s_idxs
    )

    unmapped_i = [idx for idx, _ in instructor_rels if idx not in mapped_i_idxs]
    unmapped_s = [idx for idx, _ in student_rels if idx not in mapped_s_idxs]

    mapping.relationship_mapping = RelationshipMapping(
        mapped_relationships=mapped_rels,
        unmapped_instructor_relationships=unmapped_i,
        unmapped_student_relationships=unmapped_s,
    )
    return mapping


def _greedy_match(
    i_rels: List[Tuple[int, ParsedRelationship]],
    s_rels: List[Tuple[int, ParsedRelationship]],
    s_to_i: dict,
    existing_mapped: List[MappedRelationship],
    existing_i_set: Set[int],
    existing_s_set: Set[int],
):
    """Greedily match relationships based on mapped classes."""
    available_i = [(idx, rel) for idx, rel in i_rels if idx not in existing_i_set]
    available_s = [(idx, rel) for idx, rel in s_rels if idx not in existing_s_set]

    candidates = []
    for s_idx, s_rel in available_s:
        for i_idx, i_rel in available_i:
            forward = (
                s_to_i.get(s_rel.source) == i_rel.source
                and s_to_i.get(s_rel.target) == i_rel.target
            )
            inverted = (
                s_to_i.get(s_rel.source) == i_rel.target
                and s_to_i.get(s_rel.target) == i_rel.source
            )
            if not forward and not inverted:
                continue
            is_exact = s_rel.relationship_type == i_rel.relationship_type
            score = 0
            if is_exact:
                score += 2
            if not inverted:
                score += 1
            candidates.append((score, -i_idx, -s_idx, i_idx, s_idx, is_exact, inverted))

    # Sort descending by score, then ascending by i_idx, then ascending by s_idx
    candidates.sort(reverse=True)

    new_mapped = list(existing_mapped)
    new_i_set = set(existing_i_set)
    new_s_set = set(existing_s_set)

    for score, neg_i, neg_s, i_idx, s_idx, is_exact, inverted in candidates:
        if i_idx in new_i_set or s_idx in new_s_set:
            continue
        mapping_type = MappingType.EXACT if is_exact else MappingType.TYPE_CHANGE
        new_mapped.append(
            MappedRelationship(
                student_rel_index=s_idx,
                instructor_rel_index=i_idx,
                mapping_type=mapping_type,
                is_inverted=inverted,
            )
        )
        new_i_set.add(i_idx)
        new_s_set.add(s_idx)

    return new_mapped, new_i_set, new_s_set
