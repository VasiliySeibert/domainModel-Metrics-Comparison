# Metric-Implementation

The 5 similarity metrics, organized as a
design history. Renamed from `Metrics/` during the project restructuring.

## Overview

Each metric takes two PlantUML class diagrams (reference + generated) and
returns a 3-score dict:

```python
{"class_score": float, "attribute_score": float, "association_score": float}
#                              each in [0.0, 1.0]
```

These three scores are aligned with the human-evaluated categories
(Class, Attribute, Association) so they can be compared directly against
human F1 scores.

## Layout

```
Metric-Implementation/
├── Metrik-1/             Rule-based mistake detection
├── Metrik-2/             Graph edit distance
├── Metrik-3/             UCG / structural similarity
├── Metrik-4/             S-1 (semantic + structural) projection v1
└── Metrik-5/             S-1 (semantic + structural) projection v2
```

Each `Metrik-N/` follows the same layout:

```
Metrik-N/
├── Implementation-1/     # Design iteration #1 (kept for history, not used)
├── Implementation-2/     # Design iteration #2 (kept for history, not used)
├── Implementation-3/     # Canonical implementation (used by the workflows)
├── Specification/         # Design specs: s1.md, s2.md, etc.
├── Testset/              # Per-metric invariant validators and test scripts
├── Parser/               # The PlantUML parser bundled per-metric
└── diss_metric_worker.py # (Metrik-4 / Metrik-5 only) ProcessPoolExecutor worker
```

**Note on `Implementation-1` and `Implementation-2`:** these directories are
intentionally kept on disk as part of the design history but are not wired
into the workflow. The new `RunMetrics/run_metrikN.py` scripts use
`Implementation-3` (or `Implementation_3` for Metrik-4/5) only.

## The 5 metrics

For the authoritative per-metric description (method, layout, entry point, quick
run), see the `README.md` inside each `Metrik-N/` directory. The table below is
a high-level index with the underlying source paper for each metric.

| Metrik | Source paper                                                                                 | One-line summary                                                                                          |
|-------:|----------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
|    1   | Singh, Boubekeur & Mussbacher (2022), MODELS '22 — [DOI:10.1145/3550356.3561583](https://doi.org/10.1145/3550356.3561583) | Rule-based mistake detection in domain models, classifies 83 of 97 identified mistake types.                |
|    2   | Čech (2019), *Expert Systems with Applications* — [DOI:10.1016/j.eswa.2019.04.008](https://doi.org/10.1016/j.eswa.2019.04.008) | Graph edit distance on attributed UML class graphs, with Hungarian assignment for internal features.      |
|    3   | Yuan, Yan & Ma (2020), *Requirements Engineering* — [DOI:10.1007/s00766-019-00317-w](https://doi.org/10.1007/s00766-019-00317-w) | Structural similarity via UML Common Graph (UCG) with intra/inter-cluster edit distance.                  |
|    4   | Triandini (2021), *IJIES* — [DOI:10.22266/IJIES2021.0430.06](https://doi.org/10.22266/IJIES2021.0430.06) | S-1 pipeline (semantic WordNet + structural GED) — projection v1.                                          |
|    5   | Triandini (2021), *IJIES* — [DOI:10.22266/IJIES2021.0430.06](https://doi.org/10.22266/IJIES2021.0430.06) | S-1 pipeline (semantic WordNet + structural GED) — projection v2.                                          |

## Background / Source papers

The four publications that ground this metric family:

1. **Singh, P., Boubekeur, Y. & Mussbacher, G. (2022).** *Detecting mistakes in
   a domain model.* Proceedings of the 25th International Conference on Model
   Driven Engineering Languages and Systems: Companion Proceedings (MODELS
   '22), pp. 257–266. ACM.
   [DOI:10.1145/3550356.3561583](https://doi.org/10.1145/3550356.3561583)
   → Used by **Metrik-1**.

2. **Čech, P. (2019).** *Matching UML class models using graph edit distance.*
   Expert Systems with Applications, 130, 206–224.
   [DOI:10.1016/j.eswa.2019.04.008](https://doi.org/10.1016/j.eswa.2019.04.008)
   → Used by **Metrik-2**.

3. **Yuan, Z., Yan, L. & Ma, Z. (2020).** *Structural similarity measure
   between UML class diagrams based on UCG.* Requirements Engineering, 25(2),
   213–229.
   [DOI:10.1007/s00766-019-00317-w](https://doi.org/10.1007/s00766-019-00317-w)
   → Used by **Metrik-3**.

4. **Triandini, E. (2021).** *Automated Class Diagram Assessment using
   Semantic and Structural Similarities.* International Journal of Intelligent
   Engineering and Systems.
   [DOI:10.22266/IJIES2021.0430.06](https://doi.org/10.22266/IJIES2021.0430.06)
   → Used by **Metrik-4** (S-1 projection v1) and **Metrik-5** (S-1 projection v2).

### Performance summary (39 pairs, MAD = mean |metric − human_f1|)

| Metrik | Class MAD | Attr MAD | Assoc MAD | **Overall MAD** |
|-------:|----------:|---------:|----------:|----------------:|
|    1   |   0.1471  |  0.2318  |  0.1309   |   0.1699        |
|    2   |   0.1867  |  0.1501  |  0.1834   |   0.1734        |
|    3   |   0.1720  |  0.2127  |  0.1258   |   0.1702        |
|    4   |   0.0866  |  0.1365  |  0.2745   |   0.1658        |
|    5   |   0.0738  |  0.1460  |  0.2582   |   **0.1593**    |

## How to run a metric

Use the workflow scripts in `../RunMetrics/`:

```bash
# From the project root
python3 Quantitative-Analysis/RunMetrics/run_metrik1.py   # rule-based, ~1s
python3 Quantitative-Analysis/RunMetrics/run_metrik2.py   # graph edit distance, ~3min
python3 Quantitative-Analysis/RunMetrics/run_metrik3.py   # UCG, ~2min
python3 Quantitative-Analysis/RunMetrics/run_metrik4.py   # S-1 projection v1, ~17min (NLTK + multiprocessing)
python3 Quantitative-Analysis/RunMetrics/run_metrik5.py   # S-1 projection v2, ~17min (NLTK + multiprocessing)

# Or all five sequentially:
python3 Quantitative-Analysis/RunMetrics/run_all.py
```

Each script writes `Quantitative-Analysis/Results/results_metrikN.json` with the same schema.

## Per-metric local dev

Each `Metrik-N/Implementation-3/` (or `Implementation_3/`) contains a
`metric.py` that exposes the canonical entry point. To run a quick smoke
test inside one metric dir:

```bash
cd Metric-Implementation/Metrik-1
PYTHONPATH="Implementation-3:.:Testset:Parser" \
  python3 -c "
from metric import metric
from Parser import PlantUMLParser
# ... parse two PlantUML strings, call metric(m1, m2), print result
"
```

Or for Metrik-4/5, use the `get_metric()` factory:

```bash
cd Metric-Implementation/Metrik-4
PYTHONPATH="Implementation_3:.:Testset:Parser" \
  python3 -c "
from metric import get_metric
m = get_metric()
print(m.compute(ref_uml, gen_uml))
"
```
