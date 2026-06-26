#!/usr/bin/env python3
"""
tS-3-new — Partial-order (Halbordnung / Quasiordnung) axioms for S2 normalized metric.

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

  Normalized metric:   q_norm(m) = mean(class_score, attr_score, assoc_score)

The induced relation is:
  a ≤_impl b   ⇔   q_impl(a) ≤ q_impl(b)

Axioms verified per implementation:
  • Reflexivität    – q(a) == q(a)            (determinism / self-consistency)
  • Antisymmetrie   – if q(a) == q(b) then a and b are equivalent by the metric
  • Transitivität   – q(a) ≤ q(b) ∧ q(b) ≤ q(c) ⇒ q(a) ≤ q(c)

Cross-implementation property (if more than one S2 impl is available):
  • Konsistenz      – both implementations induce the same ranking on M:
                      sign(q_impl1(a) - q_impl1(b)) == sign(q_impl2(a) - q_impl2(b))
                      for every pair (a, b).
"""

import sys
import importlib.util
from pathlib import Path

# ------------------------------------------------------------------
# Path setup
# ------------------------------------------------------------------
_D4 = Path(__file__).resolve().parent.parent
_ROOT = _D4.parent.parent

sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_D4))

from Parser import PlantUMLParser
from Testset.isValidModel import isValidModel
from Specification.metric_interface import validate_metric_result


# ------------------------------------------------------------------
# Helper: dynamic loader for an Implementation-xxx/metric.py file
# ------------------------------------------------------------------
def _load_metric(impl_dir: Path):
    """Import metric.py from impl_dir and return the metric function."""
    sys.path.insert(0, str(_D4.parent))
    sys.path.insert(0, str(_D4))
    sys.path.insert(0, str(impl_dir))

    module_name = "metric_impl_" + impl_dir.name.replace("-", "_")
    spec = importlib.util.spec_from_file_location(
        module_name,
        str(impl_dir / "metric.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "metric")


# ------------------------------------------------------------------
# Discover available S2 implementations
# ------------------------------------------------------------------
IMPL_KIMI = _D4 / "Implementation-kimi-extended"
IMPL_GML = _D4 / "Implementation-glm-extended"

metric_impls = []
if IMPL_KIMI.exists():
    try:
        metric_impls.append(("kimi-extended", _load_metric(IMPL_KIMI)))
    except Exception as exc:
        print(f"WARNING: could not load {IMPL_KIMI.name}: {exc}")

if IMPL_GML.exists():
    try:
        metric_impls.append(("glm", _load_metric(IMPL_GML)))
    except Exception as exc:
        print(f"WARNING: could not load {IMPL_GML.name}: {exc}")

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


def _run_metric(inst, stud, metric_fn):
    """Run S2 normalized metric and return scalar quality q = mean(scores)."""
    result = metric_fn(inst, stud)
    assert isinstance(result, dict), "metric must return a dict"
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
    parser = PlantUMLParser(strict=True)
    instructor = parser.parse(INSTRUCTOR_UML)
    worse = parser.parse(WORSE_UML)
    baseline = parser.parse(BASELINE_UML)
    better = parser.parse(BETTER_UML)
    perfect = parser.parse(PERFECT_UML)

    # Sanity: all models structurally valid
    for name, model in [
        ("instructor", instructor),
        ("worse", worse),
        ("baseline", baseline),
        ("better", better),
        ("perfect", perfect),
    ]:
        assert isValidModel(model), f"{name} model invalid"

    # Named references for mathematical clarity
    R = instructor
    a = worse          # WORSE model
    b = baseline       # BASELINE model
    c = better         # BETTER model
    d = perfect        # PERFECT model

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
    # ==================================================================
    try:
        for impl_name, metric_fn in metric_impls:
            for label in ["a", "b", "c", "d"]:
                model_by_label = {"a": a, "b": b, "c": c, "d": d}
                q_self = _run_metric(R, model_by_label[label], metric_fn)[0]
                _assert_approx(q_self, q_results[impl_name][label], tol=0.0,
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
