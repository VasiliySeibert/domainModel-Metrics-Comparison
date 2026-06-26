#!/usr/bin/env python3
"""Run Metrik-2 over the dataset and save Quantitative-Analysis/Results/results_metrik2.json.

Metrik-2 is a graph-edit-distance metric. The S2 module ``metric.py`` takes
two ``ParsedModel`` instances and returns a 3-field ``MetricResult`` dict.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (
    DATASET_PATH,
    RESULTS_DIR,
    WORKFLOW_DIR,
    load_metric_module,
    metric_paths,
    setup_sys_path,
)

_, impl_dir = metric_paths(2)
setup_sys_path(impl_dir)

sys.path.insert(0, str(WORKFLOW_DIR.parent))

from Workflow import MetricWorkflow  # noqa: E402


class _Metrik2Adapter:
    def __init__(self, metric_module):
        self._metric = metric_module.metric
        from Parser import PlantUMLParser  # noqa: E402
        self._parser = PlantUMLParser(strict=True)

    @property
    def name(self) -> str:
        return "metrik-2"

    @property
    def version(self) -> str:
        return "1.0.0"

    def compute(self, reference_plantuml: str, generated_plantuml: str):
        ref = self._parser.parse(reference_plantuml)
        gen = self._parser.parse(generated_plantuml)
        return self._metric(ref, gen)


def main() -> int:
    metric_module = load_metric_module(impl_dir)
    adapter = _Metrik2Adapter(metric_module)

    workflow = MetricWorkflow(
        adapter,
        dataset_path=str(DATASET_PATH),
        output_dir=str(RESULTS_DIR),
        verbose=True,
    )
    workflow.run()
    output = workflow.save("results_metrik2.json")
    print(f"Done — wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
