# Metrik-3 — Structural Similarity via UCG

A purely structural similarity metric that represents each UML class diagram as
a **UML Common Graph (UCG)** and compares two UCGs by combining an
intra-cluster edit distance (within each class) with an inter-cluster edit
distance (between classes).

## Source paper

**Yuan, Z., Yan, L. & Ma, Z. (2020).** *Structural similarity measure between
UML class diagrams based on UCG.* Requirements Engineering, 25(2), 213–229.
[DOI:10.1007/s00766-019-00317-w](https://doi.org/10.1007/s00766-019-00317-w)

### Abstract

In software reuse, the reuse of UML class diagram produced in design phase has
received more attention due to the important influence on the following
developing process. The reuse is based on similarity. The similarity between
class diagrams contains semantic and structural aspects. The existing works
focus on semantic similarity, while the structural similarity is little paid
attention to. The structure of class diagram can be categorized into two
aspects: intra-structure and inter-structure. The intra-structure refers to
the composition of each class, and the inter-structure is represented as the
relationships between classes. So, the structural similarity measure should be
carried out from these two aspects. In this paper, we propose to use a graph
named UML class graph (UCG) to represent a class diagram for the structural
similarity measure. An algorithm based on UCG Maximum Common Subgraph Sequence
is proposed for the inter-structure similarity measure, and UCG edit distance
is proposed and introduced to the intra-structure similarity measure. The
experimental results show that our proposed approach is effective within a
domain or across domains.

## Method

- **UML Common Graph (UCG) construction:** each class diagram is encoded as a
  UCG capturing both intra-structure (attribute/operation composition of each
  class) and inter-structure (associations between classes).
- **Intra-structure similarity:** for each pair of matched classes, attributes
  are compared via UCG edit distance, producing an `intraSim` score.
- **Inter-structure similarity:** the class-level topology is aligned using
  the UCG Maximum Common Subgraph Sequence algorithm, producing an `interSim`
  score.
- **Output:** `class_score` and `attribute_score` derive from `intraSim`;
  `association_score` derives from `interSim`. Structural-only — no lexical /
  semantic matching, hence fast.

## Layout

```
Metrik-3/
├── Implementation-1/     # Design iteration #1 (kept for history, not used)
├── Implementation-2/     # Design iteration #2 (kept for history, not used)
├── Implementation-3/     # Canonical implementation (used by the workflows)
├── Specification/         # Design specs: s1.md, s2.md, ...
├── Testset/              # Invariant validators and test scripts
└── Parser/               # PlantUML parser bundled per-metric
```

## Canonical entry point

`Implementation-3/metric.py:metric(m_ref, m_gen)` — returns a 3-score dict
`{"class_score", "attribute_score", "association_score"}`.

## Quick run

```bash
cd Metric-Implementation/Metrik-3
PYTHONPATH="Implementation-3:.:Testset:Parser" \
  python3 -c "
from metric import metric
from Parser import PlantUMLParser
ref = PlantUMLParser.parse_file('path/to/reference.puml')
gen = PlantUMLParser.parse_file('path/to/generated.puml')
print(metric(ref, gen))
"
```

## Performance (39 pairs, MAD = mean |metric − human_f1|)

| Class MAD | Attr MAD | Assoc MAD | **Overall MAD** |
|----------:|---------:|----------:|----------------:|
|   0.1720  |  0.2127  |  0.1258   |   0.1702        |

Structural-only and fast; runs in ~2 minutes on the full 39-pair test set.
