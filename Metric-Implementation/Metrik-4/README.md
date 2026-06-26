# Metrik-4 — S-1 Pipeline (semantic + structural) — Projection v1

A hybrid similarity metric that combines a **semantic** WordNet-based class
matcher with a **structural** graph edit distance on attributes and
associations, then projects the three pipelines onto a single class /
attribute / association scoring scheme (projection v1).

> Shares its source paper with **Metrik-5** — both implement two different
> projections of the same S-1 pipeline (Triandini 2021).

## Source paper

**Triandini, E. (2021).** *Automated Class Diagram Assessment using Semantic
and Structural Similarities.* International Journal of Intelligent Engineering
and Systems.
[DOI:10.22266/IJIES2021.0430.06](https://doi.org/10.22266/IJIES2021.0430.06)

### Abstract

Class diagrams show classes in software and the relationships between those
classes. A class diagram is a unified modeling language diagram commonly used
in education. Thus, an assessment of class diagrams is essential for teachers
who usually have students produce class diagrams based on predetermined
projects. Teachers assess student-produced class diagrams based on an answer
key. However, teachers have a problem with a lack of consistency in assessment
as teachers can use different standards between answers. This research
attempts to approach class diagram assessment automatically. The proposed
approach consists of two assessments: semantic and structural similarities.
Semantic similarity is calculated using lexical information in the class
diagram, and structural similarity is calculated using the diagram's
structure, ignoring its lexical information. Our results show that experts see
semantic and structural similarities equally during assessment. The proposed
approach shows substantial agreement with experts in class diagram similarity
assessment. Therefore, the proposed approach can automatically assess class
diagram similarity as reliably as experts can.

## Method

- **Semantic class matching:** class names are matched using a WordNet-based
  lexical similarity (handles synonyms such as `Customer` ↔ `Client`).
- **Structural attribute matching:** for each semantically matched class
  pair, attribute lists are compared via property similarity (`propSim`).
- **Structural association matching:** the inter-class topology is compared
  via relationship similarity (`relSim`).
- **Projection v1:** the three sub-scores (semantic class, `propSim`
  attribute, `relSim` association) are reported as-is.
- **Output:** a 3-score dict aligned to the human-evaluated Class, Attribute,
  and Association categories.

## Layout

```
Metrik-4/
├── Implementation-1/      # Design iteration #1 (kept for history, not used)
├── Implementation-2/      # Design iteration #2 (kept for history, not used)
├── Implementation_3/      # Canonical implementation (used by the workflows)
│                           # (note the underscore, not hyphen)
│   ├── metric.py              # entry point (factory get_metric())
│   ├── metric_interface.py
│   ├── metric_models.py
│   ├── metric_normalize.py
│   ├── metric_primitives.py
│   ├── metric_semantic.py
│   ├── metric_structural.py
│   ├── s1.md
│   └── metric-information.txt
├── Specification/         # Design specs: s1.md, s2.md, ...
├── Testset/              # Invariant validators and test scripts
├── Parser/               # PlantUML parser bundled per-metric
└── diss_metric_worker.py # ProcessPoolExecutor worker (multiprocessing)
```

## Canonical entry point

`Implementation_3/metric.py:get_metric()` returns a worker whose `compute(ref,
gen)` method produces the 3-score dict. The workflow uses
`diss_metric_worker.py` for parallel execution.

## Quick run

```bash
cd Metric-Implementation/Metrik-4
PYTHONPATH="Implementation_3:.:Testset:Parser" \
  python3 -c "
from metric import get_metric
m = get_metric()
print(m.compute(ref_uml, gen_uml))
"
```

## Performance (39 pairs, MAD = mean |metric − human_f1|)

| Class MAD | Attr MAD | Assoc MAD | **Overall MAD** |
|----------:|---------:|----------:|----------------:|
|   0.0866  |  0.1365  |  0.2745   |   0.1658        |

**Best class MAD of the family.** Uses NLTK + WordNet; runs in ~17 minutes on
the full 39-pair test set with multiprocessing.
