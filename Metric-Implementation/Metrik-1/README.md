# Metrik-1 — Rule-based Mistake Detection

A deterministic, rule-based metric that detects mistakes in a student-produced
UML class diagram (the "generated" model) by comparing it against a reference
diagram and classifying every discrepancy by type.

## Source paper

**Singh, P., Boubekeur, Y. & Mussbacher, G. (2022).** *Detecting mistakes in a
domain model.* Proceedings of the 25th International Conference on Model Driven
Engineering Languages and Systems: Companion Proceedings (MODELS '22),
pp. 257–266. ACM.
[DOI:10.1145/3550356.3561583](https://doi.org/10.1145/3550356.3561583)

### Abstract

Domain models are a fundamental part of software engineering, and it is
important for every software engineer to be taught the principles of domain
modeling. Instructors play a vital role in teaching students the skills required
to understand and design domain models. Instructors check models created by
students for mistakes by comparing them with a correct solution. While this did
not use to be an overwhelming task, this is not the case anymore nowadays due to
a rapid increase in the number of students wanting to become software
engineers, leading to larger class sizes. Hence, students may need to wait for
a longer time to get feedback on their solutions and the feedback may be more
superficial due to time constraints. In this paper, we propose a mistake
detection system (MDS) that aims to automate the manual approach of checking
student solutions and help save both students' and instructors' time. MDS
automatically indicates the exact location and the type of the mistake to the
student. At present, MDS accurately detects 83 out of 97 identified different
types of mistakes that may exist in a student solution. A prototype tool
verifies the feasibility of the proposed approach. When synonyms are considered
by MDS, recall of 0.93 and precision of 0.79 are achieved based on the results
for real student solutions. The proposed MDS takes us one step closer to
automating the existing manual approach, freeing up instructor time and helping
students learn domain modeling more effectively.

## Method

- **Class matching:** greedy alignment of reference classes to generated
  classes by name similarity.
- **Attribute checking:** for each matched class, attributes are compared
  name-by-name, type-by-type, with `missing`, `extra`, and `type-mismatch`
  categorized.
- **Association checking:** relationships are matched by endpoint classes and
  cardinalities; structural mistakes (`missing`, `extra`, `wrong-endpoint`,
  `wrong-cardinality`) are enumerated.
- **Output:** the three scores are derived from mistake counts per category,
  i.e. a model with zero mistakes scores 1.0, more mistakes lower the score.

## Layout

```
Metrik-1/
├── Implementation-1/     # Design iteration #1 (kept for history, not used)
├── Implementation-2/     # Design iteration #2 (kept for history, not used)
├── Implementation-3/     # Canonical implementation (used by the workflows)
│   ├── metric.py             # entry point
│   ├── metric_interface.py
│   ├── checkClasses.py
│   ├── checkMissing.py
│   ├── checkRelations.py
│   ├── mapClasses.py
│   ├── mapRelationships.py
│   └── normalize.py
├── Specification/         # Design specs: s1.md, s2.md, ...
├── Testset/              # Invariant validators and test scripts
└── Parser/               # PlantUML parser bundled per-metric
```

## Canonical entry point

`Implementation-3/metric.py:metric(m_ref, m_gen)` — returns a 3-score dict
`{"class_score", "attribute_score", "association_score"}`.

## Quick run

```bash
cd Metric-Implementation/Metrik-1
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
|   0.1471  |  0.2318  |  0.1309   |   0.1699        |

Rule-based and deterministic; runs in ~1 second on the full 39-pair test set.
