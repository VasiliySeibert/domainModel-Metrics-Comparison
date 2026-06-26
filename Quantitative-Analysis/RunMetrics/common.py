"""Shared helpers for RunMetrics/run_metrik*.py scripts."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Tuple


ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT / "Quantitative-Analysis" / "Dataset" / "combined-data.json"
RESULTS_DIR = ROOT / "Quantitative-Analysis" / "Results"
WORKFLOW_DIR = ROOT / "Quantitative-Analysis" / "Workflow"


def metric_paths(metric_id: int) -> Tuple[Path, str]:
    """Return (impl_dir, impl_subdir_name) for the given metric id.

    The implementation directory differs in name between Metrik-1..3
    ("Implementation-3", hyphen) and Metrik-4/5 ("Implementation_3", underscore).
    """
    metric_dir = ROOT / "Metric-Implementation" / f"Metrik-{metric_id}"
    if metric_id in (1, 2, 3):
        impl_dir = metric_dir / "Implementation-3"
    elif metric_id in (4, 5):
        impl_dir = metric_dir / "Implementation_3"
    else:
        raise ValueError(f"Unknown metric id: {metric_id}")
    if not impl_dir.is_dir():
        raise FileNotFoundError(f"Implementation dir not found: {impl_dir}")
    return metric_dir, impl_dir


def setup_sys_path(impl_dir: Path) -> None:
    """Add the impl dir and its parent to sys.path so the metric loads cleanly.

    For Metrik-1..3, sibling modules (Testset/*.py, Parser/*.py) are needed.
    For Metrik-4/5, the `Implementation_3` package is also needed so that
    `from Implementation_3.metric_X import …` resolves.

    The `Parser/` directory is **NOT** added directly to sys.path — adding it
    there causes `from models import …` to load `Parser/models.py` as a
    top-level module, while `from Parser.models import …` loads it as a
    package member, creating two different module objects and breaking
    identity checks on shared classes (e.g. ``RelationshipType`` enums).
    """
    impl_parent = impl_dir.parent
    # Add the metric root and the impl dir
    for p in (impl_dir, impl_parent):
        sp = str(p)
        if sp not in sys.path:
            sys.path.insert(0, sp)
    # For Metrik-4/5, also add the impl dir as a package path
    if impl_dir.name == "Implementation_3":
        # Add the metric root (parent of Implementation_3) so that
        # `from Implementation_3.metric import …` resolves.
        if str(impl_parent) not in sys.path:
            sys.path.insert(0, str(impl_parent))
    # Always add the Workflow package parent so `from Workflow import …` works
    if str(WORKFLOW_DIR.parent) not in sys.path:
        sys.path.insert(0, str(WORKFLOW_DIR.parent))


def load_metric_module(impl_dir: Path):
    """Load ``metric.py`` from ``impl_dir`` as a top-level module.

    Uses ``importlib.util.spec_from_file_location`` so we don't depend on
    ``__init__.py`` being present in the implementation directory.
    """
    metric_py = impl_dir / "metric.py"
    if not metric_py.is_file():
        raise FileNotFoundError(f"metric.py not found in {impl_dir}")
    spec = importlib.util.spec_from_file_location(
        f"metrik_module_{impl_dir.parent.name}", metric_py
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {metric_py}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ensure_nltk_corpora() -> None:
    """Download NLTK corpora needed by Metrik-4/5 (WordNet, omw, stopwords, ...).

    Idempotent. ``nltk.download`` is a no-op if the resource is already
    up-to-date.
    """
    try:
        import nltk
    except ImportError:
        return
    for resource in (
        "wordnet",
        "omw-1.4",
        "stopwords",
        "averaged_perceptron_tagger",
        "punkt",
    ):
        try:
            nltk.download(resource, quiet=True)
        except Exception:
            nltk.download(resource, quiet=False)
