"""Internal helpers for loading the canonical Metrik implementations.

This module is private to ``domain_model_metrics``. It centralises the
``sys.path`` setup and ``importlib.util``-based loading of the
``metric.py`` files under ``Metric-Implementation/Metrik-N/`` so that the
public ``get_metric()`` factory in ``domain_model_metrics.__init__`` stays
small.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Dict, Tuple

from ..workflow import MetricProtocol


# --------------------------------------------------------------------------
# Locate the repository root and the per-metric implementation directories.
#
# Layout: src/domain_model_metrics/metrics/_factory.py -> repo root is
# parents[3] (src -> domain_model_metrics -> metrics -> repo).
# --------------------------------------------------------------------------
_MODULE_PATH = Path(__file__).resolve()
_REPO_ROOT = _MODULE_PATH.parents[3]


def _impl_dir(metric_id: int) -> Tuple[Path, Path]:
    """Return ``(metric_root, impl_dir)`` for the given metric id.

    The implementation directory differs in name between Metrik-1..3
    (``Implementation-3``, hyphen) and Metrik-4/5 (``Implementation_3``,
    underscore).
    """
    metric_root = _REPO_ROOT / "Metric-Implementation" / f"Metrik-{metric_id}"
    if metric_id in (1, 2, 3):
        impl_dir = metric_root / "Implementation-3"
    elif metric_id in (4, 5):
        impl_dir = metric_root / "Implementation_3"
    else:
        raise ValueError(f"Unknown metric id: {metric_id}")
    if not impl_dir.is_dir():
        raise FileNotFoundError(
            f"Implementation directory not found: {impl_dir}. "
            "Did you install from a source checkout (vs. a wheel)?"
        )
    return metric_root, impl_dir


def _setup_sys_path(metric_root: Path, impl_dir: Path) -> None:
    """Configure sys.path + sys.modules so the metric's modules resolve unambiguously.

    Two problems to solve:

    1. **sys.path pollution.** Each of Metrik-1..5 ships its own
       ``Parser/``, ``Testset/``, and ``Implementation-3/`` (or
       ``Implementation_3/``) at the metric root. With multiple metric
       roots on ``sys.path``, Python picks the first match — so a bare
       ``from normalize import normalize`` (Metrik-3) may resolve to
       Metrik-1's ``normalize.py`` instead of Metrik-3's.

    2. **sys.modules caching.** Once any metric has been loaded in this
       Python process, ``sys.modules`` caches every module it imported:
       ``Parser``, ``Testset`` (a PEP 420 namespace package whose
       ``__path__`` lists every metric's ``Testset/``),
       ``Implementation_3``, and the implementation helpers
       (``normalize``, ``mapClasses``, ``createGraph``, …). To load a
       different metric, we must drop the cached namespace packages,
       their children, and the implementation helpers.

    Strategy:
    1. Drop the cached ``Parser`` / ``Testset`` / ``Implementation_3``
       namespace packages and ALL their submodules.
    2. Drop every cached module whose source file lives under
       ``Metric-Implementation/`` (covers ``normalize``, ``mapClasses``,
       ``createGraph``, ``transformUCDtoUCG``, …).
    3. Strip every ``Metric-Implementation/`` path from ``sys.path``
       except for the target metric's paths.
    4. Prepend the target metric's paths.
    """
    # Step 1+2: evict cached modules that would clash with the new metric.
    impl_root_str = str(_REPO_ROOT / "Metric-Implementation")
    cached_to_drop = set()
    for name in list(sys.modules):
        mod = sys.modules.get(name)
        # Drop namespace packages by name pattern.
        if name == "Testset" or name.startswith("Testset."):
            cached_to_drop.add(name); continue
        if name == "Parser" or name.startswith("Parser."):
            cached_to_drop.add(name); continue
        if name == "Implementation_3" or name.startswith("Implementation_3."):
            cached_to_drop.add(name); continue
        # Drop any other module whose source path lives under
        # Metric-Implementation/ — covers helper modules like normalize,
        # mapClasses, createGraph, etc.
        if mod is not None:
            mod_file = getattr(mod, "__file__", None)
            if mod_file and impl_root_str in mod_file:
                cached_to_drop.add(name)
    for stale in cached_to_drop:
        sys.modules.pop(stale, None)

    # Step 3: strip every Metric-Implementation/ path from sys.path that
    # does NOT belong to the target metric.
    metric_root_str = str(metric_root)
    impl_dir_str = str(impl_dir)
    sys.path[:] = [
        p for p in sys.path
        if metric_root_str in p
        or impl_dir_str in p
        or impl_root_str not in p
    ]

    # Step 4: prepend the target metric's paths in the right order.
    paths_to_add = (
        impl_dir,
        metric_root,
        _REPO_ROOT / "Quantitative-Analysis" / "Workflow",
    )
    for p in reversed(paths_to_add):
        sp = str(p)
        if sp in sys.path:
            sys.path.remove(sp)
        sys.path.insert(0, sp)

    # Ensure Workflow package parent is on sys.path so `from Workflow import …` works.
    workflow_parent = str((_REPO_ROOT / "Quantitative-Analysis" / "Workflow").parent)
    if workflow_parent not in sys.path:
        sys.path.insert(0, workflow_parent)


def _load_metric_module(metric_id: int):
    """Load ``metric.py`` from the canonical impl dir as a top-level module."""
    _, impl_dir = _impl_dir(metric_id)
    metric_py = impl_dir / "metric.py"
    if not metric_py.is_file():
        raise FileNotFoundError(f"metric.py not found in {impl_dir}")
    spec = importlib.util.spec_from_file_location(
        f"_metrik_{metric_id}_module", metric_py,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {metric_py}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------
# Adapter for Metrik-1..3: their metric.py exposes a top-level ``metric()``
# function rather than a MetricProtocol-conforming class. We wrap it.
# --------------------------------------------------------------------------
class _FunctionAdapter:
    """Wrap a top-level ``metric(ref, gen)`` function as ``MetricProtocol``."""

    def __init__(self, metric_id: int, metric_fn, parser_cls, name: str):
        self._metric = metric_fn
        self._parser_cls = parser_cls
        self._name = name
        self._metric_id = metric_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return "1.0.0"

    def compute(self, reference_plantuml: str, generated_plantuml: str) -> Dict[str, float]:
        parser = self._parser_cls(strict=True)
        ref = parser.parse(reference_plantuml)
        gen = parser.parse(generated_plantuml)
        result = self._metric(ref, gen)
        # Ensure dict-shape MetricResult (TypedDict compatible).
        return {
            "class_score": float(result["class_score"]),
            "attribute_score": float(result["attribute_score"]),
            "association_score": float(result["association_score"]),
        }


# --------------------------------------------------------------------------
# Public factory.
# --------------------------------------------------------------------------
def build(metric_id: int) -> MetricProtocol:
    """Construct and return a ``MetricProtocol`` for the given metric id."""
    metric_root, impl_dir = _impl_dir(metric_id)
    _setup_sys_path(metric_root, impl_dir)

    if metric_id in (1, 2, 3):
        module = _load_metric_module(metric_id)
        # Each of Metrik-1..3 bundles its own PlantUMLParser under Metrik-N/Parser.
        from Parser import PlantUMLParser  # noqa: E402
        return _FunctionAdapter(
            metric_id=metric_id,
            metric_fn=module.metric,
            parser_cls=PlantUMLParser,
            name=f"metrik-{metric_id}",
        )

    if metric_id in (4, 5):
        # Metrik-4/5 ship a ``get_metric()`` factory that already returns a
        # MetricProtocol-conforming adapter; we just call it.
        module = _load_metric_module(metric_id)
        # ``get_metric`` is the canonical factory exported from each
        # Implementation_3/metric.py.
        get_metric = getattr(module, "get_metric", None)
        if get_metric is None:
            raise ImportError(
                f"Metrik-{metric_id} does not export a get_metric() factory. "
                "This version of the implementation is not supported."
            )
        return get_metric()

    raise ValueError(f"Unknown metric id: {metric_id}")