"""
tS-3-new — Partial-order (Halbordnung / Quasiordnung) axioms for Metrik-1.

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

  Base metric:         q_base(m)  = -len( mistakes(R, m) )
  Normalized metric:   q_norm(m) = mean( class_score, attr_score, assoc_score )

The induced relation is:
  a ≤_impl b   ⇔   q_impl(a) ≤ q_impl(b)

Axioms verified per implementation:
  • Reflexivität    – q(a) == q(a)            (determinism / self-consistency)
  • Antisymmetrie   – if q(a) == q(b) then a and b are equivalent by the metric
  • Transitivität   – q(a) ≤ q(b) ∧ q(b) ≤ q(c) ⇒ q(a) ≤ q(c)

Cross-implementation property:
  • Konsistenz      – both implementations induce the same ranking on M:
                      sign(q_base(a) - q_base(b)) == sign(q_norm(a) - q_norm(b))
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

from Parser.parser import PlantUMLParser
from isValidModel import isValidModel
from isValidMistakes import isValidMistakes

# ------------------------------------------------------------------
# Load Implementation-gml-normalized
# ------------------------------------------------------------------
sys.path.insert(0, str(_D4 / "Implementation-gml-normalized"))
if "metric" in sys.modules:
    del sys.modules["metric"]
from metric import metric as metric_normalized  # noqa: E402

# ------------------------------------------------------------------
# Load Implementation-gml (returns mistakes list)
# ------------------------------------------------------------------
sys.path.insert(0, str(_D4 / "Implementation-gml"))
if "metric_base" in sys.modules:
    del sys.modules["metric_base"]
_spec = importlib.util.spec_from_file_location("metric_base",
                                                  _D4 / "Implementation-gml" / "metric.py")
_metric_base_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_metric_base_mod)
metric_base = _metric_base_mod.metric

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


def _run_base(inst, stud):
    """Run base metric and return scalar quality q_base = -len(mistakes)."""
    mistakes = metric_base(inst, stud)
    assert isinstance(mistakes, list), "metric_base must return a list"
    assert isValidMistakes(mistakes), "returned mistakes are not valid"
    return -len(mistakes)


def _run_normalized(inst, stud):
    """Run normalized metric and return scalar quality q_norm = mean(scores)."""
    result = metric_normalized(inst, stud)
    assert isinstance(result, dict), "metric_normalized must return a dict"
    dims = ["class_score", "attribute_score", "association_score"]
    for k in dims:
        assert k in result, f"missing key {k}"
        assert isinstance(result[k], float), f"{k} must be float, got {type(result[k])}"
        assert 0.0 <= result[k] <= 1.0, f"{k}={result[k]} out of range [0.0, 1.0]"
    return _mean([result[k] for k in dims])


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

    # Quality values for each implementation
    q_base = {
        "a": _run_base(R, a),
        "b": _run_base(R, b),
        "c": _run_base(R, c),
        "d": _run_base(R, d),
    }
    q_norm = {
        "a": _run_normalized(R, a),
        "b": _run_normalized(R, b),
        "c": _run_normalized(R, c),
        "d": _run_normalized(R, d),
    }

    print("Quality values computed:")
    print(f"  base metric  (q_base): {q_base}")
    print(f"  norm metric  (q_norm): {q_norm}")
    print()

    failures = []

    # ==================================================================
    # 1. Reflexivität:  ∀x ∈ {a,b,c,d} : q(x) ≤ q(x)   (equality)
    # ==================================================================
    try:
        for impl_name, q in [("base", q_base), ("norm", q_norm)]:
            for label in ["a", "b", "c", "d"]:
                # A model compared to itself must yield identical quality.
                model_by_label = {"a": a, "b": b, "c": c, "d": d}
                if impl_name == "base":
                    q_self = _run_base(R, model_by_label[label])
                else:
                    q_self = _run_normalized(R, model_by_label[label])
                _assert_approx(q_self, q[label], tol=0.0,
                               label=f"Reflexivität [{impl_name}, {label}]")
        print("PASS [1]: Reflexivität  (a ≤ a, b ≤ b, c ≤ c, d ≤ d)")
    except Exception as exc:
        failures.append(str(exc))
        print(f"FAIL [1]: Reflexivität -> {exc}")

    # ==================================================================
    # 2. Antisymmetrie:  q(x) ≤ q(y) ∧ q(y) ≤ q(x)  ⇒  q(x) == q(y)
    #     (in a metric-induced preorder, different models may share
    #      the same quality → they form an equivalence class)
    # ==================================================================
    try:
        pairs = [("a", "b"), ("a", "c"), ("a", "d"), ("b", "c"), ("b", "d"), ("c", "d")]
        for impl_name, q in [("base", q_base), ("norm", q_norm)]:
            for x, y in pairs:
                qx, qy = q[x], q[y]
                if qx <= qy and qy <= qx:
                    # In a true partial order this would imply x == y.
                    # For a metric-induced preorder it means x and y are
                    # indistinguishable by the metric (same quality).
                    _assert_approx(qx, qy, tol=0.0,
                                   label=f"Antisymmetrie [{impl_name}, {x}={y}]")
                    print(f"  INFO: Antisymmetrie [{impl_name}] — {x} and {y} are in the "
                          f"same equivalence class (q={qx:.4f})")
        print("PASS [2]: Antisymmetrie  (no contradictions found)")
    except Exception as exc:
        failures.append(str(exc))
        print(f"FAIL [2]: Antisymmetrie -> {exc}")

    # ==================================================================
    # 3. Transitivität:  q(x) ≤ q(y) ∧ q(y) ≤ q(z)  ⇒  q(x) ≤ q(z)
    #     We test the full chain a ≤ b ≤ c ≤ d plus all skip-step pairs.
    # ==================================================================
    try:
        chains = [
            ("a", "b", "c"),   # worse ≤ baseline ≤ better
            ("b", "c", "d"),   # baseline ≤ better ≤ perfect
            ("a", "b", "d"),   # worse ≤ baseline ≤ perfect
            ("a", "c", "d"),   # worse ≤ better ≤ perfect
            ("a", "b", "c"),   # (duplicate for completeness)
        ]
        for impl_name, q in [("base", q_base), ("norm", q_norm)]:
            for x, y, z in chains:
                qx, qy, qz = q[x], q[y], q[z]
                if qx <= qy and qy <= qz:
                    assert qx <= qz, (
                        f"Transitivität [{impl_name}] failed: "
                        f"{x}(q={qx:.4f}) ≤ {y}(q={qy:.4f}) ≤ {z}(q={qz:.4f}) BUT {x} > {z}"
                    )
        print("PASS [3]: Transitivität  (all chains verified)")
    except Exception as exc:
        failures.append(str(exc))
        print(f"FAIL [3]: Transitivität -> {exc}")

    # ==================================================================
    # 4. Konsistenz — both implementations must induce the same ranking
    # ==================================================================
    try:
        labels = ["a", "b", "c", "d"]
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                x, y = labels[i], labels[j]
                sign_base = q_base[x] - q_base[y]
                sign_norm = q_norm[x] - q_norm[y]
                # They must have the same sign (or one/both be zero).
                if not ((sign_base == 0 and sign_norm == 0) or
                        (sign_base > 0 and sign_norm > 0) or
                        (sign_base < 0 and sign_norm < 0)):
                    raise AssertionError(
                        f"Konsistenz violated for ({x}, {y}): "
                        f"base_diff={sign_base:.4f}, norm_diff={sign_norm:.4f}"
                    )
        print("PASS [4]: Konsistenz  (both implementations rank identically)")
    except Exception as exc:
        failures.append(str(exc))
        print(f"FAIL [4]: Konsistenz -> {exc}")

    # ==================================================================
    # Summary
    # ==================================================================
    print()
    if failures:
        print(f"FAILED: {len(failures)} test(s)")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
