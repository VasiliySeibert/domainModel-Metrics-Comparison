#!/usr/bin/env python3
"""
normalize.py — Decompose Metrik-3 structural signals into three
MetricResult scores by hybridizing with lexical F1.

Combination strategy: Simple Average
    class_score      = (class_structural_f1 + class_lexical_f1)  / 2
    attribute_score  = (attr_structural_raw + attr_lexical_f1)   / 2
    association_score = (assoc_structural_f1 + assoc_lexical_f1) / 2

All sub-scores use F1 semantics: both precision and recall.
"""

import sys
from pathlib import Path
from typing import Set, Tuple, Dict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Testset.isValidModel import isValidModel
from Testset.isValidUCG import isValidUCG


def _normalize_name(name: str) -> str:
    """Canonicalize element name for lexical matching."""
    return name.lower().strip().replace("_", "").replace("-", "").replace(" ", "").replace(".", "")


def _compute_f1(ref_set, gen_set):
    """Compute F1 score between two sets."""
    if len(ref_set) == 0 and len(gen_set) == 0:
        return 1.0
    tp = len(ref_set & gen_set)
    precision = tp / len(gen_set) if len(gen_set) > 0 else 0.0
    recall = tp / len(ref_set) if len(ref_set) > 0 else 0.0
    if precision + recall == 0.0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _lexical_class_f1(instructor_model, student_model) -> float:
    """F1 of normalized class+enum name sets."""
    ref_names = set(_normalize_name(n) for n in instructor_model.all_class_names + instructor_model.all_enum_names)
    gen_names = set(_normalize_name(n) for n in student_model.all_class_names + student_model.all_enum_names)
    return _compute_f1(ref_names, gen_names)


def _lexical_attribute_f1(instructor_model, student_model) -> float:
    """F1 of normalized attribute name sets."""
    ref_attrs = set()
    gen_attrs = set()
    for cls in instructor_model.classes:
        for attr in cls.attributes:
            ref_attrs.add(_normalize_name(attr.name))
    for cls in student_model.classes:
        for attr in cls.attributes:
            gen_attrs.add(_normalize_name(attr.name))
    return _compute_f1(ref_attrs, gen_attrs)


def _relationship_tuple(rel):
    """Canonical relationship tuple for lexical matching."""
    s = _normalize_name(rel.source)
    t = _normalize_name(rel.target)
    rt = rel.relationship_type.value
    if rt in ("association", "inheritance"):
        pair = tuple(sorted([s, t]))
        return (pair[0], pair[1], rt)
    return (s, t, rt)


def _lexical_association_f1(instructor_model, student_model) -> float:
    """F1 of normalized relationship tuple sets."""
    ref_rels = set()
    gen_rels = set()
    for rel in instructor_model.relationships:
        if rel.relationship_type.value != "association_class":
            ref_rels.add(_relationship_tuple(rel))
    for rel in student_model.relationships:
        if rel.relationship_type.value != "association_class":
            gen_rels.add(_relationship_tuple(rel))
    return _compute_f1(ref_rels, gen_rels)


def _structural_class_f1(instructor_ucg, student_ucg, matching_pairs: Set[Tuple[str, str]]) -> float:
    """Structural class F1 from UMCS matched vertex pairs."""
    ref_cv = [v for v in instructor_ucg.vertices if v.vertex_type == "class"]
    gen_cv = [v for v in student_ucg.vertices if v.vertex_type == "class"]
    n_ref = len(ref_cv)
    n_gen = len(gen_cv)
    if n_ref == 0 and n_gen == 0:
        return 1.0
    if n_ref == 0 or n_gen == 0:
        return 0.0
    matched_ref = set()
    matched_gen = set()
    for v1, v2 in matching_pairs:
        if v1.startswith("cv:") and v2.startswith("cv:"):
            matched_ref.add(v1)
            matched_gen.add(v2)
    if not matched_ref:
        return 0.0
    p = len(matched_gen) / n_gen
    r = len(matched_ref) / n_ref
    return 2 * p * r / (p + r) if (p + r) > 0 else 0.0


def _structural_association_f1(instructor_ucg, student_ucg, sim_inter: float) -> float:
    """Structural association F1 (precision + recall of matched edges)."""
    n_ref_re = len([e for e in instructor_ucg.edges if e.edge_type == "relationship"])
    n_gen_re = len([e for e in student_ucg.edges if e.edge_type == "relationship"])
    min_re = min(n_ref_re, n_gen_re)
    max_re = max(n_ref_re, n_gen_re)
    if min_re == 0:
        return 0.0
    umcs_size = int(round(sim_inter * min_re))
    if umcs_size == 0:
        return 0.0
    recall = sim_inter  # = umcs_size / min_re
    precision = umcs_size / max_re if max_re > 0 else 0.0
    return 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0


def _structural_attribute_raw(sim_intra: float) -> float:
    """Extract raw attribute similarity from sim_intra decomposition."""
    # sim_intra = ALPHA * simAttr + BETA * simOper + GAMMA * simParam
    # simOper = 1.0, simParam = 1.0 (no operations/parameters in parser)
    ALPHA = 0.4
    BETA = 0.5
    GAMMA = 0.1
    if ALPHA <= 0:
        return 1.0
    raw = (sim_intra - BETA - GAMMA) / ALPHA
    return max(0.0, min(1.0, raw))


def _class_score_no_rel(instructor_ucg, student_ucg, instructor_model, student_model) -> float:
    """Class score when one UCG has no relationship edges."""
    ref_labels = set(v.label for v in instructor_ucg.vertices if v.vertex_type == "class")
    gen_labels = set(v.label for v in student_ucg.vertices if v.vertex_type == "class")
    struct = _compute_f1(ref_labels, gen_labels)
    lexical = _lexical_class_f1(instructor_model, student_model)
    return max(0.0, min(1.0, (struct + lexical) / 2.0))


def _attribute_score_no_rel(instructor_ucg, student_ucg, instructor_model, student_model) -> float:
    """Attribute score when one UCG has no relationship edges."""
    ref_att_count = len([e for e in instructor_ucg.edges if e.edge_type == "attribute"])
    gen_att_count = len([e for e in student_ucg.edges if e.edge_type == "attribute"])
    if ref_att_count == 0 and gen_att_count == 0:
        struct = 1.0
    elif ref_att_count == 0 or gen_att_count == 0:
        struct = 0.0
    else:
        struct = min(ref_att_count, gen_att_count) / max(ref_att_count, gen_att_count)
    lexical = _lexical_attribute_f1(instructor_model, student_model)
    return max(0.0, min(1.0, (struct + lexical) / 2.0))


def normalize(
    instructor_model,
    student_model,
    instructor_ucg,
    student_ucg,
    sim_inter: float,
    sim_intra: float,
    matching_pairs: Set[Tuple[str, str]],
) -> Dict[str, float]:
    """
    Compute the Simple-Average normalized metric result.

    Parameters
    ----------
    instructor_model, student_model : ParsedModel
        The parsed PlantUML models.
    instructor_ucg, student_ucg : UCG
        Corresponding UCGs (output of transformUCDtoUCG).
    sim_inter : float
        Best inter-structure similarity from computeInterStructureSimilarity.
    sim_intra : float
        Best intra-structure similarity from computeIntraStructureSimilarity.
    matching_pairs : set
        Best set of (instructor_vertex_id, student_vertex_id) pairs from
        the UMCS traversal.

    Returns
    -------
    dict
        {
            "class_score":       float,  # [0, 1]
            "attribute_score":   float,  # [0, 1]
            "association_score": float,  # [0, 1]
        }
    """
    # Lexical scores (always available)
    cls_lex = _lexical_class_f1(instructor_model, student_model)
    att_lex = _lexical_attribute_f1(instructor_model, student_model)
    asc_lex = _lexical_association_f1(instructor_model, student_model)

    # Check if both UCGs have relationship edges
    instructor_has_re = any(e.edge_type == "relationship" for e in instructor_ucg.edges)
    student_has_re = any(e.edge_type == "relationship" for e in student_ucg.edges)

    if not instructor_has_re or not student_has_re:
        # Edge case: no relationship edges in one or both UCGs
        cls_score = _class_score_no_rel(instructor_ucg, student_ucg, instructor_model, student_model)
        att_score = _attribute_score_no_rel(instructor_ucg, student_ucg, instructor_model, student_model)
        asc_score = max(0.0, min(1.0, (0.0 + asc_lex) / 2.0))
        return {
            "class_score": cls_score,
            "attribute_score": att_score,
            "association_score": asc_score,
        }

    # Normal case: structural + lexical via Simple Average
    cls_struct = _structural_class_f1(instructor_ucg, student_ucg, matching_pairs)
    att_struct = _structural_attribute_raw(sim_intra)
    asc_struct = _structural_association_f1(instructor_ucg, student_ucg, sim_inter)

    cls_score = max(0.0, min(1.0, (cls_struct + cls_lex) / 2.0))
    att_score = max(0.0, min(1.0, (att_struct + att_lex) / 2.0))
    asc_score = max(0.0, min(1.0, (asc_struct + asc_lex) / 2.0))

    return {
        "class_score": cls_score,
        "attribute_score": att_score,
        "association_score": asc_score,
    }
