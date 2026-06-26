import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidModel import isValidModel
from Testset.isValidEditInformations import isValidEditInformations
from Testset.s1_types import EditInformations, EditInformation, OperationType

from transformUCDtoUCG import transformUCDtoUCG
from buildUMCSTree import buildUMCSTree
from computeInterStructureSimilarity import computeInterStructureSimilarity
from computeIntraStructureSimilarity import computeIntraStructureSimilarity
from combineStructuralSimilarity import combineStructuralSimilarity


@icontract.require(lambda instructor_model, student_model: (
    isValidModel(instructor_model) and isValidModel(student_model)
))
@icontract.ensure(lambda result: isValidEditInformations(result))
def metric(instructor_model, student_model) -> EditInformations:
    """
    Compute the Metrik-3 structural similarity between an instructor
    (reference) and a student (generated) UML class diagram model.

    Returns an EditInformations object containing a single
    VERTEX_SUBSTITUTION operation whose scaled_cost equals the
    structural similarity value.
    """
    instructor_ucg = transformUCDtoUCG(instructor_model)
    student_ucg = transformUCDtoUCG(student_model)

    # Check if both UCGs have relationship edges (precondition for
    # computeInterStructureSimilarity)
    instructor_has_re = any(e.edge_type == "relationship" for e in instructor_ucg.edges)
    student_has_re = any(e.edge_type == "relationship" for e in student_ucg.edges)

    if not instructor_has_re or not student_has_re:
        # If one or both UCGs have no relationship edges, inter-structure
        # similarity is trivially 0.0 (no common structure to compare).
        best_similarity = 0.0
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

    return EditInformations(
        operations=[
            EditInformation(
                operation_type=OperationType.VERTEX_SUBSTITUTION,
                source_ref="structural_similarity",
                target_ref=None,
                raw_cost=0.0,
                scaled_cost=best_similarity,
            )
        ],
        total_scaled_distance=best_similarity,
    )
