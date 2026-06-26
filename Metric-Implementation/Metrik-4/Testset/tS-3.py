#!/usr/bin/env python3
"""
tS-3.py — Partial-order (Halbordnung / Quasiordnung) axioms for Metrik-4.

Mathematical background
-----------------------
A relation ≤ on a set M is a *preorder* (Quasiordnung) if it satisfies:
  1. Reflexivität:    ∀a ∈ M : a ≤ a
  2. Transitivität:   ∀a,b,c ∈ M : a ≤ b ∧ b ≤ c ⇒ a ≤ c

If, in addition, antisymmetry holds,
  3. Antisymmetrie:   ∀a,b ∈ M : a ≤ b ∧ b ≤ a ⇒ a = b
it becomes a *partial order* (Halbordnung).

Because two *different* UML models can receive the exact same quality value,
a score-based metric induces a **preorder** on models, not necessarily a
strict partial order.  The quotient set (grouping models with identical
quality) *does* form a partial order.

What we test
------------
Let R = instructor reference model (fixed).
Let M = {WORSE, BASELINE, BETTER, PERFECT}.

For each implementation we define a quality function q : M → ℝ:

  q_norm(m) = mean(class_score, attribute_score, association_score)

For Metrik-4 the 3-field MetricResult is built from the 7-field
SimilarityResult (Triandini S-1) via the projection
    class_score       <- semantic
    attribute_score   <- propSim
    association_score <- relSim

The induced relation is:
  a ≤_impl b   ⇔   q_impl(a) ≤ q_impl(b)

Axioms verified per implementation:
  • Reflexivität    – q(a) == q(a)            (determinism / self-consistency)
  • Antisymmetrie   – if q(a) == q(b) then a and b are equivalent by the metric
  • Transitivität   – q(a) ≤ q(b) ∧ q(b) ≤ q(c) ⇒ q(a) ≤ q(c)

Cross-implementation property (if more than one S-1 impl is available):
  • Konsistenz      – all implementations induce the same ranking on M:
                      sign(q_impl1(a) - q_impl1(b)) == sign(q_impl2(a) - q_impl2(b))
                      for every pair (a, b).

Implementations under test
--------------------------
  1. local          – Metrik-4/Implementation_3/metric.metric  (3-field dict)

Run from the Metrik-4/ directory:
    python -m Testset.tS-3
"""

import sys
from pathlib import Path

# ------------------------------------------------------------------
# Path setup
# ------------------------------------------------------------------
_PKG = Path(__file__).resolve().parent.parent       # = Metrik-4/

sys.path.insert(0, str(_PKG))

from Parser import PlantUMLParser
from Testset.metric_invariants import isValidParsedModel
from Implementation_3.metric import metric as local_metric
from Implementation_3.metric_interface import validate_metric_result


# ------------------------------------------------------------------
# Metrik-4 projection: 7-field SimilarityResult -> 3-field MetricResult
# ------------------------------------------------------------------
def _project_similarity_to_metric(result, projection: str) -> dict:
    """Project a 7-field SimilarityResult onto the 3-field MetricResult schema.

    Args:
        result: object with attributes similarity, semantic, structural,
                propSim, relSim, intraSim, interSim (all floats in [0, 1]).
        projection: "9-1" or "9-2" — selects which S-1 sub-scores map onto
                    class_score, attribute_score, association_score.

    Returns:
        Dict with keys class_score, attribute_score, association_score.
    """
    if projection == "9-1":
        return {
            "class_score":      float(result.semantic),
            "attribute_score":  float(result.propSim),
            "association_score": float(result.relSim),
        }
    if projection == "9-2":
        return {
            "class_score":       float(result.intraSim),
            "attribute_score":   float(result.intraSim),
            "association_score": float(result.interSim),
        }
    raise ValueError(f"unknown projection: {projection!r}")


PROJECTION = "9-1"


# ------------------------------------------------------------------
# Helper: subprocess runner for an external implementation's metric
# ------------------------------------------------------------------
def _make_external_metric(impl_root: Path, projection: str):
    """Return a callable (uml1: str, uml2: str) -> 3-field MetricResult dict
    that runs ``<impl_root>/Developing-DISS-Metric/Specification/metric.py``
    in an isolated subprocess and projects the 7-field SimilarityResult onto
    the 3-field MetricResult schema.

    Subprocess isolation is necessary because kimi/glm ship their own
    ``Parser``/``Testset`` packages, which would otherwise shadow the local
    Metrik-4 modules.
    """
    import json as _json
    import subprocess as _sp

    spec_dir = impl_root / "Developing-DISS-Metric"

    def _wrapped(uml1: str, uml2: str) -> dict:
        code = f"""
import sys, json, traceback
sys.path.insert(0, {str(spec_dir)!r})
from Parser import PlantUMLParser
from Specification.metric import metric

p = PlantUMLParser(strict=True)
m1 = p.parse({uml1!r})
m2 = p.parse({uml2!r})
r = metric(m1, m2)

if {projection!r} == '9-1':
    out = {{'class_score': float(r.semantic),
            'attribute_score': float(r.propSim),
            'association_score': float(r.relSim)}}
elif {projection!r} == '9-2':
    out = {{'class_score': float(r.intraSim),
            'attribute_score': float(r.intraSim),
            'association_score': float(r.interSim)}}
else:
    raise ValueError('unknown projection: ' + {projection!r})

print(json.dumps(out, default=float))
"""
        proc = _sp.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"external metric {impl_root.name} failed (exit={proc.returncode}): "
                f"{proc.stderr[-500:]}"
            )
        out_line = ""
        for line in reversed(proc.stdout.strip().splitlines()):
            line = line.strip()
            if line:
                out_line = line
                break
        if not out_line:
            raise RuntimeError(
                f"external metric {impl_root.name} produced no output: "
                f"stdout={proc.stdout[-300:]!r} stderr={proc.stderr[-300:]!r}"
            )
        return _json.loads(out_line)

    _wrapped.__name__ = f"metric_via_{impl_root.name}"
    return _wrapped


# ------------------------------------------------------------------
# Discover available implementations
# ------------------------------------------------------------------
KIMI_ROOT = _PKG / "Implementation-kimi"
GLM_ROOT = _PKG / "Implementation-glm"


def _wrap_local_metric(local_metric_fn):
    """Wrap the local Metrik-4 metric so it accepts PlantUML strings.

    The local ``Implementation_extended.metric.metric`` already returns the 3-field
    MetricResult dict; we just need to parse the UML inputs first.
    """
    def _wrapped(uml1: str, uml2: str) -> dict:
        m1 = parser.parse(uml1)
        m2 = parser.parse(uml2)
        return local_metric_fn(m1, m2)
    _wrapped.__name__ = "local_metric_wrapped"
    return _wrapped


metric_impls = []

try:
    parser = PlantUMLParser(strict=True)
    metric_impls.append(("local", _wrap_local_metric(local_metric)))
except Exception as exc:
    print(f"WARNING: could not load local metric: {exc}")

if KIMI_ROOT.exists():
    try:
        metric_impls.append(("kimi-extended", _make_external_metric(KIMI_ROOT, PROJECTION)))
    except Exception as exc:
        print(f"WARNING: could not load {KIMI_ROOT.name}: {exc}")

if GLM_ROOT.exists():
    try:
        metric_impls.append(("glm-extended", _make_external_metric(GLM_ROOT, PROJECTION)))
    except Exception as exc:
        print(f"WARNING: could not load {GLM_ROOT.name}: {exc}")

if not metric_impls:
    print("ERROR: no metric implementations available")
    sys.exit(1)

print(f"Loaded {len(metric_impls)} implementation(s):")
for name, _func in metric_impls:
    print(f"  - {name}")
print()


# ------------------------------------------------------------------
# Test data
# ------------------------------------------------------------------

INSTRUCTOR_UML = """@startuml
class PISystem
class Person {
    String name
    String address
}
class Role
class Victim
class PoliceStation {
    String address
}
class PoliceOfficer {
    int badgeNumber
}
class Case {
    Date startDate
    Date endDate
}
Role <|-- Victim
Role <|-- PoliceOfficer
Person "1" -- "1..2" Role : roles
PISystem "1" -- "0..*" Person : persons
PISystem *-- "0..*" Victim
Victim "0..*" -- "1..*" Case
PISystem "1" *-- "0..*" Case
PISystem "1" *-- "0..*" PoliceStation
PoliceStation "1" -- "0..*" PoliceOfficer : workLocation
PoliceOfficer "0..*" -- "0..*" Case : worksOnCases
PISystem "1" *-- "0..*" PoliceOfficer
@enduml
"""

# WORSE – systematically removes overlap with instructor.
WORSE_UML = """@startuml
class City
class Mayor {
    String name
    String party
}
class Officer {
    int officerId
}
class Suspect {
    String alias
}
class File {
    Date date
    String description
}
class Meeting {
    String topic
    Date scheduled
}
City "1" -- "0..*" Mayor
City "1" -- "0..*" Officer
Mayor "1" -- "0..*" Meeting
Officer "0..*" -- "0..*" File
Suspect "0..*" -- "1..*" File
@enduml
"""

# BASELINE – realistic student submission with several mistakes.
BASELINE_UML = """@startuml
class PISystem
class Person {
  String name
  String address
}
class Victim
class PoliceOfficer {
  String badgeNumber
}
class PoliceStation {
  String address
}
class Cases {
  String objective
  Date startDate
}
Person <|-- Victim
Person <|-- PoliceOfficer
PISystem "1" *-- "0..*" Person : persons
PISystem "1" *-- "0..*" PoliceStation : policeStations
PISystem "1" *-- "0..*" Cases : cases
PoliceStation "1" *-- "0..*" PoliceOfficer
Victim "0..*" -- "1..*" Cases : victims
PoliceOfficer "1" -- "0..*" Cases : assignedOfficer
@enduml
"""

# BETTER – overlap increased compared with BASELINE.
BETTER_UML = """@startuml
class PISystem
class Person {
    String name
    String address
}
class Role
class Victim
class PoliceStation {
    String address
}
class PoliceOfficer {
    String badgeNumber
}
class Case {
    Date startDate
    Date endDate
}
Role <|-- Victim
Role <|-- PoliceOfficer
Person "1" -- "1..2" Role : roles
PISystem "1" *-- "0..*" Person : persons
PISystem "1" *-- "0..*" PoliceStation : policeStations
PISystem "1" *-- "0..*" Case : cases
PoliceStation "1" *-- "0..*" PoliceOfficer
Victim "0..*" -- "1..*" Case : victims
PoliceOfficer "1" -- "0..*" Case : assignedOfficer
@enduml
"""

PERFECT_UML = INSTRUCTOR_UML


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _mean(values):
    return sum(values) / len(values) if values else 0.0


def _assert_approx(actual, expected, tol=0.001, label=""):
    if abs(actual - expected) > tol:
        raise AssertionError(
            f"{label}: expected {expected}, got {actual} (diff={abs(actual - expected)})"
        )


def _run_metric(uml_inst: str, uml_stud: str, metric_fn):
    """Run the metric on (instructor_uml, student_uml) and return (q, raw_dict).

    The metric_fn must accept two PlantUML strings and return a 3-field dict
    with keys class_score, attribute_score, association_score whose values
    are floats in [0, 1].
    """
    result = metric_fn(uml_inst, uml_stud)
    assert isinstance(result, dict), f"metric must return a dict, got {type(result)}"
    dims = ["class_score", "attribute_score", "association_score"]
    for k in dims:
        assert k in result, f"missing key {k}"
        assert isinstance(result[k], float), f"{k} must be float, got {type(result[k])}"
        assert 0.0 <= result[k] <= 1.0, f"{k}={result[k]} out of range [0.0, 1.0]"
    assert validate_metric_result(result), "result fails validate_metric_result"
    return _mean([result[k] for k in dims]), result


# ------------------------------------------------------------------
# Main test harness
# ------------------------------------------------------------------

def main():
    # Sanity-check that the local parser considers all 5 models valid. We do
    # NOT use the parsed models to drive the metric — each implementation is
    # responsible for parsing the UML strings itself, because kimi/glm have a
    # different ParsedModel class than Metrik-4.
    parser = PlantUMLParser(strict=True)
    for name, uml in [
        ("instructor", INSTRUCTOR_UML),
        ("worse", WORSE_UML),
        ("baseline", BASELINE_UML),
        ("better", BETTER_UML),
        ("perfect", PERFECT_UML),
    ]:
        assert isValidParsedModel(parser.parse(uml)), f"{name} model invalid (local parser)"

    # Named references for mathematical clarity (UML strings)
    R = INSTRUCTOR_UML
    a = WORSE_UML        # WORSE model
    b = BASELINE_UML     # BASELINE model
    c = BETTER_UML       # BETTER model
    d = PERFECT_UML      # PERFECT model

    # Compute quality values for each implementation
    q_results = {}
    detailed_results = {}
    for impl_name, metric_fn in metric_impls:
        q_results[impl_name] = {
            "a": _run_metric(R, a, metric_fn)[0],
            "b": _run_metric(R, b, metric_fn)[0],
            "c": _run_metric(R, c, metric_fn)[0],
            "d": _run_metric(R, d, metric_fn)[0],
        }
        detailed_results[impl_name] = {
            "a": _run_metric(R, a, metric_fn)[1],
            "b": _run_metric(R, b, metric_fn)[1],
            "c": _run_metric(R, c, metric_fn)[1],
            "d": _run_metric(R, d, metric_fn)[1],
        }

    print("Quality values computed:")
    for impl_name, q in q_results.items():
        print(f"  {impl_name}: {q}")
    print()

    failures = []
    all_pass = True

    # ==================================================================
    # 1. Reflexivität: ∀x ∈ {a,b,c,d} : q(x) == q(x)
    #    Tolerance: 1e-3. Two calls to the same (impl, model) must agree
    #    within this tolerance. Implementations may use non-deterministic
    #    numerical primitives (e.g. random sampling in graph matching),
    #    so we allow a small floating-point drift while still catching
    #    genuine non-determinism > 0.1%.
    # ==================================================================
    try:
        for impl_name, metric_fn in metric_impls:
            for label in ["a", "b", "c", "d"]:
                uml_by_label = {"a": a, "b": b, "c": c, "d": d}
                q_self = _run_metric(R, uml_by_label[label], metric_fn)[0]
                _assert_approx(q_self, q_results[impl_name][label], tol=1e-3,
                               label=f"Reflexivität [{impl_name}, {label}]")
        print("PASS [1]: Reflexivität  (a ≤ a, b ≤ b, c ≤ c, d ≤ d)")
    except Exception as exc:
        failures.append(str(exc))
        all_pass = False
        print(f"FAIL [1]: Reflexivität -> {exc}")

    # ==================================================================
    # 2. Antisymmetrie: q(x) ≤ q(y) ∧ q(y) ≤ q(x) ⇒ q(x) == q(y)
    # ==================================================================
    try:
        pairs = [("a", "b"), ("a", "c"), ("a", "d"), ("b", "c"), ("b", "d"), ("c", "d")]
        for impl_name, q in q_results.items():
            for x, y in pairs:
                qx, qy = q[x], q[y]
                # For a metric-induced preorder, if qx == qy they are in the same
                # equivalence class.
                if qx <= qy and qy <= qx:
                    _assert_approx(qx, qy, tol=0.0,
                                   label=f"Antisymmetrie [{impl_name}, {x}={y}]")
                    print(f"  INFO: Antisymmetrie [{impl_name}] — {x} and {y} are in the "
                          f"same equivalence class (q={qx:.4f})")
        print("PASS [2]: Antisymmetrie  (no contradictions found)")
    except Exception as exc:
        failures.append(str(exc))
        all_pass = False
        print(f"FAIL [2]: Antisymmetrie -> {exc}")

    # ==================================================================
    # 3. Transitivität: q(a) ≤ q(b) ≤ q(c) ≤ q(d)
    # ==================================================================
    try:
        chains = [
            ("a", "b", "c"),   # worse ≤ baseline ≤ better
            ("b", "c", "d"),   # baseline ≤ better ≤ perfect
            ("a", "b", "d"),   # worse ≤ baseline ≤ perfect
            ("a", "c", "d"),   # worse ≤ better ≤ perfect
        ]
        for impl_name, q in q_results.items():
            for x, y, z in chains:
                qx, qy, qz = q[x], q[y], q[z]
                if not (qx <= qy and qy <= qz):
                    raise AssertionError(
                        f"Transitivität [{impl_name}] failed: "
                        f"{x}(q={qx:.4f}) ≤ {y}(q={qy:.4f}) ≤ {z}(q={qz:.4f})"
                    )
                if not (qx <= qz):
                    raise AssertionError(
                        f"Transitivität [{impl_name}] failed: "
                        f"{x}(q={qx:.4f}) ≤ {z}(q={qz:.4f})"
                    )
        print("PASS [3]: Transitivität  (all chains verified)")
    except Exception as exc:
        failures.append(str(exc))
        all_pass = False
        print(f"FAIL [3]: Transitivität -> {exc}")

    # ==================================================================
    # 4. Monotonie / expected ordering:
    #    q(worse) ≤ q(baseline) ≤ q(better) ≤ q(perfect)
    # ==================================================================
    try:
        for impl_name, q in q_results.items():
            assert q["a"] <= q["b"] <= q["c"] <= q["d"], (
                f"Monotonie [{impl_name}] failed: "
                f"worse={q['a']:.4f}, baseline={q['b']:.4f}, "
                f"better={q['c']:.4f}, perfect={q['d']:.4f}"
            )
        print("PASS [4]: Monotonie  (worse ≤ baseline ≤ better ≤ perfect)")
    except Exception as exc:
        failures.append(str(exc))
        all_pass = False
        print(f"FAIL [4]: Monotonie -> {exc}")

    # ==================================================================
    # 5. Perfect = 1.0   (or near 1.0 within tolerance)
    # ==================================================================
    try:
        for impl_name, q in q_results.items():
            _assert_approx(q["d"], 1.0, tol=0.01,
                           label=f"Perfect score [{impl_name}]")
        print("PASS [5]: Perfect score ≈ 1.0")
    except Exception as exc:
        failures.append(str(exc))
        all_pass = False
        print(f"FAIL [5]: Perfect score -> {exc}")

    # ==================================================================
    # 6. Konsistenz — if multiple implementations, same ranking
    # ==================================================================
    if len(metric_impls) >= 2:
        try:
            labels = ["a", "b", "c", "d"]
            for i in range(len(labels)):
                for j in range(i + 1, len(labels)):
                    x, y = labels[i], labels[j]
                    signs = []
                    for impl_name in q_results.keys():
                        diff = q_results[impl_name][x] - q_results[impl_name][y]
                        if diff > 0.001:
                            signs.append(1)
                        elif diff < -0.001:
                            signs.append(-1)
                        else:
                            signs.append(0)
                    # All non-zero signs must agree
                    non_zero = [s for s in signs if s != 0]
                    if non_zero and not all(s == non_zero[0] for s in non_zero):
                        raise AssertionError(
                            f"Konsistenz violated for ({x}, {y}): signs={signs}"
                        )
            print("PASS [6]: Konsistenz  (all implementations rank identically)")
        except Exception as exc:
            failures.append(str(exc))
            all_pass = False
            print(f"FAIL [6]: Konsistenz -> {exc}")
    else:
        print("SKIP [6]: Konsistenz  (only one implementation available)")

    # ==================================================================
    # Summary
    # ==================================================================
    print()
    if all_pass:
        print("ALL TESTS PASSED")
        sys.exit(0)
    else:
        print(f"FAILED: {len(failures)} test(s)")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
