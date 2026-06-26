#!/usr/bin/env python3
"""
tS-2.py — Compare Metrik-2 metric implementations (KIMI vs GLM)
on the full S1 dataset.

Comparison criteria:
  1) total_scaled_distance within ±0.1 tolerance
  2) operation counts within ±1 tolerance
  3) isValidEditInformations passes for both
"""

import importlib.util
import json
import sys
from pathlib import Path

# ------------------------------------------------------------------
# Ensure the metric root is on sys.path
# ------------------------------------------------------------------
D_METRIK_BASE = Path(__file__).resolve().parent.parent
if str(D_METRIK_BASE) not in sys.path:
    sys.path.insert(0, str(D_METRIK_BASE))

for extra in (D_METRIK_BASE / "Testset", D_METRIK_BASE / "Parser"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from Parser import PlantUMLParser  # noqa: E402
from isValidModel import isValidModel  # noqa: E402
from isValidEditInformations import isValidEditInformations  # noqa: E402


# ------------------------------------------------------------------
# Dynamic loader for Implementation-xxx/metric.py
# ------------------------------------------------------------------
def _load_metric(impl_dir: Path):
    """Import metric.py from impl_dir and return the metric function."""
    sys.path.insert(0, str(impl_dir.parent))          # Developing-DISS-Metric
    sys.path.insert(0, str(impl_dir))                  # Implementation-xxx

    module_name = "metric_impl_" + impl_dir.name.replace("-", "_")
    spec = importlib.util.spec_from_file_location(
        module_name,
        str(impl_dir / "metric.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, "metric")


IMPL_KIMI = D_METRIK_BASE / "Implementation-kimi"
IMPL_GML = D_METRIK_BASE / "Implementation-glm-extended"

metric_kimi = _load_metric(IMPL_KIMI)
metric_gml = _load_metric(IMPL_GML)


# ------------------------------------------------------------------
# Comparison helpers
# ------------------------------------------------------------------
def distance_match(d1: float, d2: float, tol: float = 0.1) -> bool:
    return abs(d1 - d2) <= tol


def count_match(c1: int, c2: int, tol: int = 1) -> bool:
    return abs(c1 - c2) <= tol


# ------------------------------------------------------------------
# Main runner
# ------------------------------------------------------------------
def main():
    dataset_path = D_METRIK_BASE / "Dataset" / "combined-data.json"
    with open(dataset_path) as f:
        data = json.load(f)

    parser = PlantUMLParser(strict=True)

    total = 0
    dist_match = 0
    dist_diff = 0
    ops_match = 0
    ops_diff = 0
    both_valid = 0
    parse_errors = 0
    invalid_models = 0
    invalid_ei = 0
    errors = []

    for model_name, model_data in data["models"].items():
        ref_uml = model_data["reference_plantuml"]
        generated = model_data.get("generated_plantuml", {})

        for setting, gen_uml in generated.items():
            label = f"{model_name}/{setting}"
            total += 1

            # --- Parse ---
            try:
                ref_parsed = parser.parse(ref_uml)
                gen_parsed = parser.parse(gen_uml)
            except Exception as exc:
                parse_errors += 1
                errors.append(f"PARSE  {label}: {exc}")
                continue

            # --- Validate models ---
            if not isValidModel(ref_parsed):
                invalid_models += 1
                errors.append(f"INVAL-MODEL  {label} (reference)")
                continue
            if not isValidModel(gen_parsed):
                invalid_models += 1
                errors.append(f"INVAL-MODEL  {label} (generated)")
                continue

            # --- Run full metric ---
            try:
                result_kimi = metric_kimi(ref_parsed, gen_parsed)
            except Exception as exc:
                errors.append(f"ERROR-METRIC-KIMI  {label}: {exc}")
                continue

            try:
                result_gml = metric_gml(ref_parsed, gen_parsed)
            except Exception as exc:
                errors.append(f"ERROR-METRIC-GML  {label}: {exc}")
                continue

            # Validate EditInformations
            valid_kimi = isValidEditInformations(result_kimi)
            valid_gml = isValidEditInformations(result_gml)
            if not valid_kimi:
                invalid_ei += 1
                errors.append(f"INVAL-EI-KIMI  {label}")
            if not valid_gml:
                invalid_ei += 1
                errors.append(f"INVAL-EI-GML  {label}")
            if valid_kimi and valid_gml:
                both_valid += 1

            # Compare total_scaled_distance (tolerance ±0.1)
            if distance_match(result_kimi.total_scaled_distance, result_gml.total_scaled_distance):
                dist_match += 1
            else:
                dist_diff += 1
                print(
                    f"DIST-DIFF {label}  "
                    f"kimi={result_kimi.total_scaled_distance:.4f} "
                    f"glm={result_gml.total_scaled_distance:.4f}"
                )

            # Compare operation counts (tolerance ±1)
            if count_match(len(result_kimi.operations), len(result_gml.operations)):
                ops_match += 1
            else:
                ops_diff += 1
                print(
                    f"OPS-DIFF {label}  "
                    f"kimi={len(result_kimi.operations)} "
                    f"glm={len(result_gml.operations)}"
                )

    # --- Summary ---
    print(f"\n{'=' * 60}")
    print(f"Total cases              : {total}")
    print(f"Parse errors             : {parse_errors}")
    print(f"Invalid models           : {invalid_models}")
    print(f"Invalid EditInformations : {invalid_ei}")
    print(f"Both outputs valid       : {both_valid}")
    print(f"Distance matches (±0.1)  : {dist_match}")
    print(f"Distance diffs           : {dist_diff}")
    print(f"Ops-count matches (±1)   : {ops_match}")
    print(f"Ops-count diffs          : {ops_diff}")

    if errors:
        other = len(errors) - parse_errors - invalid_models - invalid_ei
        print(f"Other errors             : {other}")
        print(f"\nErrors / details:")
        for e in errors:
            print("  ", e)


if __name__ == "__main__":
    main()
