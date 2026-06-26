"""
S-1 Class-Diagram Similarity Metric

Top-level entry point implementing the Triandini (2021) semantic and
structural similarity metric, adapted for PlantUML input via the project's
PlantUMLParser (see Metric-Implementation/Metrik-4/Implementation_3/s1.md).

Exported function:
    metric  – takes two ParsedModel instances and returns a SimilarityResult.
"""

import math

import icontract

from ..Parser.models import ParsedModel
from ..Testset.metric_invariants import isValidParsedModel, isValidMetricResult
from metric_normalize import normalize
from metric_semantic import classSem
from metric_structural import classStruc
from metric_primitives import clampToUnit
from metric_models import SimilarityResult


# ----------------------------------------------------------------------
# Top-level metric
# ----------------------------------------------------------------------
@icontract.require(lambda model1: isValidParsedModel(model1))
@icontract.require(lambda model2: isValidParsedModel(model2))
@icontract.ensure(lambda model1, model2, result: isValidMetricResult(model1, model2, result))
def metric(model1: ParsedModel, model2: ParsedModel) -> SimilarityResult:
    """
    Computes the combined class-diagram similarity between two parsed models.

    Pipeline
    --------
    1. Normalise both models:
           d1 = normalize(model1)
           d2 = normalize(model2)
    2. Compute semantic component:
           sem_scores = classSem(d1, d2)        # rho_sem = 0.3 internally
    3. Compute structural component:
           struc_scores = classStruc(d1, d2)    # rho_struc = 0.1 internally
    4. Combine with equal weighting (rho = 0.5):
           similarity = 0.5 * sem_scores.semantic + 0.5 * struc_scores.structural
    5. Build and return SimilarityResult:
           return SimilarityResult(
               similarity=clampToUnit(similarity),
               semantic=sem_scores.semantic,
               structural=struc_scores.structural,
               propSim=sem_scores.propSim,
               relSim=sem_scores.relSim,
               intraSim=struc_scores.intraSim,
               interSim=struc_scores.interSim,
           )

    Input:  Two ParsedModel instances (student and instructor).
    Output: A SimilarityResult whose fields satisfy the reconstruction
            identities and the input-dependent guarantees defined in
            ``isValidMetricResult``.

    Output Guarantees
    -----------------
    Mathematical reconstruction (tolerance ``1e-6``):
        similarity  == 0.5 * semantic + 0.5 * structural
        semantic    == 0.7 * propSim   + 0.3 * relSim
        structural  == 0.9 * intraSim  + 0.1 * interSim

    Input-dependent guarantees:
    - Identical models:  ``metric(m, m).similarity == 1.0`` (and all
      sub-scores == 1.0).
    - Both fully empty (no classes, no relationships) -> all scores ``1.0``.
    - One empty + one non-empty -> ``similarity == 0.0``.
    - The result is guaranteed finite (no NaN, no Inf).

    See Also
    --------
    SimilarityResult, isValidMetricResult, classSem, classStruc
    """
    ...