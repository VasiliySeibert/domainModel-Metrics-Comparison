"""
diss_metric_worker.py — Top-level worker function for ProcessPoolExecutor.

Required because ``concurrent.futures`` workers must be picklable, which means
the callable must live at module top level (not be a closure or a method of a
locally-defined class).

Each worker process:
  1. Adds the impl's root directory to sys.path so ``diss_metric``,
     ``metric_interface``, ``Parser``, ``Specification``, and ``Testset`` all
     resolve correctly.
  2. Imports the metric instance and the validator into module-level globals.
  3. Processes one (model, setting) pair and returns a small dict.

The module deliberately keeps a *single* module-level ``_metric`` and
``_validate`` set up by ``init_worker`` so we don't re-parse WordNet / re-load
NLTK data per call.
"""
import sys
from pathlib import Path

_metric = None
_validate = None


def init_worker(pkg_root: str) -> None:
    """Initializer run once per worker process.

    Args:
        pkg_root: Absolute path of the per-impl root directory (parent of this
                  file). Added to ``sys.path`` so that ``diss_metric``,
                  ``metric_interface``, ``Parser``, etc. all resolve.
    """
    global _metric, _validate

    root = Path(pkg_root).resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from Implementation_3.metric import get_metric  # noqa: WPS433
    from Implementation_3.metric_interface import validate_metric_result  # noqa: WPS433

    _metric = get_metric()
    _validate = validate_metric_result


def process_one(args):
    """Worker function: run the metric on a single (model, setting) pair.

    Args:
        args: tuple of (model_name, setting, ref_uml, gen_uml, human_dict)

    Returns:
        dict with keys:
            status: "ok" | "error" | "skipped"
            model, setting: identifying strings (always present)
            + metric / human fields on success
            + error message on failure
    """
    model_name, setting, ref_uml, gen_uml, human = args

    if not gen_uml:
        return {
            "status": "skipped",
            "model": model_name,
            "setting": setting,
        }

    try:
        result = _metric.compute(ref_uml, gen_uml)
    except Exception as exc:
        return {
            "status": "error",
            "model": model_name,
            "setting": setting,
            "error": repr(exc),
        }

    if not _validate(result):
        return {
            "status": "error",
            "model": model_name,
            "setting": setting,
            "error": "invalid MetricResult",
        }

    return {
        "status": "ok",
        "model": model_name,
        "setting": setting,
        "human_class_f1": human.get("Class", {}).get("f1"),
        "human_attribute_f1": human.get("Attribute", {}).get("f1"),
        "human_association_f1": human.get("Association", {}).get("f1"),
        "class_score": result["class_score"],
        "attribute_score": result["attribute_score"],
        "association_score": result["association_score"],
    }
