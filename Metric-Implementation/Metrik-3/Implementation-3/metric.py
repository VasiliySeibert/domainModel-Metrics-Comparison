"""
metric.py — Metrik-3 structural similarity metric.

Implements MetricProtocol:
    - name: "D-Metrik-8"
    - version: "1.0.0"
    - compute(ref_model, gen_model) -> MetricResult (dict)

Computes the Metrik-3 structural similarity between an instructor
(reference) and student (generated) UML class diagram model.

Returns a dict with keys:
    "class_score":       float  # [0, 1]
    "attribute_score":   float  # [0, 1]
    "association_score": float  # [0, 1]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidModel import isValidModel
from Testset.s1_types import UCG

from transformUCDtoUCG import transformUCDtoUCG
from buildUMCSTree import buildUMCSTree
from computeInterStructureSimilarity import computeInterStructureSimilarity
from computeIntraStructureSimilarity import computeIntraStructureSimilarity
from combineStructuralSimilarity import combineStructuralSimilarity
from normalize import normalize


# ------------------------------------------------------------------
# MetricProtocol conformance
# ------------------------------------------------------------------
NAME = "D-Metrik-8"
VERSION = "1.0.0"


@icontract.require(lambda instructor_model, student_model: (
    isValidModel(instructor_model) and isValidModel(student_model)
))
def metric(instructor_model, student_model) -> dict:
    """
    Compute Metrik-3 scores.

    Returns
    -------
    dict
        {
            "class_score":       float,  # [0, 1]
            "attribute_score":   float,  # [0, 1]
            "association_score": float,  # [0, 1]
        }
    """
    instructor_ucg = transformUCDtoUCG(instructor_model)
    student_ucg = transformUCDtoUCG(student_model)

    # Check if both UCGs have relationship edges (precondition for
    # computeInterStructureSimilarity)
    instructor_has_re = any(e.edge_type == "relationship" for e in instructor_ucg.edges)
    student_has_re = any(e.edge_type == "relationship" for e in student_ucg.edges)

    best_similarity = 0.0
    best_sim_inter = 0.0
    best_sim_intra = 1.0
    best_matching_pairs = set()

    if not instructor_has_re or not student_has_re:
        # If one or both UCGs have no relationship edges, inter-structure
        # similarity is trivially 0.0 (no common structure to compare).
        best_similarity = 0.0
        best_sim_inter = 0.0
        best_sim_intra = computeIntraStructureSimilarity(
            instructor_ucg, student_ucg, set()
        )
    else:
        umcs_tree = buildUMCSTree(instructor_ucg, student_ucg)

        inter_candidates = computeInterStructureSimilarity(
            instructor_ucg, student_ucg, umcs_tree
        )

        best_similarity = 0.0
        for sim_inter, matching_pairs in inter_candidates:
            sim_intra = computeIntraStructureSimilarity(
                instructor_ucg, student_ucg, matching_pairs
            )
            sim = combineStructuralSimilarity(sim_inter, sim_intra)
            if sim > best_similarity:
                best_similarity = sim
                best_sim_inter = sim_inter
                best_sim_intra = sim_intra
                best_matching_pairs = matching_pairs

    # Decompose into three scores via normalization
    result = normalize(
        instructor_model=instructor_model,
        student_model=student_model,
        instructor_ucg=instructor_ucg,
        student_ucg=student_ucg,
        sim_inter=best_sim_inter,
        sim_intra=best_sim_intra,
        matching_pairs=best_matching_pairs,
    )

    # Ensure all values are clamped to [0, 1]
    for key in ("class_score", "attribute_score", "association_score"):
        result[key] = max(0.0, min(1.0, float(result[key])))

    return result
