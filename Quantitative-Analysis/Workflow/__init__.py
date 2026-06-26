"""
Workflow — Reusable Metric Evaluation Workflow.

A modular workflow system for evaluating UML domain model comparison metrics
against human evaluations. Loads ``Dataset/combined-data.json``, runs a metric
implementing ``MetricProtocol`` over all 39 (model, setting) pairs, computes
deltas against human F1 scores, and writes a JSON results file.

Example usage:
    from Quantitative-Analysis.Workflow import MetricWorkflow, MetricResult

    class MyMetric:
        @property
        def name(self): return "MyMetric"
        @property
        def version(self): return "1.0.0"
        def compute(self, ref_uml, gen_uml) -> MetricResult:
            return MetricResult(class_score=0.5, attribute_score=0.5, association_score=0.5)

    workflow = MetricWorkflow(MyMetric())
    results = workflow.run()
    workflow.save()
"""

from .metric_interface import MetricProtocol, MetricResult, validate_metric, validate_metric_result
from .workflow import MetricWorkflow, run_workflow
from .data_loader import DataLoader, ComparisonData
from .delta_calculator import DeltaCalculator
from .results_writer import ResultsWriter

__all__ = [
    "MetricProtocol",
    "MetricResult",
    "validate_metric",
    "validate_metric_result",
    "MetricWorkflow",
    "run_workflow",
    "DataLoader",
    "ComparisonData",
    "DeltaCalculator",
    "ResultsWriter",
]
