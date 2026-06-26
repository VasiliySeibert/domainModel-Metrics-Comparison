"""Cross-metric comparison CLI.

This is the pip-install-friendly version of the source ``compare_metrics.py``
script. It loads the 5 pre-computed ``results_metrikN.json`` files (bundled
under ``Quantitative-Analysis/Results/``) and prints a per-metric MAD table,
RQ2 statistics, and per-element best-metric decisions.

Usage::

    python -m domain_model_metrics.compare            # print everything to stdout
    python -m domain_model_metrics.compare --self-test  # write JSON + PNG to current dir
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, List

# Re-use the source repo's compare_metrics.py by import. We add the repo
# root to sys.path so the file resolves, then delegate to its ``main()``.
# Layout: src/domain_model_metrics/compare.py -> parents[2] is the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_PARENT = str(_REPO_ROOT)
if _SRC_PARENT not in sys.path:
    sys.path.insert(0, _SRC_PARENT)

import compare_metrics as _cm  # noqa: E402


def _resolve_results_dir() -> Path:
    """Locate the directory containing the 5 results_metrikN.json files."""
    return _REPO_ROOT / "Quantitative-Analysis" / "Results"


def _print_table(results: Dict[str, Dict[str, Any]]) -> None:
    header = (
        f"{'Metric':<10} | {'Class Score':>11} | {'Attr Score':>11} | {'Assoc Score':>11} |"
        f" {'Human Class':>11} | {'Human Attr':>11} | {'Human Assoc':>11} |"
        f" {'Class MAD':>11} | {'Attr MAD':>11} | {'Assoc MAD':>11} |"
        f" {'Overall MAD':>11}"
    )
    print(header)
    print("-" * len(header))
    for name, r in results.items():
        def fmt(v, w=11, p=4):
            return f"{v:>{w}.{p}f}" if isinstance(v, (int, float)) else f"{'N/A':>{w}}"

        line = (
            f"{name:<10} | {fmt(r['avg_class_score'])} | {fmt(r['avg_attribute_score'])} |"
            f" {fmt(r['avg_association_score'])} | {fmt(r['avg_human_class_f1'])} |"
            f" {fmt(r['avg_human_attr_f1'])} | {fmt(r['avg_human_assoc_f1'])} |"
            f" {fmt(r['mad_class_delta_f1'])} | {fmt(r['mad_attribute_delta_f1'])} |"
            f" {fmt(r['mad_association_delta_f1'])} | {fmt(r['mad_overall_delta'])}"
        )
        print(line)
    print()
    print("Note: MAD = mean absolute deviation of (metric_score - human_f1) deltas")


def main(argv: List[str] | None = None) -> int:
    """Entry point: load the 5 bundled results JSONs, print summary, optionally write files."""
    argv = list(sys.argv[1:] if argv is None else argv)
    self_test = "--self-test" in argv
    out_dir = Path.cwd()

    project_root = _REPO_ROOT
    raw_data: Dict[str, Dict[str, Any]] = {}
    results: Dict[str, Dict[str, Any]] = {}
    for name, rel_path in _cm.METRIC_FILES.items():
        path = project_root / rel_path
        data = _cm.load_metric_data(path)
        avgs = _cm.extract_averages(data)
        mads = _cm.compute_mads(data)
        rq2 = _cm.extract_rq2_stats(data)
        raw_data[name] = data
        results[name] = {
            "timestamp": data.get("metadata", {}).get("generated_timestamp", "N/A"),
            "n_comparisons": len(data.get("comparisons", {})),
            "avg_class_score": avgs["avg_class_score"],
            "avg_attribute_score": avgs["avg_attribute_score"],
            "avg_association_score": avgs["avg_association_score"],
            "avg_human_class_f1": avgs["avg_human_class_f1"],
            "avg_human_attr_f1": avgs["avg_human_attr_f1"],
            "avg_human_assoc_f1": avgs["avg_human_assoc_f1"],
            "mad_class_delta_f1": mads["mad_class_delta_f1"],
            "mad_attribute_delta_f1": mads["mad_attribute_delta_f1"],
            "mad_association_delta_f1": mads["mad_association_delta_f1"],
            "mad_overall_delta": mads["mad_overall_delta"],
            "residual_std_class": rq2["residual_std_class"],
            "residual_std_attribute": rq2["residual_std_attribute"],
            "residual_std_association": rq2["residual_std_association"],
            "residual_std_overall": rq2["residual_std_overall"],
            "bias_class": rq2["bias_class"],
            "bias_attribute": rq2["bias_attribute"],
            "bias_association": rq2["bias_association"],
            "abs_bias_class": rq2["abs_bias_class"],
            "abs_bias_attribute": rq2["abs_bias_attribute"],
            "abs_bias_association": rq2["abs_bias_association"],
            "pearson_r_class": rq2["pearson_r_class"],
            "pearson_r_attribute": rq2["pearson_r_attribute"],
            "pearson_r_association": rq2["pearson_r_association"],
        }

    _print_table(results)

    # RQ2 row
    print()
    print("RQ2 — consistency of distance from human F1 (lower ResStd = more consistent)")
    header_rq2 = (
        f"{'Metric':<10} | {'Class r_std':>10} | {'Class |bias|':>11} | {'Class r':>7} |"
        f" {'Attr r_std':>10} | {'Attr |bias|':>11} | {'Attr r':>7} |"
        f" {'Assoc r_std':>11} | {'Assoc |bias|':>12} | {'Assoc r':>7} |"
        f" {'Ov r_std':>9}"
    )
    print(header_rq2)
    print("-" * len(header_rq2))
    for name, r in results.items():
        def fmt(v, w=10, p=4):
            return f"{v:>{w}.{p}f}" if isinstance(v, (int, float)) else f"{'N/A':>{w}}"
        line = (
            f"{name:<10} | {fmt(r['residual_std_class'])} | {fmt(r['abs_bias_class'], 11)} |"
            f" {fmt(r['pearson_r_class'], 7, 3)} |"
            f" {fmt(r['residual_std_attribute'])} | {fmt(r['abs_bias_attribute'], 11)} |"
            f" {fmt(r['pearson_r_attribute'], 7, 3)} |"
            f" {fmt(r['residual_std_association'], 11)} | {fmt(r['abs_bias_association'], 12)} |"
            f" {fmt(r['pearson_r_association'], 7, 3)} |"
            f" {fmt(r['residual_std_overall'], 9)}"
        )
        print(line)

    # Decision table
    print()
    print("Best metric per (element, RQ preference):")
    decision_header = f"{'Element':<12} | {'RQ1 (lowest MAD)':<24} | {'RQ2 (lowest ResStd)':<24} | {'RQ2 (highest r)':<24}"
    print(decision_header)
    print("-" * len(decision_header))
    for elem in ("class", "attribute", "association"):
        mad_key = f"mad_{elem}_delta_f1"
        rstd_key = f"residual_std_{elem}"
        r_key = f"pearson_r_{elem}"
        rows = [(n, r[mad_key], r[rstd_key], r[r_key]) for n, r in results.items()]
        rq1_winner = min(rows, key=lambda x: x[1])
        rq2_std_winner = min(rows, key=lambda x: x[2])
        rq2_r_winner = max(rows, key=lambda x: x[3])
        rq1_str = f"{rq1_winner[0]} (MAD={rq1_winner[1]:.4f})"
        rq2s_str = f"{rq2_std_winner[0]} (RStd={rq2_std_winner[2]:.4f})"
        rq2r_str = f"{rq2_r_winner[0]} (r={rq2_r_winner[3]:+.3f})"
        print(f"{elem:<12} | {rq1_str:<24} | {rq2s_str:<24} | {rq2r_str:<24}")

    if self_test:
        png_path = out_dir / "metrics_comparison_histogram.png"
        _cm.render_histogram_png(results, raw_data, png_path)
        scatter_path = out_dir / "metrics_comparison_scatter.png"
        _cm.render_scatter_png(results, raw_data, scatter_path)
        json_path = out_dir / "metrics_comparison.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print()
        print(f"Wrote {png_path}")
        print(f"Wrote {scatter_path}")
        print(f"Wrote {json_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())