# Workflow — Reusable Metric Evaluation Harness

A Python package that provides the metric-evaluation pipeline used by the
project's workflows.

## What it does

1. **Load dataset** — `DataLoader` reads `Dataset/combined-data.json` and
   yields `ComparisonData` objects for each (model, setting) pair.
2. **Run metric** — accepts any object implementing `MetricProtocol`
   (`name`, `version`, `compute(ref_uml, gen_uml) -> MetricResult`).
3. **Compute deltas** — `DeltaCalculator` measures the difference between
   metric scores and human-evaluated F1 scores for Class, Attribute,
   Association.
4. **Save results** — `ResultsWriter` writes a `results.json` with
   per-comparison details and summary statistics.

## Quick start

```python
from Workflow import MetricWorkflow, MetricResult

class MyMetric:
    @property
    def name(self): return "MyMetric"
    @property
    def version(self): return "1.0.0"
    def compute(self, ref_uml, gen_uml) -> MetricResult:
        return MetricResult(class_score=0.5, attribute_score=0.5, association_score=0.5)

wf = MetricWorkflow(MyMetric(),
                    dataset_path="Dataset/combined-data.json",
                    output_dir="Results", verbose=True)
wf.run()
wf.save("results_my_metric.json")
```

## API

### `MetricProtocol`

```python
from typing import Protocol, TypedDict, runtime_checkable

class MetricResult(TypedDict):
    class_score: float       # in [0.0, 1.0]
    attribute_score: float   # in [0.0, 1.0]
    association_score: float # in [0.0, 1.0]

@runtime_checkable
class MetricProtocol(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def version(self) -> str: ...
    def compute(self, reference_plantuml: str, generated_plantuml: str) -> MetricResult: ...
```

### `MetricWorkflow`

```python
class MetricWorkflow:
    def __init__(self, metric, dataset_path=None, output_dir=None, verbose=True): ...
    def run() -> dict: ...               # returns the full results dict
    def save(filename="results.json"): ...  # writes JSON, returns path
    @property
    def results: Optional[dict]: ...
    @property
    def errors: List[dict]: ...
```

### `run_workflow(metric, output_filename="results.json", verbose=True)`

A convenience function that creates a workflow, runs it, and saves in one
call.

### `DeltaCalculator`

```python
from Workflow.delta_calculator import DeltaCalculator

delta = DeltaCalculator.compute_comparison_delta(
    metric_results={"class_score": 0.65, "attribute_score": 0.42, "association_score": 0.16},
    human_metrics={"Class": {"f1": 0.625, ...}, "Attribute": {"f1": 0.605, ...}, "Association": {"f1": 0.241, ...}},
)
print(delta.to_dict())
# {"class_vs_f1": 0.025, "class_vs_precision": ..., "class_vs_recall": ...,
#  "attribute_vs_f1": ..., "association_vs_f1": ..., ...}

agg = DeltaCalculator.compute_aggregated(metric_results, human_metrics)
print(agg.to_dict())
# {"metric_average": ..., "human_f1_average": ..., "overall_delta": ...}
```

## Output JSON schema

See `../../Results/README.md` for the full schema written by `save()`.
