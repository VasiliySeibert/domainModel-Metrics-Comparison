#!/usr/bin/env python3
"""Run Metrik-5 over the dataset using a process pool.

The S-1 metric underlying Metrik-5 is expensive (NLTK / WordNet graph
traversals). The metric package ships ``diss_metric_worker.py``, a top-level
picklable worker compatible with ``concurrent.futures.ProcessPoolExecutor``.
We reuse it verbatim and post-process its output into the same JSON shape
that ``MetricWorkflow`` produces, so downstream tools see a uniform
``results_*.json`` file across all Metrik variants.
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from multiprocessing import get_context
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (
    DATASET_PATH,
    RESULTS_DIR,
    WORKFLOW_DIR,
    ensure_nltk_corpora,
    metric_paths,
)

_, impl_dir = metric_paths(5)
METRIC_ROOT = impl_dir.parent

# Make diss_metric_worker importable
sys.path.insert(0, str(METRIC_ROOT))
from diss_metric_worker import init_worker, process_one  # noqa: E402

# Add Workflow so we can reuse DeltaCalculator
sys.path.insert(0, str(WORKFLOW_DIR.parent))
from Workflow.delta_calculator import DeltaCalculator  # noqa: E402

try:
    from tqdm import tqdm
    _HAS_TQDM = True
except ImportError:
    _HAS_TQDM = False


METRIC_NAME = "metrik-5"
METRIC_VERSION = "1.0.0"
MAX_WORKERS = min(6, max(1, (os.cpu_count() or 2) - 1))
SETTINGS = ["0shot", "1shot_BTMS", "1shot_H2S", "2shots", "CoT"]


def _build_task_list(dataset_path: Path):
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tasks = []
    metadata = data.get("metadata", {})
    settings = metadata.get("settings_included", SETTINGS)
    for model_key, model_data in data.get("models", {}).items():
        ref_uml = model_data.get("reference_plantuml", "")
        generated = model_data.get("generated_plantuml", {})
        metrics_human = model_data.get("metrics", {})
        for setting in settings:
            gen_uml = generated.get(setting)
            human = metrics_human.get(setting)
            if gen_uml is None or human is None:
                continue
            tasks.append((model_key, setting, ref_uml, gen_uml, human))
    return tasks, data, metadata


def _to_comparison_dict(payload: dict, data: dict) -> dict:
    model_key = payload["model"]
    model_data = data["models"].get(model_key, {})
    setting = payload["setting"]
    metric_results = {
        "class_score": payload["class_score"],
        "attribute_score": payload["attribute_score"],
        "association_score": payload["association_score"],
    }
    human_metrics = model_data.get("metrics", {}).get(setting, {})
    delta = DeltaCalculator.compute_comparison_delta(metric_results, human_metrics)
    aggregated = DeltaCalculator.compute_aggregated(metric_results, human_metrics)
    return {
        "comparison_id": f"{model_key}_{setting}",
        "model_key": model_key,
        "model_full_name": model_data.get("full_name", model_key),
        "setting": setting,
        "reference_plantuml": model_data.get("reference_plantuml", ""),
        "generated_plantuml": model_data.get("generated_plantuml", {}).get(
            setting, ""
        ),
        "metric_results": metric_results,
        "human_metrics": human_metrics,
        "delta": delta.to_dict(),
        "aggregated": aggregated.to_dict(),
    }


def main() -> int:
    started = time.time()
    ensure_nltk_corpora()

    tasks, data, _ = _build_task_list(DATASET_PATH)
    print(f"Running {METRIC_NAME} on {len(tasks)} pairs (workers={MAX_WORKERS})")

    comparisons: dict = {}
    errors: list = []
    successful = 0
    failed = 0

    ctx = get_context("spawn")
    with ProcessPoolExecutor(
        max_workers=MAX_WORKERS,
        mp_context=ctx,
        initializer=init_worker,
        initargs=(str(METRIC_ROOT),),
    ) as pool:
        futures = [pool.submit(process_one, t) for t in tasks]
        iterator = as_completed(futures)
        if _HAS_TQDM:
            iterator = tqdm(
                iterator,
                total=len(futures),
                desc="metrik-5",
                unit="pair",
            )
        for fut in iterator:
            try:
                payload = fut.result()
            except Exception as exc:
                errors.append({"comparison_id": "?", "error": repr(exc)})
                failed += 1
                continue
            status = payload.get("status")
            if status == "ok":
                comp = _to_comparison_dict(payload, data)
                comparisons[comp["comparison_id"]] = comp
                successful += 1
            else:
                errors.append(
                    {
                        "comparison_id": f"{payload.get('model', '?')}_{payload.get('setting', '?')}",
                        "error": payload.get("error", status),
                    }
                )
                failed += 1

    summary = DeltaCalculator.compute_summary_statistics(comparisons)
    results = {
        "metadata": {
            "generated_timestamp": datetime.now().isoformat(),
            "metric_name": METRIC_NAME,
            "metric_version": METRIC_VERSION,
            "dataset_source": str(DATASET_PATH),
            "total_comparisons": successful + failed,
            "successful_comparisons": successful,
            "failed_comparisons": failed,
        },
        "comparisons": comparisons,
        "summary_statistics": summary,
        "errors": errors,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / "results_metrik5.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    elapsed = time.time() - started
    print(f"\nWall time: {elapsed:.1f}s")
    print(f"Processed: {successful} ok, {failed} failed")
    print(f"Results saved to: {output_path}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
