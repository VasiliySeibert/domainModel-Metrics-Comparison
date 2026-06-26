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

    Algorithm
    ---------
    1. Transform both models into UCGs using ``transformUCDtoUCG``.
    2. Build the UMCS Tree using ``buildUMCSTree``.
    3. Enumerate all candidate inter-structure similarities and matching
       class-vertex pairs using ``computeInterStructureSimilarity``.
    4. For each candidate, compute the intra-structure similarity using
       ``computeIntraStructureSimilarity``.
    5. Combine inter- and intra-similarity using
       ``combineStructuralSimilarity`` (with ``THETA = 0.9``).
    6. Return an EditInformations object with the maximum combined
       similarity as both the scaled_cost and total_scaled_distance.
       If no candidates exist, return EditInformations with
       total_scaled_distance=0.0.

    Parameters
    ----------
    instructor_model : ParsedModel
        The reference UML class diagram model.
    student_model : ParsedModel
        The generated UML class diagram model.

    Returns
    -------
    EditInformations
        An edit path with one VERTEX_SUBSTITUTION operation whose
        scaled_cost equals the structural similarity, and
        total_scaled_distance equals that similarity.

    Preconditions
    -------------
    * ``isValidModel(instructor_model)`` holds.
    * ``isValidModel(student_model)`` holds.

    Postconditions
    --------------
    * ``isValidEditInformations(result)`` holds.
    * The total_scaled_distance is the maximum structural similarity
      computed among all candidate inter-structure matches, or ``0.0``
      if no candidates exist.
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
        # We still compute intra-structure similarity with empty matching
        # pairs if both have class vertices.
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
