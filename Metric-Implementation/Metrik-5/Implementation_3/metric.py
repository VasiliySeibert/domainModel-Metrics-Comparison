"""
Metrik-5 — S-1 Class-Diagram Similarity Metric (3-field view).

Top-level entry point implementing the Triandini (2021) semantic and
structural similarity metric, adapted for PlantUML input via the project's
PlantUMLParser (see Metric-Implementation/Metrik-5/Implementation_3/s1.md).

The function ``metric`` returns a ``MetricResult`` (the standard 3-field
schema) rather than a ``SimilarityResult``. The seven S-1 sub-scores
are still computed as locals inside the pipeline and projected onto the three
human-aligned categories:

    class_score       <- intraSim
    attribute_score   <- intraSim
    association_score <- interSim

A ``MetricProtocol``-conforming adapter (``DISSMetricExtended2``) and a
``get_metric()`` factory are also provided so this module can be consumed
directly without going through a separate ``diss_metric.py`` shim.
"""

import sys
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parent.parent
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from Parser import PlantUMLParser
from Parser.models import ParsedModel
from Testset.metric_invariants import isValidParsedModel
from Implementation_3.metric_normalize import normalize
from Implementation_3.metric_semantic import classSem
from Implementation_3.metric_structural import classStruc
from Implementation_3.metric_primitives import clampToUnit
from Implementation_3.metric_models import SimilarityResult
from Implementation_3.metric_interface import (
    MetricResult,
    MetricProtocol,
    validate_metric_result,
)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _clamp(x: float) -> float:
    """Clamp ``x`` into the closed unit interval [0.0, 1.0]."""
    return max(0.0, min(1.0, float(x)))


# ----------------------------------------------------------------------
# Top-level metric
# ----------------------------------------------------------------------
def metric(model1: ParsedModel, model2: ParsedModel) -> MetricResult:
    """
    Computes the combined class-diagram similarity between two parsed models
    and returns a 3-field ``MetricResult``.

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
    5. Build the internal 7-field S-1 result (kept as a local for clarity):
           s1 = SimilarityResult(
               similarity=clampToUnit(similarity),
               semantic=...,
               structural=...,
               propSim=...,
               relSim=...,
               intraSim=...,
               interSim=...,
           )
    6. Project the S-1 sub-scores onto the 3-field ``MetricResult`` schema:
           class_score       <- s1.intraSim
           attribute_score   <- s1.intraSim
           association_score <- s1.interSim
    7. Validate the projected result and return it.

    Input:  Two ``ParsedModel`` instances (instructor and student).
    Output: A ``MetricResult`` dict with ``class_score``,
            ``attribute_score``, ``association_score`` in ``[0.0, 1.0]``.

    Output Guarantees
    -----------------
    - All three returned scores are finite floats in ``[0.0, 1.0]``.
    - The returned dict satisfies ``validate_metric_result``.
    - For identical models, all three scores are ``1.0`` (and conversely, an
      all-``1.0`` result is produced whenever the underlying S-1 pipeline
      reports identical sub-scores).
    - The result is deterministic: the function is pure in its inputs.

    See Also
    --------
    MetricResult, validate_metric_result, DISSMetricExtended2, get_metric
    """
    assert isValidParsedModel(model1), "model1 is not a valid ParsedModel"
    assert isValidParsedModel(model2), "model2 is not a valid ParsedModel"

    d1 = normalize(model1)
    d2 = normalize(model2)

    sem_scores = classSem(d1, d2)
    struc_scores = classStruc(d1, d2)

    similarity = clampToUnit(0.5 * sem_scores.semantic + 0.5 * struc_scores.structural)

    s1 = SimilarityResult(
        similarity=similarity,
        semantic=sem_scores.semantic,
        structural=struc_scores.structural,
        propSim=sem_scores.propSim,
        relSim=sem_scores.relSim,
        intraSim=struc_scores.intraSim,
        interSim=struc_scores.interSim,
    )

    result: MetricResult = {
        "class_score":       _clamp(s1.intraSim),
        "attribute_score":   _clamp(s1.intraSim),
        "association_score": _clamp(s1.interSim),
    }

    if not validate_metric_result(result):
        raise AssertionError(f"metric() produced an invalid MetricResult: {result}")

    return result


# ----------------------------------------------------------------------
# MetricProtocol-conforming adapter
# ----------------------------------------------------------------------
class DISSMetricExtended2:
    """Adapter that exposes ``metric`` as a ``MetricProtocol``.

    Implements ``MetricProtocol``:
        .name        -> "metrik-5"
        .version     -> "1.0.0"
        .compute(ref_uml, gen_uml) -> MetricResult
    """

    @property
    def name(self) -> str:
        return "metrik-5"

    @property
    def version(self) -> str:
        return "1.0.0"

    def compute(
        self,
        reference_plantuml: str,
        generated_plantuml: str,
    ) -> MetricResult:
        parser = PlantUMLParser(strict=True)
        m1 = parser.parse(reference_plantuml)
        m2 = parser.parse(generated_plantuml)

        if not isValidParsedModel(m1):
            raise ValueError("Invalid reference model")
        if not isValidParsedModel(m2):
            raise ValueError("Invalid generated model")

        return metric(m1, m2)


def get_metric() -> MetricProtocol:
    """Factory that returns a fresh ``MetricProtocol``-conforming instance."""
    return DISSMetricExtended2()


# ----------------------------------------------------------------------
# Smoke test
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    _PKG_ROOT = Path(__file__).resolve().parent.parent
    if str(_PKG_ROOT) not in sys.path:
        sys.path.insert(0, str(_PKG_ROOT))

    # Imports after sys.path manipulation so Parser resolves from the root.
    from Implementation_3.metric import get_metric, metric  # noqa: E402
    from Implementation_3.metric_interface import MetricProtocol  # noqa: E402

    DATASET = _PKG_ROOT / "Dataset" / "combined-data.json"
    with open(DATASET) as f:
        data = json.load(f)

    m = get_metric()
    print(f"name    : {m.name}")
    print(f"version : {m.version}")
    print(f"valid   : {isinstance(m, MetricProtocol)}")

    model_name, model_data = next(iter(data["models"].items()))
    setting, gen_uml = next(iter(model_data["generated_plantuml"].items()))
    ref_uml = model_data["reference_plantuml"]

    out = m.compute(ref_uml, gen_uml)
    print(f"\nSmoke test ({model_name}/{setting}):")
    print(json.dumps(out, indent=2))
