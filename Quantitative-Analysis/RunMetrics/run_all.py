#!/usr/bin/env python3
"""Run all 5 metrics sequentially and save Quantitative-Analysis/Results/results_metrik*.json.

Exits non-zero if any metric fails.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = [
    "run_metrik1.py",
    "run_metrik2.py",
    "run_metrik3.py",
    "run_metrik4.py",
    "run_metrik5.py",
]


def main() -> int:
    failed = []
    for name in SCRIPTS:
        print(f"\n{'=' * 70}\n=== Running {name} ===\n{'=' * 70}")
        result = subprocess.run(
            [sys.executable, str(HERE / name)],
            cwd=str(HERE.parent.parent),
        )
        if result.returncode != 0:
            failed.append(name)
            print(f"!!! {name} exited with code {result.returncode}")
        else:
            print(f"=== {name} OK ===")
    print()
    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1
    print("All 5 metrics completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
