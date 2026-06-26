"""domain_model_metrics — public API for the 5 domain-model similarity metrics.

This package is a thin wrapper around the canonical implementations under
``Metric-Implementation/Metrik-{1..5}/Implementation-3`` (or
``Implementation_3`` for Metrik-4/5). It provides a uniform
``MetricProtocol`` interface so users can switch metrics without changing
call-site code.

Public API
----------
- ``get_metric(name)`` : factory returning a ``MetricProtocol``-conforming
  instance for one of the 5 metrics.
- ``MetricResult`` : TypedDict describing the 3-score dict returned by
  ``MetricProtocol.compute(ref, gen)``.
- ``MetricProtocol`` : structural Protocol all metric adapters implement.
- ``list_metrics()`` : return the list of supported metric names.

The metric implementations themselves are *not* copied or re-exported; they
are loaded on demand via ``importlib.util`` from the canonical
implementation directories. This keeps the pip-install footprint small and
ensures bit-exact reproducibility with the source diss-metrik project.
"""
from __future__ import annotations

from typing import Dict, List

# Re-export the 3-score TypedDict and the Protocol from the workflow package.
from .workflow import MetricProtocol, MetricResult  # noqa: F401

# Lazy registry of metric factories — populated on first ``get_metric`` call
# to keep ``import domain_model_metrics`` cheap and side-effect free.
_METRIC_NAMES: List[str] = ["metrik-1", "metrik-2", "metrik-3", "metrik-4", "metrik-5"]


def list_metrics() -> List[str]:
    """Return the list of supported metric names (in metric-number order)."""
    return list(_METRIC_NAMES)


def get_metric(name: str) -> MetricProtocol:
    """Return a ``MetricProtocol``-conforming instance for the named metric.

    Parameters
    ----------
    name : str
        One of ``"metrik-1"``, ``"metrik-2"``, ..., ``"metrik-5"`` (case
        insensitive; ``"metrik1"`` is also accepted).

    Returns
    -------
    MetricProtocol
        An object exposing ``.name``, ``.version``, and
        ``.compute(ref_uml, gen_uml) -> MetricResult``.
    """
    if not isinstance(name, str):
        raise TypeError(f"metric name must be a string, got {type(name).__name__}")
    normalised = name.strip().lower().replace("-", "").replace("_", "").replace(" ", "")
    mapping: Dict[str, int] = {
        "metrik1": 1, "metrik2": 2, "metrik3": 3, "metrik4": 4, "metrik5": 5,
    }
    if normalised not in mapping:
        raise ValueError(
            f"Unknown metric '{name}'. Supported: {', '.join(_METRIC_NAMES)}. "
            "Use domain_model_metrics.list_metrics() for the canonical list."
        )
    metric_id = mapping[normalised]

    # Lazy import to avoid loading NLTK / WordNet on import unless needed.
    from .metrics import _factory

    return _factory.build(metric_id)


__all__ = [
    "MetricProtocol",
    "MetricResult",
    "get_metric",
    "list_metrics",
]


__version__ = "1.0.0"