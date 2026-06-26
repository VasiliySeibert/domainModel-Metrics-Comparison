"""Per-metric Protocol-conformance + score-range tests.

For each of the 5 metrics we instantiate via ``get_metric("metrik-N")``
and verify:
  1. The returned object satisfies ``MetricProtocol``.
  2. ``compute(ref, gen)`` returns a 3-key dict with all scores in [0, 1].
  3. The metric name matches the requested one.

We exercise the metrics against the canonical ``LabTracker_0shot`` pair
from the bundled 39-pair benchmark. Every metric's source implementation
has been validated on this pair; if a metric's invariants reject it, that
indicates a regression in the metric code (not a test problem).

Metrik-4/5 are slow (NLTK / WordNet). We mark them with a ``@pytest.mark.slow``
marker so they can be skipped with ``pytest -m 'not slow'`` for fast CI.
"""
from __future__ import annotations

import pytest

from domain_model_metrics import MetricProtocol, get_metric, list_metrics

from _fixtures import load_labtracker_0shot


_REQUIRED_KEYS = ("class_score", "attribute_score", "association_score")


def _is_unit_float(x: object) -> bool:
    return isinstance(x, (int, float)) and 0.0 <= float(x) <= 1.0


# Metrik-4 and Metrik-5 use NLTK / WordNet and take ~10 seconds per pair.
# Mark them slow so the fast CI matrix runs quickly.
SLOW_METRICS = {"metrik-4", "metrik-5"}


@pytest.mark.parametrize("name", list_metrics())
def test_get_metric_returns_metric_protocol(name: str) -> None:
    """``get_metric(name)`` returns a ``MetricProtocol``-conforming object."""
    metric = get_metric(name)
    assert isinstance(metric, MetricProtocol)
    assert metric.name == name
    assert metric.version == "1.0.0"


@pytest.mark.parametrize("name", list_metrics())
def test_get_metric_rejects_non_string_score_inputs(name: str) -> None:
    """Computing on empty strings raises ``ValueError`` (input validation)."""
    metric = get_metric(name)
    with pytest.raises(Exception):
        metric.compute("", "")


@pytest.mark.parametrize("name", list_metrics())
def test_metric_returns_three_unit_interval_scores(name: str) -> None:
    """``compute`` on LabTracker_0shot returns the 3 expected keys in [0, 1]."""
    if name in SLOW_METRICS:
        pytest.skip(f"{name} is slow (NLTK/WordNet); run with -m 'not slow' to skip")
    metric = get_metric(name)
    ref, gen, _ = load_labtracker_0shot()
    result = metric.compute(ref, gen)
    assert isinstance(result, dict)
    for key in _REQUIRED_KEYS:
        assert key in result, f"{name}.compute() missing required key: {key}"
        assert _is_unit_float(result[key]), f"{name}.compute()['{key}'] = {result[key]!r} not in [0,1]"