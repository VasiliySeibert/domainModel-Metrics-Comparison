"""Smoke tests for the public ``domain_model_metrics`` API.

These tests verify that the package imports cleanly and exposes the
expected names; they do **not** exercise the metric implementations (those
are heavier tests in ``test_metrics_protocol.py``).
"""
from __future__ import annotations

import importlib

import pytest


def test_package_imports() -> None:
    """``import domain_model_metrics`` resolves without side effects."""
    pkg = importlib.import_module("domain_model_metrics")
    # The version is bumped on each release; just verify it's a non-empty
    # PEP-440-ish string (digits + dots).
    assert isinstance(pkg.__version__, str)
    parts = pkg.__version__.split(".")
    assert len(parts) >= 2
    assert all(p.isdigit() for p in parts)


def test_public_api_exports() -> None:
    """All documented public names are importable from the top level."""
    import domain_model_metrics as dmm
    for name in ("MetricProtocol", "MetricResult", "get_metric", "list_metrics"):
        assert hasattr(dmm, name), f"missing public name: {name}"


def test_list_metrics_returns_canonical_set() -> None:
    """``list_metrics()`` returns the 5 supported metric names in order."""
    from domain_model_metrics import list_metrics
    assert list_metrics() == ["metrik-1", "metrik-2", "metrik-3", "metrik-4", "metrik-5"]


def test_get_metric_rejects_unknown_name() -> None:
    """``get_metric("metrik-99")`` raises ``ValueError``."""
    from domain_model_metrics import get_metric
    with pytest.raises(ValueError, match="Unknown metric"):
        get_metric("metrik-99")


def test_get_metric_rejects_non_string() -> None:
    """``get_metric(42)`` raises ``TypeError``."""
    from domain_model_metrics import get_metric
    with pytest.raises(TypeError):
        get_metric(42)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "alias",
    ["metrik-1", "metrik1", "Metrik-1", "METRIK_1", "metrik 1"],
)
def test_get_metric_accepts_aliases(alias: str) -> None:
    """``get_metric`` accepts hyphenated / underscored / spaced aliases.

    The factory normalises the input so casual spellings still work.
    """
    from domain_model_metrics import get_metric
    metric = get_metric(alias)
    assert metric.name == "metrik-1"
    assert metric.version == "1.0.0"