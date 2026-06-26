import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import icontract
from Testset.isValidModel import isValidModel
from Testset.isValidSimilarity import isValidSimilarity

from Specification.transformUCDtoUCG import transformUCDtoUCG
from Specification.buildUMCSTree import buildUMCSTree
from Specification.computeInterStructureSimilarity import computeInterStructureSimilarity
from Specification.computeIntraStructureSimilarity import computeIntraStructureSimilarity
from Specification.combineStructuralSimilarity import combineStructuralSimilarity


@icontract.require(lambda instructor_model, student_model: (
    isValidModel(instructor_model) and isValidModel(student_model)
))
@icontract.ensure(lambda result: isValidSimilarity(result))
def metric(instructor_model, student_model) -> float:
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
    6. Return the maximum combined similarity among all candidates.
       If no candidates exist, return ``0.0``.

    Parameters
    ----------
    instructor_model : ParsedModel
        The reference UML class diagram model.
    student_model : ParsedModel
        The generated UML class diagram model.

    Returns
    -------
    float
        Structural similarity value in [0, 1].
        0 means completely different, 1 means identical.

    Preconditions
    -------------
    * ``isValidModel(instructor_model)`` holds.
    * ``isValidModel(student_model)`` holds.

    Postconditions
    --------------
    * ``isValidSimilarity(result)`` holds.
    * The returned value is the maximum structural similarity computed
      among all candidate inter-structure matches, or ``0.0`` if no
      candidates exist.
    """
    instructor_ucg = transformUCDtoUCG(instructor_model)
    student_ucg = transformUCDtoUCG(student_model)

    umcs_tree = buildUMCSTree(instructor_ucg, student_ucg)

    inter_candidates = computeInterStructureSimilarity(
        instructor_ucg, student_ucg, umcs_tree
    )

    similarities = []
    for sim_inter, matching_pairs in inter_candidates:
        sim_intra = computeIntraStructureSimilarity(
            instructor_ucg, student_ucg, matching_pairs
        )
        sim = combineStructuralSimilarity(sim_inter, sim_intra)
        similarities.append(sim)

    return max(similarities) if similarities else 0.0
