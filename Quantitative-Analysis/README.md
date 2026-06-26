# Quantitative-Analysis

The data, parser, and evaluation workflow for the project.

This directory was renamed during the project
restructuring. The dummy metric (`dummyMetric/`) was dropped; the workflow
harness was renamed to `Workflow/`.

## Contents

```
Quantitative-Analysis/
├── Dataset/
│   └── combined-data.json        # The 8 models × 5 LLM settings dataset (39 pairs)
├── Workflow/                     # Reusable metric-evaluation harness (Python package)
│   ├── __init__.py               # exports MetricProtocol, MetricWorkflow, run_workflow, ...
│   ├── workflow.py
│   ├── data_loader.py
│   ├── delta_calculator.py
│   ├── results_writer.py
│   ├── metric_interface.py
│   ├── README.md
│   └── tests/
├── RunMetrics/                    # Runnable scripts: run_metrik{1..5}.py + run_all.py
│   ├── common.py
│   ├── run_metrik1.py            # ~1s
│   ├── run_metrik2.py            # ~3min
│   ├── run_metrik3.py            # ~2min
│   ├── run_metrik4.py            # ~17min, ProcessPoolExecutor
│   ├── run_metrik5.py            # ~17min, ProcessPoolExecutor
│   ├── run_all.py
│   └── README.md
├── Results/                      # All run outputs
│   ├── results_metrik1..5.json
│   ├── metrics_comparison.json
│   ├── metrics_comparison_histogram.png
│   ├── .baseline/                # preserved for verification
│   └── README.md
└── Notebooks/                    # Walkthrough notebook
    ├── comparisons_walkthrough.ipynb
    ├── _build_walkthrough.py
    └── README.md
```

> **Note:** the PlantUML parser is per-metric, at
> `../../Metric-Implementation/Metrik-N/Parser/`. Each metric implementation
> ships its own copy to keep the metric self-contained.

## Dataset (`Dataset/combined-data.json`)

- **8 Domain Models**: LabTracker, CelO, TSS, SHAS, OTS, Block, TileO, HBMS
- **5 LLM Settings** per model: `0shot`, `1shot_BTMS`, `1shot_H2S`, `2shots`, `CoT`
- **Human Evaluation Metrics**: Precision/recall/F1 for Class, Attribute, Association
- **39 comparison pairs** (one per (model, setting))

See `Workflow/README.md` for the schema; the dataset is loaded by `Workflow.data_loader.DataLoader`.

## Parser

A robust PlantUML class-diagram parser. Converts PlantUML text into structured
Python data objects (`ParsedModel`, `ParsedClass`, `ParsedRelationship`, etc.).
Supports all syntax patterns found in the dataset: classes, enums, all
relationship types (association, inheritance, composition, aggregation),
cardinalities, labels, comments, notes.

The parser is **per-metric** (each `Metric-Implementation/Metrik-N/Parser/`
ships its own copy) to keep each metric self-contained. The class signature
is identical across copies.

```python
from Parser import PlantUMLParser

parser = PlantUMLParser(strict=True)
model = parser.parse(plantuml_string)
print(f"Classes: {len(model.classes)}, Relationships: {len(model.relationships)}")
```

## Workflow (`Workflow/`) — the library

A reusable evaluation **library** (a Python package). Note the singular name
— this is the *importable* `Workflow` package, distinct from `RunMetrics/`
(the runnable scripts that drive it). Takes a metric object implementing
`MetricProtocol` (with `name`, `version`, `compute(ref_uml, gen_uml) -> MetricResult`),
loads the dataset, runs the metric on all 39 (model, setting) pairs, computes
deltas against the human-evaluated F1 scores, and writes a `results.json`
with the schema documented in `Results/README.md`.

```python
from Workflow import MetricWorkflow, MetricResult

class MyMetric:
    @property
    def name(self): return "MyMetric"
    @property
    def version(self): return "1.0.0"
    def compute(self, ref_uml, gen_uml) -> MetricResult:
        return MetricResult(class_score=0.5, attribute_score=0.5, association_score=0.5)

wf = MetricWorkflow(MyMetric(), dataset_path="Dataset/combined-data.json",
                    output_dir="Results", verbose=True)
wf.run()
wf.save("results_my_metric.json")
```

The actual metric runnables live in `RunMetrics/run_metrik{1..5}.py` and
delegate to `Workflow.MetricWorkflow` (or to the multiprocessing pool for
Metrik-4/5). See `RunMetrics/README.md` and `Results/README.md`.
