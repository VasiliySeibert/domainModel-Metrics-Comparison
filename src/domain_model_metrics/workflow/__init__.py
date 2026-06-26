"""Re-export of the Workflow package's public API.

The canonical implementation lives at
``Quantitative-Analysis/Workflow/`` (carried verbatim from the source
diss-metrik project). This thin wrapper adds ``Quantitative-Analysis`` to
``sys.path`` on import so the canonical package resolves as
``import Workflow`` even when ``domain_model_metrics`` is installed as a
wheel into a different Python environment.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Locate Quantitative-Analysis/Workflow relative to the package source.
_PKG_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_QANALYSIS_PARENT = _PKG_ROOT / "Quantitative-Analysis"
if not _QANALYSIS_PARENT.is_dir():
    raise FileNotFoundError(
        f"Quantitative-Analysis/ not found at {_QANALYSIS_PARENT}. "
        "domain_model_metrics must be installed from a source checkout."
    )
_QANALYSIS_PARENT_STR = str(_QANALYSIS_PARENT)
if _QANALYSIS_PARENT_STR not in sys.path:
    sys.path.insert(0, _QANALYSIS_PARENT_STR)

# Re-export the canonical API. These names live in
# Quantitative-Analysis/Workflow/metric_interface.py (MetricResult,
# MetricProtocol) and Quantitative-Analysis/Workflow/workflow.py
# (MetricWorkflow, run_workflow).
from Workflow.metric_interface import (  # noqa: E402
    MetricProtocol,
    MetricResult,
    validate_metric,
    validate_metric_result,
)
from Workflow.workflow import MetricWorkflow, run_workflow  # noqa: E402

__all__ = [
    "MetricProtocol",
    "MetricResult",
    "MetricWorkflow",
    "run_workflow",
    "validate_metric",
    "validate_metric_result",
]