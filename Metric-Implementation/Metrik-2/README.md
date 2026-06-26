# Metrik-2 — Graph Edit Distance on Attributed UML Graphs

A similarity metric that treats each UML class diagram as an attributed graph
and computes the cost of transforming one into the other via graph edit
distance (GED), with the Hungarian algorithm used for optimal feature
assignment inside each vertex.

## Source paper

**Čech, P. (2019).** *Matching UML class models using graph edit distance.*
Expert Systems with Applications, 130, 206–224.
[DOI:10.1016/j.eswa.2019.04.008](https://doi.org/10.1016/j.eswa.2019.04.008)

### Abstract

The Unified Modelling Language (UML) class model is an essential constituent
in the software system development process and a considerable body of knowledge
is encompassed in the form of class model designs. A UML class model forms an
elaborate specification hierarchy and comparing different class models in order
to identify corresponding parts assumes considerable human expertise. To imitate
such human capacity an exponentially complex task needs to be addressed. Yet,
the research that involves UML class model matching focuses primarily only on
a design pattern detection and studies that tackle the problem of matching any
class models are rather rare. The aim of this study is to introduce a class
model distance computation framework that can be utilised for comparing class
models in model repositories. The framework exploits the relational structure
between model elements as well as internal element features to devise a distance
measure between any pair of class models. The relational structures of two
class models in the form of graphs are aligned using the graph edit distance
technique. The internal element feature distance computation deploys the
Hungarian algorithm for optimal assignment of any two-feature sets. The
distance computation framework reduces the comparison task to polynomial time
complexity. The study presents experimental performance analysis of the
proposed framework conducted using the precision-recall and receiver operating
characteristics curves and corresponding areas under the curves. The results
of the analysis indicate low false positive rates for both pairwise and
pattern detection tasks.

**Keywords:** UML class model matching; Graph edit distance; Design pattern
detection.

## Method

- **Graph construction:** each class diagram is encoded as an attributed graph
  (classes = vertices, associations = edges, attribute lists carried per
  vertex).
- **Internal feature distance:** for any two matched vertices, the Hungarian
  algorithm finds an optimal assignment of their attribute sets, minimizing
  the sum of per-attribute substitution costs.
- **Relational structure alignment:** the two attributed graphs are aligned
  by graph edit distance (vertex/edge insertion, deletion, substitution
  costs).
- **Output:** the three scores are derived from GED operations — vertex ops
  for `class_score`, per-vertex Hungarian cost for `attribute_score`, and
  edge ops for `association_score`. Strong on attributes, weak on
  associations.

## Layout

```
Metrik-2/
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
cd Metric-Implementation/Metrik-2
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
|   0.1867  |  0.1501  |  0.1834   |   0.1734        |

Polynomial-time comparison; runs in ~3 minutes on the full 39-pair test set.
