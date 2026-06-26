"""Shared fixtures for the metric tests.

The bundled ``data/combined-data.json`` ships the full 39-pair benchmark.
This module exposes the canonical ``LabTracker_0shot`` pair as a pytest
fixture so each metric can be exercised against known-good inputs.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple


_REPO_ROOT = Path(__file__).resolve().parents[1]
_DATASET_PATH = _REPO_ROOT / "data" / "combined-data.json"


def load_labtracker_0shot() -> Tuple[str, str, Dict[str, Dict[str, float]]]:
    """Return ``(reference_plantuml, generated_plantuml, human_metrics)``.

    Human metrics keys are ``"Class"``, ``"Attribute"``, ``"Association"``;
    each value has ``"precision"``, ``"recall"``, ``"f1"``.
    """
    with open(_DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    lab = data["models"]["LabTracker"]
    ref = lab["reference_plantuml"]
    gen = lab["generated_plantuml"]["0shot"]
    human = lab["metrics"]["0shot"]
    return ref, gen, human


def tiny_plantuml() -> Tuple[str, str]:
    """Return a 4-class minimal PlantUML pair for fast smoke tests.

    Designed so every metric produces a non-degenerate result quickly. The
    reference and generated differ in two class names and one attribute
    type, so all three scores (class, attribute, association) should be
    in (0, 1).
    """
    ref = (
        "@startuml\n"
        "class A { name : String }\n"
        "class B { value : Integer }\n"
        "class C {}\n"
        "A \"1\" -- \"*\" B\n"
        "@enduml\n"
    )
    gen = (
        "@startuml\n"
        "class Alpha { name : String }\n"
        "class B { value : String }\n"
        "class D {}\n"
        "A \"1\" -- \"*\" B\n"
        "@enduml\n"
    )
    return ref, gen