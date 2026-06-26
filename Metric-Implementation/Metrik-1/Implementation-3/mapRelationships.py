"""
mapRelationships — Relationship mapping: greedy relationship match, then greedy generalization match.

Association-class relationships (RelationshipType.ASSOCIATION_CLASS) are
completely IGNORED — they are neither mapped nor placed in unmapped lists.

Algorithm
---------
1. Build a dictionary instructor_class_name → student_class_name from the
   existing class mapping.
2. Initialise every relationship in both models as *unmatched*, discarding
   association-class relationships.
3. Stage 1 – Strong matching (greedy, score-based).
4. Stage 2 – Weak endpoint-only matching (greedy, deterministic sort).
5. Remainders → unmapped lists.
6. Return the updated mapping.
"""

import icontract
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set

_D4 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_D4))
sys.path.insert(0, str(_D4 / "Testset"))

from isValidModel import isValidModel, ParsedModel
from isValidMapping import (
    isValidMapping,
    ParsedMapping,
    MappedRelationship,
    RelationshipMapping,
    MappingType,
)
from Parser.models import ParsedClass, ParsedAttribute, ParsedRelationship, RelationshipType


def _translate_endpoints(
    rel: ParsedRelationship,
    ic_to_sc: Dict[str, str],
) -> Tuple[Optional[str], Optional[str]]:
    """Translate instructor-relationship endpoints via the class mapping.
    Returns (None, None) if either endpoint is not in the class mapping."""
    src = ic_to_sc.get(rel.source)
    tgt = ic_to_sc.get(rel.target)
    if src is None or tgt is None:
        return None, None
    return src, tgt


def _cardinality_match(
    ir: ParsedRelationship,
    sr: ParsedRelationship,
    inverted: bool,
) -> bool:
    """Check whether cardinalities match after accounting for direction."""
    if not inverted:
        return (
            ir.source_cardinality == sr.source_cardinality
            and ir.target_cardinality == sr.target_cardinality
        )
    else:
        return (
            ir.source_cardinality == sr.target_cardinality
            and ir.target_cardinality == sr.source_cardinality
        )


@icontract.require(lambda instructor_model: isValidModel(instructor_model))
@icontract.require(lambda student_model: isValidModel(student_model))
@icontract.require(lambda mapping: isValidMapping(mapping))
@icontract.ensure(lambda result: isValidMapping(result))
def mapRelationships(
    instructor_model: ParsedModel,
    student_model: ParsedModel,
    mapping: ParsedMapping,
) -> ParsedMapping:
    """Map instructor relationships to student relationships using a two-stage
    greedy algorithm that reuses the existing class mapping."""

    # ------------------------------------------------------------------
    # 1. Build instructor → student class name dictionary
    # ------------------------------------------------------------------
    ic_to_sc: Dict[str, str] = {}
    for mc in mapping.class_mapping.mapped_classes:
        for ic_name in mc.instructor_classes:
            ic_to_sc[ic_name] = mc.student_class

    # ------------------------------------------------------------------
    # 2. Collect non-association-class relationships and their indices
    # ------------------------------------------------------------------
    instructor_rels: List[Tuple[int, ParsedRelationship]] = []
    for i, r in enumerate(instructor_model.relationships):
        if r.relationship_type != RelationshipType.ASSOCIATION_CLASS:
            instructor_rels.append((i, r))

    student_rels: List[Tuple[int, ParsedRelationship]] = []
    for i, r in enumerate(student_model.relationships):
        if r.relationship_type != RelationshipType.ASSOCIATION_CLASS:
            student_rels.append((i, r))

    matched_ir: Set[int] = set()
    matched_sr: Set[int] = set()
    mapped_relationships: List[MappedRelationship] = list(
        mapping.relationship_mapping.mapped_relationships
    )

    # ------------------------------------------------------------------
    # 3. Stage 1 – Strong matching
    # ------------------------------------------------------------------
    # For each (ir, sr) pair, check if translated endpoints match.
    # Score: +100 type match, +10 label match, +5 cardinality match, +1 exact direction
    strong_candidates: List[Tuple[int, str, str, int, int]] = []
    # (neg_score, sr_source, sr_target, ir_index, sr_index)

    for ir_idx, ir in instructor_rels:
        trans_src, trans_tgt = _translate_endpoints(ir, ic_to_sc)
        if trans_src is None or trans_tgt is None:
            continue
        for sr_idx, sr in student_rels:
            # Check exact direction
            is_inverted = False
            if trans_src == sr.source and trans_tgt == sr.target:
                is_inverted = False
            elif trans_src == sr.target and trans_tgt == sr.source:
                is_inverted = True
            else:
                continue  # endpoints don't match in either direction

            score = 0
            if ir.relationship_type == sr.relationship_type:
                score += 100
            if ir.label == sr.label:
                score += 10
            if _cardinality_match(ir, sr, is_inverted):
                score += 5
            if not is_inverted:
                score += 1

            # Sort: score desc, then sr.source, sr.target, ir_idx, sr_idx
            strong_candidates.append(
                (-score, sr.source, sr.target, ir_idx, sr_idx, is_inverted,
                 ir.relationship_type == sr.relationship_type)
            )

    strong_candidates.sort(key=lambda t: (t[0], t[1], t[2], t[3], t[4]))

    for neg_score, sr_src, sr_tgt, ir_idx, sr_idx, is_inverted, type_match in strong_candidates:
        if ir_idx not in matched_ir and sr_idx not in matched_sr:
            mtype = MappingType.EXACT if type_match else MappingType.TYPE_CHANGE
            mapped_relationships.append(
                MappedRelationship(
                    student_rel_index=sr_idx,
                    instructor_rel_index=ir_idx,
                    mapping_type=mtype,
                    is_inverted=is_inverted,
                )
            )
            matched_ir.add(ir_idx)
            matched_sr.add(sr_idx)

    # ------------------------------------------------------------------
    # 4. Stage 2 – Weak endpoint-only matching
    # ------------------------------------------------------------------
    weak_candidates: List[Tuple[str, str, int, int]] = []

    for ir_idx, ir in instructor_rels:
        if ir_idx in matched_ir:
            continue
        trans_src, trans_tgt = _translate_endpoints(ir, ic_to_sc)
        if trans_src is None or trans_tgt is None:
            continue
        for sr_idx, sr in student_rels:
            if sr_idx in matched_sr:
                continue
            if trans_src == sr.source and trans_tgt == sr.target:
                weak_candidates.append(
                    (sr.source, sr.target, ir_idx, sr_idx, False)
                )
            elif trans_src == sr.target and trans_tgt == sr.source:
                weak_candidates.append(
                    (sr.source, sr.target, ir_idx, sr_idx, True)
                )

    weak_candidates.sort(key=lambda t: (t[0], t[1], t[2], t[3]))

    for sr_src, sr_tgt, ir_idx, sr_idx, is_inverted in weak_candidates:
        if ir_idx not in matched_ir and sr_idx not in matched_sr:
            mapped_relationships.append(
                MappedRelationship(
                    student_rel_index=sr_idx,
                    instructor_rel_index=ir_idx,
                    mapping_type=MappingType.CUSTOM,
                    is_inverted=is_inverted,
                )
            )
            matched_ir.add(ir_idx)
            matched_sr.add(sr_idx)

    # ------------------------------------------------------------------
    # 5. Remainders (only non-association-class rels)
    # ------------------------------------------------------------------
    # We need to collect ALL non-association-class relationship indices
    # for proper unmapped tracking. The indices used are the original
    # indices in the model.relationships list.
    all_ir_indices = {idx for idx, r in instructor_rels}
    all_sr_indices = {idx for idx, r in student_rels}

    # Also preserve any previously unmapped indices from the input mapping
    # (though typically the mapping starts empty for relationships)
    unmapped_instructor_relationships = sorted(
        idx for idx in all_ir_indices if idx not in matched_ir
    )
    unmapped_student_relationships = sorted(
        idx for idx in all_sr_indices if idx not in matched_sr
    )

    # ------------------------------------------------------------------
    # 6. Build and return the updated mapping
    # ------------------------------------------------------------------
    new_mapping = ParsedMapping(
        class_mapping=mapping.class_mapping,
        relationship_mapping=RelationshipMapping(
            mapped_relationships=mapped_relationships,
            unmapped_instructor_relationships=unmapped_instructor_relationships,
            unmapped_student_relationships=unmapped_student_relationships,
        ),
        raw_source=mapping.raw_source,
    )

    return new_mapping