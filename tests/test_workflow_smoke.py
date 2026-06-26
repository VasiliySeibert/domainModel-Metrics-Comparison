"""Smoke test for the Workflow package.

Verifies that ``MetricWorkflow`` can be instantiated against the bundled
dataset and that ``MetricResult`` validation works. Runs the workflow on
Metrik-1 (the fast rule-based metric) only; the 4 heavier metrics have
their own runnable scripts under ``Quantitative-Analysis/RunMetrics/``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from domain_model_metrics import get_metric
from domain_model_metrics.workflow import MetricResult, MetricWorkflow

_REPO_ROOT = Path(__file__).resolve().parents[1]
_RESULTS_DIR = _REPO_ROOT / "Quantitative-Analysis" / "Results"


def test_metric_result_validator_accepts_canonical_shape() -> None:
    """A dict with the 3 required keys, each in [0,1], passes validation."""
    from domain_model_metrics.workflow import validate_metric_result
    assert validate_metric_result({"class_score": 0.5, "attribute_score": 0.5, "association_score": 0.5})
    assert not validate_metric_result({"class_score": 1.5, "attribute_score": 0.5, "association_score": 0.5})
    assert not validate_metric_result({"class_score": 0.5, "attribute_score": 0.5})  # missing key


def test_metric_workflow_runs_on_bundled_dataset(tmp_path: Path) -> None:
    """End-to-end: run Metrik-1 on the bundled 39-pair dataset, verify JSON schema."""
    metric = get_metric("metrik-1")
    workflow = MetricWorkflow(
        metric,
        dataset_path=str(_REPO_ROOT / "data" / "combined-data.json"),
        output_dir=str(tmp_path),
        verbose=False,
    )
    workflow.run()
    output_path = workflow.save("results_metrik1_test.json")
    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert "metadata" in payload
    assert "comparisons" in payload
    # Bundled dataset has 39 valid pairs (SHAS_0shot is skipped).
    n_pairs = len(payload["comparisons"])
    assert n_pairs >= 38, f"expected >= 38 comparisons, got {n_pairs}"


def test_bundled_results_match_workflow_re_run_bit_exact(tmp_path: Path) -> None:
    """Bit-exact reproducibility: re-running Metrik-1 on the bundled dataset
    produces the same JSON values as the pre-bundled
    ``Quantitative-Analysis/Results/results_metrik1.json``.

    This is the cross-check that the ``pip install`` flow is faithful to
    the source diss-metrik results.
    """
    bundled = _RESULTS_DIR / "results_metrik1.json"
    if not bundled.is_file():
        pytest.skip(f"bundled results JSON not present: {bundled}")

    metric = get_metric("metrik-1")
    workflow = MetricWorkflow(
        metric,
        dataset_path=str(_REPO_ROOT / "data" / "combined-data.json"),
        output_dir=str(tmp_path),
        verbose=False,
    )
    workflow.run()
    fresh = workflow.save("results_metrik1_fresh.json")
    bundled_payload = json.loads(bundled.read_text(encoding="utf-8"))
    fresh_payload = json.loads(fresh.read_text(encoding="utf-8"))

    # Compare per-comparison metric_results. class_score, attribute_score,
    # association_score must be bit-identical (JSON serialisation of the
    # same float values).
    for cid, comp in fresh_payload["comparisons"].items():
        assert cid in bundled_payload["comparisons"], f"missing pair {cid} in bundled results"
        bundled_mr = bundled_payload["comparisons"][cid]["metric_results"]
        fresh_mr = comp["metric_results"]
        for key in ("class_score", "attribute_score", "association_score"):
            assert bundled_mr[key] == fresh_mr[key], (
                f"score drift for {cid}.{key}: bundled={bundled_mr[key]} "
                f"fresh={fresh_mr[key]}"
            )