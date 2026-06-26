#!/usr/bin/env python3
"""
tS-metric.py — Compare full metric implementations (kimi vs glm)
on the full dataset, including mapping + mistakes.

Similar structure to tS-2.py but compares:
  1) class mapping
  2) relationship mapping
  3) final mistakes list
"""

import copy
import importlib.util
import json
import sys
from pathlib import Path

# ------------------------------------------------------------------
# Ensure Metrik-4 is on sys.path so that Parser / Testset resolve
# ------------------------------------------------------------------
D_METRIK_4 = Path(__file__).resolve().parent.parent
if str(D_METRIK_4) not in sys.path:
    sys.path.insert(0, str(D_METRIK_4))

for extra in (D_METRIK_4 / "Testset", D_METRIK_4 / "Parser"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from Parser import PlantUMLParser  # noqa: E402
from isValidMapping import isValidMapping  # noqa: E402
from isValidModel import isValidModel  # noqa: E402
from isValidMistakes import isValidMistakes  # noqa: E402


# ------------------------------------------------------------------
# Dynamic loader for Implementation-xxx/metric.py
# ------------------------------------------------------------------
def _load_metric(impl_dir: Path):
    """Import metric.py from impl_dir and return the metric function."""
    # Add impl_dir to path so its internal imports resolve
    if str(impl_dir) not in sys.path:
        sys.path.insert(0, str(impl_dir))

    # We need to import metric.py but it may have same module name.
    # Use spec_from_file_location with a unique module name.
    module_name = "metric_impl_" + impl_dir.name.replace("-", "_")
    spec = importlib.util.spec_from_file_location(
        module_name,
        str(impl_dir / "metric.py"),
    )
    mod = importlib.util.module_from_spec(spec)
    # Also make sure the impl_dir is on sys.path for its sub-imports
    sys.path.insert(0, str(impl_dir))
    spec.loader.exec_module(mod)
    return getattr(mod, "metric")


IMPL_KIMI = D_METRIK_4 / "Implementation-kimi"
IMPL_GML = D_METRIK_4 / "Implementation-gml"

metric_kimi = _load_metric(IMPL_KIMI)
metric_gml = _load_metric(IMPL_GML)


# ------------------------------------------------------------------
# Comparison helpers (same as tS-2)
# ------------------------------------------------------------------
def _class_mapping_to_dict(m) -> dict:
    return {
        "mapped_classes": sorted(
            [
                {
                    "student_class": mc.student_class,
                    "instructor_classes": sorted(mc.instructor_classes),
                    "mapping_type": mc.mapping_type.value,
                    "mapped_attributes": sorted(
                        [
                            {
                                "student_attr": ma.student_attr,
                                "instructor_attr": ma.instructor_attr,
                                "mapping_type": ma.mapping_type.value,
                            }
                            for ma in mc.mapped_attributes.mappings
                        ],
                        key=lambda x: x["student_attr"],
                    ),
                }
                for mc in m.class_mapping.mapped_classes
            ],
            key=lambda x: x["student_class"],
        ),
        "unmapped_instructor_classes": sorted(m.class_mapping.unmapped_instructor_classes),
        "unmapped_student_classes": sorted(m.class_mapping.unmapped_student_classes),
    }


def _relationship_mapping_to_dict(m) -> dict:
    return {
        "mapped_relationships": sorted(
            [
                {
                    "student_rel_index": mr.student_rel_index,
                    "instructor_rel_index": mr.instructor_rel_index,
                    "mapping_type": mr.mapping_type.value,
                    "is_inverted": mr.is_inverted,
                }
                for mr in m.relationship_mapping.mapped_relationships
            ],
            key=lambda x: (x["student_rel_index"], x["instructor_rel_index"]),
        ),
        "unmapped_instructor_relationships": sorted(m.relationship_mapping.unmapped_instructor_relationships),
        "unmapped_student_relationships": sorted(m.relationship_mapping.unmapped_student_relationships),
    }


def _mistakes_to_dict(mistakes) -> list:
    return sorted(
        [(m.mistake_id, m.description) for m in mistakes],
        key=lambda x: (x[0], x[1]),
    )


def compare_class_mappings(m1, m2) -> bool:
    return _class_mapping_to_dict(m1) == _class_mapping_to_dict(m2)


def compare_relationship_mappings(m1, m2) -> bool:
    return _relationship_mapping_to_dict(m1) == _relationship_mapping_to_dict(m2)


def compare_mistakes(m1, m2) -> bool:
    return _mistakes_to_dict(m1) == _mistakes_to_dict(m2)


# ------------------------------------------------------------------
# Main runner
# ------------------------------------------------------------------
def main():
    dataset_path = D_METRIK_4 / "Dataset" / "combined-data.json"
    with open(dataset_path) as f:
        data = json.load(f)

    parser = PlantUMLParser(strict=True)

    total = 0
    class_match = 0
    class_diff = 0
    rel_match = 0
    rel_diff = 0
    mistakes_match = 0
    mistakes_diff = 0
    parse_errors = 0
    invalid_models = 0
    invalid_class_maps = 0
    invalid_rel_maps = 0
    invalid_mistakes = 0
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
                map_and_mistakes_kimi = metric_kimi(ref_parsed, gen_parsed)
            except Exception as exc:
                errors.append(f"ERROR-METRIC-KIMI  {label}: {exc}")
                continue

            try:
                map_and_mistakes_gml = metric_gml(ref_parsed, gen_parsed)
            except Exception as exc:
                errors.append(f"ERROR-METRIC-GML  {label}: {exc}")
                continue

            # Validate mistakes
            if not isValidMistakes(map_and_mistakes_kimi):
                invalid_mistakes += 1
                errors.append(f"INVAL-MISTAKES-KIMI  {label}")
            if not isValidMistakes(map_and_mistakes_gml):
                invalid_mistakes += 1
                errors.append(f"INVAL-MISTAKES-GML  {label}")

            if compare_mistakes(map_and_mistakes_kimi, map_and_mistakes_gml):
                mistakes_match += 1
            else:
                mistakes_diff += 1
                print(f"M-DIFF {label}")

    # --- Summary ---
    print(f"\n{'=' * 50}")
    print(f"Total cases              : {total}")
    print(f"Parse errors             : {parse_errors}")
    print(f"Invalid models           : {invalid_models}")
    print(f"Invalid mistakes         : {invalid_mistakes}")
    print(f"Mistakes matches         : {mistakes_match}")
    print(f"Mistakes diffs           : {mistakes_diff}")

    if errors:
        other = len(errors) - parse_errors - invalid_models - invalid_mistakes
        print(f"Other errors             : {other}")
        print(f"\nErrors / details:")
        for e in errors:
            print("  ", e)


if __name__ == "__main__":
    main()
