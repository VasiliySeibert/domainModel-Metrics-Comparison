#!/usr/bin/env python3
"""Run Metrik-1 over the dataset and save Quantitative-Analysis/Results/results_metrik1.json.

Metrik-1 is a rule-based mistake-detection metric. The S2 module
``metric.py`` takes two ``ParsedModel`` instances and returns a 3-field
``MetricResult`` dict. We wrap it in a ``MetricProtocol`` adapter and run it
through the ``MetricWorkflow`` harness.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make Workflows/common.py importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (
    DATASET_PATH,
    RESULTS_DIR,
    WORKFLOW_DIR,
    load_metric_module,
    metric_paths,
    setup_sys_path,
)

# Setup sys.path for the metric
_, impl_dir = metric_paths(1)
setup_sys_path(impl_dir)

# Make Workflow importable
sys.path.insert(0, str(WORKFLOW_DIR.parent))

from Workflow import MetricWorkflow  # noqa: E402


class _Metrik1Adapter:
    """Adapter that exposes Metrik-1's ``metric()`` function as a MetricProtocol."""

    def __init__(self, metric_module):
        self._metric = metric_module.metric
        from Parser import PlantUMLParser  # noqa: E402
        self._parser = PlantUMLParser(strict=True)

    @property
    def name(self) -> str:
        return "metrik-1"

    @property
    def version(self) -> str:
        return "1.0.0"

    def compute(self, reference_plantuml: str, generated_plantuml: str):
        ref = self._parser.parse(reference_plantuml)
        gen = self._parser.parse(generated_plantuml)
        return self._metric(ref, gen)


def main() -> int:
    metric_module = load_metric_module(impl_dir)
    adapter = _Metrik1Adapter(metric_module)

    workflow = MetricWorkflow(
        adapter,
        dataset_path=str(DATASET_PATH),
        output_dir=str(RESULTS_DIR),
        verbose=True,
    )
    workflow.run()
    output = workflow.save("results_metrik1.json")
    print(f"Done — wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
