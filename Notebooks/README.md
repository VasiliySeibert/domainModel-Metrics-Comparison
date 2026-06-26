# Notebooks

Narrated walkthroughs of the `domain-model-metrics` package.

## `quantitative_results_walkthrough.ipynb`

A self-contained notebook that loads the 5 pre-computed
`results_metrikN.json` files and reproduces:

1. The headline **MAD table** (per metric × element, 39 pairs).
2. The **RQ2 consistency statistics** (residual std, Pearson r,
   bias) and the **per-element best-metric decision table**.
3. The **4 qualitative failure-mode patterns** (constant offset,
   linear rescalable, random noise, close-but-doesn't-track-ordering).
4. A **per-pair scatter plot** (5 metrics × 3 elements = 15 panels)
   showing `metric_score` vs `human_f1` with the y = x reference line
   and the OLS fit.

The notebook is read-only with respect to the data (no metric
re-runs) and executes in a few seconds.

## How to regenerate the notebook

The notebook is built from the Python source
[`_build_walkthrough.py`](./_build_walkthrough.py) so the markdown
content stays in clean Python literals. To regenerate after editing:

```bash
python Notebooks/_build_walkthrough.py
```

## How to run the notebook

```bash
pip install -e ".[notebooks]"
jupyter lab Notebooks/quantitative_results_walkthrough.ipynb
```