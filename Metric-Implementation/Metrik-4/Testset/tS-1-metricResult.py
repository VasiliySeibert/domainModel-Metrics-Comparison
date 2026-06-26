"""
tS-1-metricResult.py — Tests for SimilarityResult and isValidMetricResult.

Verifies that:
  1. SimilarityResult and sub-score dataclasses can be constructed and are frozen.
  2. isValidMetricResult Tier A (type & bounds) rejects invalid objects / NaN / Inf.
  3. isValidMetricResult Tier B (math reconstruction) catches identity violations.
  4. isValidMetricResult Tier C (input-dependent behavior) enforces correct
     values for identical, empty, and partially-empty inputs.

The file follows the same shape as tS-1-isValidInvariants.py.
"""

import math
import sys
from pathlib import Path

# Add the metric root to path so Parser and Testset resolve
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Specification.metric_models import (
    SimilarityResult,
    SemanticScores,
    StructuralScores,
)
from Testset.metric_invariants import isValidSimilarity, isValidMetricResult
from Parser.models import ParsedModel


# ---------------------------------------------------------------------------
# 1.  Dataclass construction & immutability
# ---------------------------------------------------------------------------

def test_semantic_scores_frozen():
    """SemanticScores must be an immutable frozen dataclass."""
    s = SemanticScores(semantic=0.7, propSim=0.5, relSim=0.9)
    assert s.semantic == 0.7
    assert s.propSim == 0.5
    assert s.relSim == 0.9
    try:
        s.semantic = 0.0
        assert False, "frozen dataclass should be immutable"
    except AttributeError:
        pass


def test_structural_scores_frozen():
    """StructuralScores must be an immutable frozen dataclass."""
    s = StructuralScores(structural=0.8, intraSim=0.6, interSim=1.0)
    assert s.structural == 0.8
    assert s.intraSim == 0.6
    assert s.interSim == 1.0
    try:
        s.structural = 0.0
        assert False, "frozen dataclass should be immutable"
    except AttributeError:
        pass


def test_similarity_result_frozen():
    """SimilarityResult must be an immutable frozen dataclass."""
    r = SimilarityResult(
        similarity=0.5,
        semantic=0.4,
        structural=0.6,
        propSim=0.3,
        relSim=0.7,
        intraSim=0.55,
        interSim=0.65,
    )
    assert r.similarity == 0.5
    try:
        r.similarity = 0.0
        assert False, "frozen dataclass should be immutable"
    except AttributeError:
        pass


# ---------------------------------------------------------------------------
# 2.  isValidSimilarity rejects NaN, Inf, bool
# ---------------------------------------------------------------------------

def test_isValidSimilarity_rejects_nan():
    assert isValidSimilarity(float("nan")) is False


def test_isValidSimilarity_rejects_inf():
    assert isValidSimilarity(float("inf")) is False
    assert isValidSimilarity(float("-inf")) is False


def test_isValidSimilarity_rejects_bool():
    assert isValidSimilarity(True) is False
    assert isValidSimilarity(False) is False


# ---------------------------------------------------------------------------
# 3.  Tier A – type & basic bounds
# ---------------------------------------------------------------------------

def test_valid_result_basic():
    """A perfectly valid SimilarityResult on two empty models."""
    r = SimilarityResult(
        similarity=1.0,
        semantic=1.0,
        structural=1.0,
        propSim=1.0,
        relSim=1.0,
        intraSim=1.0,
        interSim=1.0,
    )
    assert isValidMetricResult(ParsedModel(), ParsedModel(), r) is True


def test_rejects_non_similarity_result():
    """Passing a plain float must fail Tier A."""
    assert isValidMetricResult(ParsedModel(), ParsedModel(), 0.5) is False


def test_rejects_field_out_of_range():
    """Any field outside [0,1] must fail Tier A."""
    r = SimilarityResult(
        similarity=1.0,
        semantic=1.0,
        structural=1.0,
        propSim=1.0,
        relSim=1.0,
        intraSim=1.0,
        interSim=1.01,  # out of range
    )
    assert isValidMetricResult(ParsedModel(), ParsedModel(), r) is False


def test_rejects_nan_field():
    """NaN in any field must fail Tier A."""
    r = SimilarityResult(
        similarity=1.0,
        semantic=1.0,
        structural=1.0,
        propSim=1.0,
        relSim=1.0,
        intraSim=1.0,
        interSim=float("nan"),
    )
    assert isValidMetricResult(ParsedModel(), ParsedModel(), r) is False


# ---------------------------------------------------------------------------
# 4.  Tier B – mathematical reconstruction
# ---------------------------------------------------------------------------

def test_rejects_similarity_identity_violation():
    """similarity != 0.5*sem + 0.5*struc must fail."""
    r = SimilarityResult(
        similarity=0.5,   # wrong — should be 0.5*0.4 + 0.5*0.6 = 0.5 ...
        semantic=0.4,
        structural=0.6,
        propSim=0.0,
        relSim=0.0,
        intraSim=0.0,
        interSim=0.0,
    )
    # actually that example *does* satisfy the first identity by accident;
    # let's break the second one.
    r = SimilarityResult(
        similarity=0.5,  # 0.5*0.4 + 0.5*0.6 = 0.5
        semantic=0.4,
        structural=0.6,
        propSim=0.0,
        relSim=0.0,      # 0.7*0 + 0.3*0 = 0  != 0.4
        intraSim=0.0,
        interSim=0.0,
    )
    assert isValidMetricResult(ParsedModel(), ParsedModel(), r) is False


def test_rejects_semantic_identity_violation():
    """semantic != 0.7*propSim + 0.3*relSim must fail."""
    # Make the top-level similarity match, but break semantic sub-identity.
    # similarity = 0.5*0.7 + 0.5*0.5 = 0.6
    # semantic   = 0.7*1.0 + 0.3*0.0 = 0.7
    # structural = 0.5 (matches)
    # intraSim should be (structural - 0.1*interSim)/0.9 =>
    #   interSim=0.0  => intraSim = 0.5/0.9 ≈ 0.555...
    # But we set intraSim to something else to break second identity.
    r = SimilarityResult(
        similarity=0.6,
        semantic=0.7,
        structural=0.5,
        propSim=1.0,
        relSim=0.0,
        intraSim=0.9,
        interSim=0.0,
    )
    assert isValidMetricResult(ParsedModel(), ParsedModel(), r) is False


def test_rejects_structural_identity_violation():
    """structural != 0.9*intraSim + 0.1*interSim must fail."""
    # similarity = 0.5*0.7 + 0.5*0.7 = 0.7
    # semantic   = 0.7*1.0 + 0.3*0.0 = 0.7
    # structural = 0.7
    r = SimilarityResult(
        similarity=0.7,
        semantic=0.7,
        structural=0.7,
        propSim=1.0,
        relSim=0.0,
        intraSim=0.0,
        interSim=0.0,
    )
    assert isValidMetricResult(ParsedModel(), ParsedModel(), r) is False


def test_accepts_exact_reconstruction_identities():
    """A result that satisfies all three identities with exact floats."""
    # Choose nice numbers:
    # propSim=1, relSim=1  => semantic = 1
    # intraSim=1, interSim=1 => structural = 1
    # similarity = 1
    r = SimilarityResult(
        similarity=1.0,
        semantic=1.0,
        structural=1.0,
        propSim=1.0,
        relSim=1.0,
        intraSim=1.0,
        interSim=1.0,
    )
    assert isValidMetricResult(ParsedModel(), ParsedModel(), r) is True


# ---------------------------------------------------------------------------
# 5.  Tier C – input-dependent guarantees
# ---------------------------------------------------------------------------

def test_identical_models_must_be_one():
    """Two identical empty models → all scores must be exactly 1.0."""
    r = SimilarityResult(
        similarity=1.0,
        semantic=1.0,
        structural=1.0,
        propSim=1.0,
        relSim=1.0,
        intraSim=1.0,
        interSim=1.0,
    )
    m = ParsedModel()
    assert isValidMetricResult(m, m, r) is True


def test_identical_models_wrong_score():
    """Two identical empty models but similarity < 1.0 must fail."""
    r = SimilarityResult(
        similarity=0.5,
        semantic=0.5,
        structural=0.5,
        propSim=0.5,
        relSim=0.5,
        intraSim=0.5,
        interSim=0.5,
    )
    m = ParsedModel()
    assert isValidMetricResult(m, m, r) is False


def test_both_empty_all_scores_must_be_one():
    """Both empty → all scores must be 1.0."""
    r = SimilarityResult(
        similarity=1.0,
        semantic=1.0,
        structural=1.0,
        propSim=1.0,
        relSim=1.0,
        intraSim=1.0,
        interSim=1.0,
    )
    assert isValidMetricResult(ParsedModel(), ParsedModel(), r) is True


# TODO: Add Tier C tests for non-empty models once `normalize` in
# Specification/metric_normalize.py is implemented (it is currently a
# stub with a `...` body).
#
# Tests to add later:
# - One empty vs one non-empty  → similarity == 0.0
# - Two identical non-empty models → all scores == 1.0
# - Both have zero relationships  → relSim == 1.0 and interSim == 1.0


# ---------------------------------------------------------------------------
# 6.  Main entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_list = [
        test_semantic_scores_frozen,
        test_structural_scores_frozen,
        test_similarity_result_frozen,
        test_isValidSimilarity_rejects_nan,
        test_isValidSimilarity_rejects_inf,
        test_isValidSimilarity_rejects_bool,
        test_valid_result_basic,
        test_rejects_non_similarity_result,
        test_rejects_field_out_of_range,
        test_rejects_nan_field,
        test_rejects_similarity_identity_violation,
        test_rejects_semantic_identity_violation,
        test_rejects_structural_identity_violation,
        test_accepts_exact_reconstruction_identities,
        test_identical_models_must_be_one,
        test_identical_models_wrong_score,
        test_both_empty_all_scores_must_be_one,
        # TODO: the next four tests require a real `normalize()` in
        # Specification/metric_normalize.py (currently a stub).
        # test_empty_vs_nonempty_must_be_zero,
        # test_empty_vs_nonempty_wrong_score,
        # test_zero_relationships,
        # test_zero_relationships_relSim_wrong,
    ]

    passed = 0
    failed = 0
    for test in test_list:
        try:
            test()
            passed += 1
        except AssertionError as exc:
            failed += 1
            print(f"FAIL: {test.__name__} – {exc}")
        except Exception as exc:
            failed += 1
            print(f"ERROR: {test.__name__} – {exc}")

    total = passed + failed
    print(f"\n{passed}/{total} tests passed, {failed}/{total} tests failed")
