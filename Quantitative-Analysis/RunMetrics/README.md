# RunMetrics

Runnable scripts that wire each metric implementation into the `Workflow`
evaluation harness and write results to `Quantitative-Analysis/Results/`.

The directory is named `RunMetrics` to distinguish it from the **library**
`Workflow/` (singular, a Python package) — the scripts here are entry
points, not importable code.

## Files

```
Quantitative-Analysis/RunMetrics/
├── README.md           # this file
├── common.py           # shared helpers: paths, sys.path setup, module loader, NLTK
├── run_metrik1.py      # Metrik-1, rule-based, single-threaded
├── run_metrik2.py      # Metrik-2, graph edit distance, single-threaded
├── run_metrik3.py      # Metrik-3, UCG structural, single-threaded
├── run_metrik4.py      # Metrik-4, S-1 v1, ProcessPoolExecutor
├── run_metrik5.py      # Metrik-5, S-1 v2, ProcessPoolExecutor
└── run_all.py          # run all 5 sequentially, exit non-zero on any failure
```

## Quick start

From the **project root** (the directory containing `Quantitative-Analysis/`
and `Metric-Implementation/`):

```bash
python3 Quantitative-Analysis/RunMetrics/run_metrik1.py   # ~1s
python3 Quantitative-Analysis/RunMetrics/run_metrik2.py   # ~3min
python3 Quantitative-Analysis/RunMetrics/run_metrik3.py   # ~2min
python3 Quantitative-Analysis/RunMetrics/run_metrik4.py   # ~17min, ProcessPoolExecutor
python3 Quantitative-Analysis/RunMetrics/run_metrik5.py   # ~17min, ProcessPoolExecutor

# Or all five in order:
python3 Quantitative-Analysis/RunMetrics/run_all.py
```

Each script writes `Quantitative-Analysis/Results/results_metrikN.json`.

## How the runners work

The new project layout does **not** install any Python package. Instead, each
runner:

1. Calls `common.metric_paths(N)` to locate the metric's `Implementation-3/`
   (or `Implementation_3/`) directory.
2. Calls `common.setup_sys_path(impl_dir)` to add the metric root, the
   implementation dir, the parser, and the testset to `sys.path` so the
   metric's `from Parser.X import …` and `from Testset.X import …` statements
   resolve correctly.
3. Calls `common.load_metric_module(impl_dir)` which uses
   `importlib.util.spec_from_file_location` to load `metric.py` as a
   top-level module without needing `__init__.py`.
4. For Metrik-1/2/3: instantiates a small adapter that calls
   `metric(instructor_parsed_model, student_parsed_model)` and runs it through
   `Workflow.MetricWorkflow`.
5. For Metrik-4/5: calls `metric_module.get_metric()` to get a
   `MetricProtocol` instance, then uses
   `concurrent.futures.ProcessPoolExecutor` (via
   `diss_metric_worker.py`) for parallelism.

## Why multiprocessing for Metrik-4/5?

Metrik-4 and Metrik-5 both depend on the Triandini (2021) S-1 pipeline,
which uses NLTK / WordNet. Each comparison takes ~10-60 seconds. Running 39
comparisons single-threaded would take ~30 minutes; with 6 workers
(ProcessPoolExecutor) it drops to ~17 minutes on a typical machine.

## NLTK corpora

`common.ensure_nltk_corpora()` downloads `wordnet`, `omw-1.4`, `stopwords`,
`averaged_perceptron_tagger`, and `punkt` on first run. Idempotent.

## Output schema

See `../Results/README.md` for the JSON schema written by these runners.
