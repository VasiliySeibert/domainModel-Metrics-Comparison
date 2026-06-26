#!/usr/bin/env python3
"""
Compare all Metrik versions side-by-side.

Loads the results JSON from each metric and prints a formatted comparison table,
plus saves a summary JSON to the project root. Reports both:

- **RQ1 (central tendency):** MAD = mean |metric_score − human_f1| per element.
- **RQ2 (consistency of distance):** residual std (spread of the signed
  delta around its mean), |bias| (systematic offset, calibratable by
  subtraction), and Pearson r between metric score and human F1
  (does the metric preserve the *ordering* of human-rated pairs?).

RQ1 and RQ2 give different rankings on every element, which is the
empirical contribution of the publication plan (see `publication.md`).
"""

import json
from math import sqrt
from pathlib import Path
from statistics import mean, median
from typing import Dict, Any, List, Tuple

# Map metric names to their result files
METRIC_FILES = {
    "Metrik-1": Path("Quantitative-Analysis/Results/results_metrik1.json"),
    "Metrik-2": Path("Quantitative-Analysis/Results/results_metrik2.json"),
    "Metrik-3": Path("Quantitative-Analysis/Results/results_metrik3.json"),
    "Metrik-4": Path("Quantitative-Analysis/Results/results_metrik4.json"),
    "Metrik-5": Path("Quantitative-Analysis/Results/results_metrik5.json"),
}

# Fixed MAD histogram buckets covering [0, 1] exhaustively. All but the last
# bucket are half-open [lo, hi); the last bucket is closed on both ends.
MAD_BUCKETS: List[tuple] = [
    ("<0.10",   0.00, 0.10),
    ("0.10-0.15", 0.10, 0.15),
    ("0.15-0.20", 0.15, 0.20),
    ("0.20-0.25", 0.20, 0.25),
    ("0.25-0.30", 0.25, 0.30),
    (">=0.30",   0.30, 1.01),
]
# Cumulative cutoffs: percent of pairs with |delta| strictly below this value.
CUM_CUTOFFS = (0.15, 0.20, 0.30)


def load_metric_data(path: Path) -> Dict[str, Any]:
    """Load results JSON, falling back to other locations if not found."""
    if not path.exists():
        raise FileNotFoundError(f"Result file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_mads(data: Dict[str, Any]) -> Dict[str, float]:
    """Compute Mean Absolute Delta (MAD) from raw per-comparison deltas."""
    comparisons = data.get("comparisons", {})

    class_deltas: List[float] = []
    attr_deltas: List[float] = []
    assoc_deltas: List[float] = []

    for comp in comparisons.values():
        delta = comp.get("delta", {})
        aggregated = comp.get("aggregated", {})

        class_deltas.append(abs(delta.get("class_vs_f1", 0)))
        attr_deltas.append(abs(delta.get("attribute_vs_f1", 0)))
        assoc_deltas.append(abs(delta.get("association_vs_f1", 0)))

    mad_class = mean(class_deltas) if class_deltas else 0
    mad_attr = mean(attr_deltas) if attr_deltas else 0
    mad_assoc = mean(assoc_deltas) if assoc_deltas else 0

    return {
        "mad_class_delta_f1": mad_class,
        "mad_attribute_delta_f1": mad_attr,
        "mad_association_delta_f1": mad_assoc,
        "mad_overall_delta": (mad_class + mad_attr + mad_assoc) / 3,
    }


def extract_averages(data: Dict[str, Any]) -> Dict[str, float]:
    """Extract average metric and human scores across all comparisons."""
    comparisons = data.get("comparisons", {})
    class_scores = []
    attr_scores = []
    assoc_scores = []
    human_class_f1 = []
    human_attr_f1 = []
    human_assoc_f1 = []
    metric_avgs = []
    human_avgs = []
    deltas = []

    for comp in comparisons.values():
        mr = comp.get("metric_results", {})
        class_scores.append(mr.get("class_score", 0))
        attr_scores.append(mr.get("attribute_score", 0))
        assoc_scores.append(mr.get("association_score", 0))

        hm = comp.get("human_metrics", {})
        human_class_f1.append(hm.get("Class", {}).get("f1", 0))
        human_attr_f1.append(hm.get("Attribute", {}).get("f1", 0))
        human_assoc_f1.append(hm.get("Association", {}).get("f1", 0))

        agg = comp.get("aggregated", {})
        metric_avgs.append(agg.get("metric_average", 0))
        human_avgs.append(agg.get("human_f1_average", 0))
        deltas.append(agg.get("overall_delta", 0))

    return {
        "avg_class_score": mean(class_scores) if class_scores else 0,
        "avg_attribute_score": mean(attr_scores) if attr_scores else 0,
        "avg_association_score": mean(assoc_scores) if assoc_scores else 0,
        "avg_human_class_f1": mean(human_class_f1) if human_class_f1 else 0,
        "avg_human_attr_f1": mean(human_attr_f1) if human_attr_f1 else 0,
        "avg_human_assoc_f1": mean(human_assoc_f1) if human_assoc_f1 else 0,
        "avg_metric_average": mean(metric_avgs) if metric_avgs else 0,
        "avg_human_f1_average": mean(human_avgs) if human_avgs else 0,
        "avg_overall_delta": mean(deltas) if deltas else 0,
    }


# Element key mapping: (delta_key, score_key, human_key) for each element.
_ELEMENT_KEYS: Dict[str, Tuple[str, str, str]] = {
    "class":       ("class_vs_f1",       "class_score",       "Class"),
    "attribute":   ("attribute_vs_f1",   "attribute_score",   "Attribute"),
    "association": ("association_vs_f1", "association_score", "Association"),
}


def extract_rq2_stats(data: Dict[str, Any]) -> Dict[str, float]:
    """Compute RQ2 statistics from per-comparison residuals.

    For each of Class, Attribute, Association, returns:
        residual_std_<e>     std of signed (metric - human) across pairs.
        |bias|_<e>            mean of signed (metric - human).
        bias_<e>              same, signed.
        median_abs_<e>        robust alternative to MAD.
        pearson_r_<e>         corr(metric_score, human_f1).
        pearson_r2_<e>        r² (coefficient of determination).
        slope_<e>             OLS slope of human on metric.
        intercept_<e>         OLS intercept of human on metric.

    RQ1 (MAD) and RQ2 (residual std) are complementary: a metric with low
    MAD but high residual std is *unpredictable* in its errors; a metric
    with high MAD but small residual std is *calibratable* by a constant
    shift.
    """
    out: Dict[str, float] = {}
    for elem, (delta_key, score_key, human_key) in _ELEMENT_KEYS.items():
        residuals: List[float] = []
        metric_scores: List[float] = []
        human_scores: List[float] = []
        for comp in data.get("comparisons", {}).values():
            d = comp.get("delta", {})
            if delta_key in d:
                residuals.append(float(d[delta_key]))
                metric_scores.append(float(comp.get("metric_results", {}).get(score_key, 0)))
                human_scores.append(float(comp.get("human_metrics", {}).get(human_key, {}).get("f1", 0)))
        if not residuals:
            out[f"residual_std_{elem}"] = 0.0
            out[f"bias_{elem}"] = 0.0
            out[f"abs_bias_{elem}"] = 0.0
            out[f"median_abs_{elem}"] = 0.0
            out[f"pearson_r_{elem}"] = 0.0
            out[f"pearson_r2_{elem}"] = 0.0
            out[f"slope_{elem}"] = 0.0
            out[f"intercept_{elem}"] = 0.0
            continue
        n = len(residuals)
        std = (sum((r - mean(residuals)) ** 2 for r in residuals) / (n - 1)) ** 0.5
        bias = mean(residuals)
        med_abs = median([abs(r) for r in residuals])
        # Pearson r and OLS slope/intercept
        mx, hx = mean(metric_scores), mean(human_scores)
        sxx = sum((m - mx) ** 2 for m in metric_scores)
        syy = sum((h - hx) ** 2 for h in human_scores)
        sxy = sum((m - mx) * (h - hx) for m, h in zip(metric_scores, human_scores))
        if sxx > 0 and syy > 0:
            r = sxy / (sxx * syy) ** 0.5
            slope = sxy / sxx
        else:
            r = 0.0
            slope = 0.0
        intercept = hx - slope * mx
        out[f"residual_std_{elem}"] = std
        out[f"bias_{elem}"] = bias
        out[f"abs_bias_{elem}"] = abs(bias)
        out[f"median_abs_{elem}"] = med_abs
        out[f"pearson_r_{elem}"] = r
        out[f"pearson_r2_{elem}"] = r * r
        out[f"slope_{elem}"] = slope
        out[f"intercept_{elem}"] = intercept
    # Also a single RQ2 number for the *aggregate* residual (overall_delta).
    overall_residuals: List[float] = []
    for comp in data.get("comparisons", {}).values():
        agg = comp.get("aggregated", {})
        if "overall_delta" in agg:
            overall_residuals.append(float(agg["overall_delta"]))
    if overall_residuals:
        n = len(overall_residuals)
        out["residual_std_overall"] = (
            sum((r - mean(overall_residuals)) ** 2 for r in overall_residuals) / (n - 1)
        ) ** 0.5
        out["bias_overall"] = mean(overall_residuals)
        out["abs_bias_overall"] = abs(out["bias_overall"])
    else:
        out["residual_std_overall"] = 0.0
        out["bias_overall"] = 0.0
        out["abs_bias_overall"] = 0.0
    return out


def bucketize(abs_deltas: List[float], buckets=MAD_BUCKETS) -> List[int]:
    """Count how many |delta| values fall into each bucket.

    Buckets are (label, lo, hi). The last bucket is closed on both ends
    (``lo <= x <= hi``); all others are half-open ``[lo, hi)``.
    """
    counts = [0] * len(buckets)
    n = len(buckets)
    for x in abs_deltas:
        placed = False
        for i, (_, lo, hi) in enumerate(buckets):
            if i == n - 1:
                if lo <= x <= hi:
                    counts[i] += 1
                    placed = True
                    break
            else:
                if lo <= x < hi:
                    counts[i] += 1
                    placed = True
                    break
        if not placed:
            # |delta| > 1.0 should be impossible (delta is in [-1, 1]),
            # but lump it into the last bucket defensively.
            counts[-1] += 1
    return counts


def cum_below(abs_deltas: List[float], cutoff: float) -> float:
    """Percentage of |delta| values strictly below ``cutoff``."""
    if not abs_deltas:
        return 0.0
    n_below = sum(1 for x in abs_deltas if x < cutoff)
    return 100.0 * n_below / len(abs_deltas)


def collect_abs_deltas(
    data: Dict[str, Any], element: str
) -> List[float]:
    """Return the |delta| values for one element type from a results JSON.

    ``element`` is one of: 'class', 'attribute', 'association'. The function
    reads the corresponding per-comparison delta field.
    """
    key_map = {
        "class": "class_vs_f1",
        "attribute": "attribute_vs_f1",
        "association": "association_vs_f1",
    }
    delta_key = key_map[element]
    out: List[float] = []
    for comp in data.get("comparisons", {}).values():
        d = comp.get("delta", {})
        if delta_key in d:
            out.append(abs(d[delta_key]))
    return out


def render_histogram_png(
    metric_data: Dict[str, Dict[str, Any]],
    data_by_metric: Dict[str, Dict[str, Any]],
    out_path: Path,
) -> None:
    """Render a small-multiples bar chart of per-metric MAD histograms.

    One figure with 3 columns (Class / Attribute / Association) and one row
    per metric. Each subplot is a stacked bar chart of the 6 buckets; the
    "good" buckets (<0.20) are colored green, the "warning" buckets
    (0.20-0.30) yellow, and the "bad" bucket (>=0.30) red. A horizontal
    line at 0.20 marks the "close enough" threshold. Median |delta| and
    Cum<0.20 are annotated in the subplot title.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    bucket_labels = [b[0] for b in MAD_BUCKETS]
    bucket_widths = [b[2] - b[1] for b in MAD_BUCKETS]
    # Use the mid-point as the bar center; widths are full bucket extents.
    bucket_centers = [b[1] + (b[2] - b[1]) / 2.0 for b in MAD_BUCKETS]

    # Color buckets: <0.20 green family, 0.20-0.30 yellow, >=0.30 red.
    bucket_colors = [
        "#2ca02c",  # <0.10
        "#5fbf5f",  # 0.10-0.15
        "#a8d8a8",  # 0.15-0.20
        "#ffdf80",  # 0.20-0.25
        "#ffb84d",  # 0.25-0.30
        "#d62728",  # >=0.30
    ]

    element_keys = [
        ("class", "Class"),
        ("attribute", "Attribute"),
        ("association", "Association"),
    ]

    metric_names = list(metric_data.keys())
    n_metrics = len(metric_names)

    fig, axes = plt.subplots(
        n_metrics, 3,
        figsize=(14, 1.6 * n_metrics),
        sharex=True,
        sharey=False,
        squeeze=False,
    )

    for r, name in enumerate(metric_names):
        data = data_by_metric[name]
        for c, (el_key, el_label) in enumerate(element_keys):
            ax = axes[r][c]
            abs_d = collect_abs_deltas(data, el_key)
            counts = bucketize(abs_d)
            med = median(abs_d) if abs_d else 0.0
            cum20 = cum_below(abs_d, 0.20)

            ax.bar(
                bucket_centers,
                counts,
                width=bucket_widths,
                color=bucket_colors,
                edgecolor="white",
                linewidth=0.6,
                align="center",
            )
            # Threshold reference line at the 0.20 boundary.
            ax.axvline(0.20, color="#444", linestyle="--", linewidth=0.8, alpha=0.6)

            # Annotate each bar with its count.
            for x, h in zip(bucket_centers, counts):
                if h > 0:
                    ax.text(
                        x, h, str(h),
                        ha="center", va="bottom",
                        fontsize=7, color="#222",
                    )

            max_count = max(max(counts), 1)
            ax.set_ylim(0, max_count * 1.18)
            ax.set_xlim(0, 0.32)

            if r == 0:
                ax.set_title(el_label, fontsize=11, fontweight="bold")
            if c == 0:
                ax.set_ylabel(name, fontsize=10, fontweight="bold")
            ax.set_xticks(bucket_centers)
            ax.set_xticklabels(bucket_labels, rotation=45, ha="right", fontsize=7)
            y_step = max(1, max_count // 5)
            ax.set_yticks(range(0, max_count + 1, y_step))
            ax.tick_params(axis="y", labelsize=7)
            ax.grid(axis="y", alpha=0.25, linestyle=":")

            ax.text(
                0.98, 0.95,
                f"med={med:.3f}\n<0.20: {cum20:.0f}%",
                transform=ax.transAxes,
                ha="right", va="top",
                fontsize=7,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                          edgecolor="#888", alpha=0.85),
            )

    fig.suptitle(
        "MAD Histograms per Metric and Element Type  (N = 39 pairs each)",
        fontsize=13, fontweight="bold", y=0.995,
    )
    fig.supxlabel(
        "|delta| bucket  (metric_score - human_f1)  —  green = close, red = far",
        fontsize=9,
    )
    fig.supylabel("count of pairs", fontsize=9)

    # Reserve generous bottom/top space for x-tick labels and the suptitle.
    fig.subplots_adjust(left=0.07, right=0.98, top=0.93, bottom=0.18, wspace=0.25, hspace=0.55)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def print_histogram(
    metric_data: Dict[str, Dict[str, Any]],
    data_by_metric: Dict[str, Dict[str, Any]],
) -> None:
    """Print a per-metric, per-element MAD histogram to the terminal.

    ``metric_data`` is the existing results dict (name -> summary fields).
    ``data_by_metric`` is a parallel dict (name -> raw loaded JSON) needed
    to walk the per-comparison deltas.
    """
    element_labels = [("class", "Class"), ("attribute", "Attribute"),
                      ("association", "Assoc.")]

    bucket_labels = [b[0] for b in MAD_BUCKETS]
    cum_headers = [f"Cum<{c:.2f}" for c in CUM_CUTOFFS]

    header_cells = ["Element"] + [f"{b:>9}" for b in bucket_labels] + \
        [" Median", "    N"] + [f"{h:>7}" for h in cum_headers]
    header = " | ".join(f"{c:<9}" if i == 0 else f"{c:>9}"
                        for i, c in enumerate(header_cells))

    for name, _ in metric_data.items():
        data = data_by_metric[name]
        n_total = len(data.get("comparisons", {}))

        print()
        print("=" * len(header))
        print(f"=== {name}  (N = {n_total} pairs) ===")
        print("=" * len(header))
        print(header)
        print("-" * len(header))

        for el_key, el_label in element_labels:
            abs_d = collect_abs_deltas(data, el_key)
            counts = bucketize(abs_d)
            med = median(abs_d) if abs_d else 0.0
            cum_cells = [f"{cum_below(abs_d, c):>6.1f}%" for c in CUM_CUTOFFS]
            cells = [f"{el_label:<9}"] + \
                [f"{c:>9}" for c in counts] + \
                [f"{med:>9.3f}", f"{len(abs_d):>9}"] + cum_cells
            print(" | ".join(cells))

    print()
    print("Buckets: half-open [lo, hi) except the last (closed).")
    print("Median = median |delta| across N pairs for that element.")
    print(
        "Cum<X = percentage of pairs with |delta| strictly below X "
        "(X in "
        + ", ".join(f"{c:.2f}" for c in CUM_CUTOFFS)
        + ")."
    )


def main():
    project_root = Path(__file__).resolve().parent
    results: Dict[str, Dict[str, Any]] = {}
    raw_data: Dict[str, Dict[str, Any]] = {}

    for name, rel_path in METRIC_FILES.items():
        path = project_root / rel_path
        data = load_metric_data(path)
        avgs = extract_averages(data)
        mads = compute_mads(data)
        rq2 = extract_rq2_stats(data)
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
            # RQ2 (consistency of distance from human F1):
            "residual_std_class":       rq2["residual_std_class"],
            "residual_std_attribute":   rq2["residual_std_attribute"],
            "residual_std_association": rq2["residual_std_association"],
            "residual_std_overall":     rq2["residual_std_overall"],
            "bias_class":       rq2["bias_class"],
            "bias_attribute":   rq2["bias_attribute"],
            "bias_association": rq2["bias_association"],
            "bias_overall":     rq2["bias_overall"],
            "abs_bias_class":       rq2["abs_bias_class"],
            "abs_bias_attribute":   rq2["abs_bias_attribute"],
            "abs_bias_association": rq2["abs_bias_association"],
            "abs_bias_overall":     rq2["abs_bias_overall"],
            "median_abs_class":       rq2["median_abs_class"],
            "median_abs_attribute":   rq2["median_abs_attribute"],
            "median_abs_association": rq2["median_abs_association"],
            "pearson_r_class":       rq2["pearson_r_class"],
            "pearson_r_attribute":   rq2["pearson_r_attribute"],
            "pearson_r_association": rq2["pearson_r_association"],
            "slope_class":       rq2["slope_class"],
            "slope_attribute":   rq2["slope_attribute"],
            "slope_association": rq2["slope_association"],
            "intercept_class":       rq2["intercept_class"],
            "intercept_attribute":   rq2["intercept_attribute"],
            "intercept_association": rq2["intercept_association"],
        }

    # Terminal output
    header = (
        f"{'Metric':<10} | {'Class Score':>11} | {'Attr Score':>11} | {'Assoc Score':>11} |"
        f" {'Human Class':>11} | {'Human Attr':>11} | {'Human Assoc':>11} |"
        f" {'Class MAD':>11} | {'Attr MAD':>11} | {'Assoc MAD':>11} |"
        f" {'Overall MAD':>11}"
    )
    print(header)
    print("-" * len(header))

    for name, r in results.items():
        def fmt(v):
            return f"{v:>11.4f}" if isinstance(v, (int, float)) else f"{'N/A':>11}"

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

    # RQ2 wide table: residual std, |bias|, Pearson r — all from the same
    # 39 signed residuals that RQ1 uses, so no new metric runs are needed.
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
        def fmt_rq2(v, w=10, p=4):
            return f"{v:>{w}.{p}f}" if isinstance(v, (int, float)) else f"{'N/A':>{w}}"

        line = (
            f"{name:<10} | {fmt_rq2(r['residual_std_class'])} | {fmt_rq2(r['abs_bias_class'], 11)} | {fmt_rq2(r['pearson_r_class'], 7, 3)} |"
            f" {fmt_rq2(r['residual_std_attribute'])} | {fmt_rq2(r['abs_bias_attribute'], 11)} | {fmt_rq2(r['pearson_r_attribute'], 7, 3)} |"
            f" {fmt_rq2(r['residual_std_association'], 11)} | {fmt_rq2(r['abs_bias_association'], 12)} | {fmt_rq2(r['pearson_r_association'], 7, 3)} |"
            f" {fmt_rq2(r['residual_std_overall'], 9)}"
        )
        print(line)

    print()
    print("Note (RQ2): r_std = std of signed (metric - human) across 39 pairs;")
    print("             |bias| = mean absolute value of the same residuals (calibratable by subtraction);")
    print("             r = Pearson correlation between metric_score and human_f1 (preserves ordering?).")
    print("             A metric with high |bias| but low r_std is a CONSISTENTLY wrong metric (calibratable).")
    print("             A metric with low |bias| but also low |r| is essentially RANDOM on that element.")

    # Decision table: which metric is best under each (element, RQ) combination?
    print()
    print("Best metric per (element, RQ preference):")
    elements = ["class", "attribute", "association"]
    decision_header = f"{'Element':<12} | {'RQ1 (lowest MAD)':<24} | {'RQ2 (lowest ResStd)':<24} | {'RQ2 (highest r)':<24}"
    print(decision_header)
    print("-" * len(decision_header))
    for elem in elements:
        mad_key = f"mad_{elem}_delta_f1"
        rstd_key = f"residual_std_{elem}"
        r_key = f"pearson_r_{elem}"
        rows = [(name, r[mad_key], r[rstd_key], r[r_key]) for name, r in results.items()]
        rq1_winner = min(rows, key=lambda x: x[1])
        rq2_std_winner = min(rows, key=lambda x: x[2])
        rq2_r_winner = max(rows, key=lambda x: x[3])
        rq1_str = f"{rq1_winner[0]} (MAD={rq1_winner[1]:.4f})"
        rq2s_str = f"{rq2_std_winner[0]} (RStd={rq2_std_winner[2]:.4f})"
        rq2r_str = f"{rq2_r_winner[0]} (r={rq2_r_winner[3]:+.3f})"
        print(f"{elem:<12} | {rq1_str:<24} | {rq2s_str:<24} | {rq2r_str:<24}")

    # Per-metric, per-element MAD histograms
    print_histogram(results, raw_data)

    # Same data, rendered as a small-multiples PNG
    png_path = project_root / "Quantitative-Analysis" / "Results" / "metrics_comparison_histogram.png"
    render_histogram_png(results, raw_data, png_path)
    print(f"Histogram PNG saved to: {png_path}")

    # Per-pair scatter plot (Fig. 2 of the publication plan): RQ1 + RQ2
    # visualised together — each subplot shows the 39 points + a y=x
    # reference line + the fitted OLS line, with MAD / ResStd / r in the
    # title.
    scatter_path = project_root / "Quantitative-Analysis" / "Results" / "metrics_comparison_scatter.png"
    render_scatter_png(results, raw_data, scatter_path)
    print(f"Per-pair scatter PNG saved to: {scatter_path}")

    # Save JSON summary
    out_path = project_root / "Quantitative-Analysis" / "Results" / "metrics_comparison.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nComparison summary saved to: {out_path}")


def render_scatter_png(
    metric_data: Dict[str, Dict[str, Any]],
    data_by_metric: Dict[str, Dict[str, Any]],
    out_path: Path,
) -> None:
    """Render a per-pair scatter plot: metric_score vs human F1.

    One subplot per (metric, element) — 5 metrics × 3 elements = 15
    panels. Each panel shows:
      - 39 scatter points (one per (model, setting) pair).
      - The y = x reference line (dashed black).
      - The fitted OLS line `human = intercept + slope * metric`
        (solid red).
      - Title annotated with RQ1 (MAD), RQ2 (residual std, |bias|,
        Pearson r), and the OLS slope.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    metric_names = list(metric_data.keys())
    n_metrics = len(metric_names)
    elements = [("class", "Class"), ("attribute", "Attribute"), ("association", "Association")]

    metric_names = list(metric_data.keys())
    n_metrics = len(metric_names)
    elements = [("class", "Class"), ("attribute", "Attribute"), ("association", "Association")]

    fig, axes = plt.subplots(
        n_metrics, 3,
        figsize=(11, 2.4 * n_metrics),
        sharex=False, sharey=False,
        squeeze=False,
    )

    for row, name in enumerate(metric_names):
        data = data_by_metric[name]
        for col, (el_key, el_label) in enumerate(elements):
            ax = axes[row][col]
            score_key = f"{el_key}_score"
            delta_key = f"{el_key}_vs_f1"
            human_key = el_label
            xs, ys = [], []
            for comp in data.get("comparisons", {}).values():
                metric_score = comp.get("metric_results", {}).get(score_key)
                human_score = comp.get("human_metrics", {}).get(human_key, {}).get("f1")
                if metric_score is None or human_score is None:
                    continue
                xs.append(float(metric_score))
                ys.append(float(human_score))
            if not xs:
                ax.set_title(f"{name} / {el_label}  (no data)", fontsize=10)
                continue
            xs_arr = np.array(xs)
            ys_arr = np.array(ys)
            ax.scatter(xs_arr, ys_arr, s=22, alpha=0.7, edgecolor="black", linewidth=0.4)

            # y = x reference
            lo = 0.0
            hi = 1.0
            ax.plot([lo, hi], [lo, hi], "k--", alpha=0.4, linewidth=1.0, label="y = x")

            # OLS fit
            slope = metric_data[name].get(f"slope_{el_key}", 0.0)
            intercept = metric_data[name].get(f"intercept_{el_key}", 0.0)
            if not (slope == 0.0 and intercept == 0.0):
                xs_line = np.array([lo, hi])
                ys_line = intercept + slope * xs_line
                ax.plot(xs_line, np.clip(ys_line, lo, hi), "r-", alpha=0.6, linewidth=1.2,
                        label=f"OLS (slope={slope:.2f})")

            # Title with RQ1 + RQ2 summary
            mad = metric_data[name].get(f"mad_{delta_key}", 0.0)
            rstd = metric_data[name].get(f"residual_std_{el_key}", 0.0)
            bias = metric_data[name].get(f"bias_{el_key}", 0.0)
            pearson_r = metric_data[name].get(f"pearson_r_{el_key}", 0.0)
            ax.set_title(
                f"{name} / {el_label}\nMAD={mad:.3f}  ResStd={rstd:.3f}  |bias|={abs(bias):.3f}  r={pearson_r:+.2f}",
                fontsize=9,
            )
            ax.set_xlim(lo, hi)
            ax.set_ylim(lo, hi)
            ax.set_aspect("equal")
            ax.grid(":", alpha=0.3)
            if col == 0:
                ax.set_ylabel("Human F1", fontsize=9)
            ax.set_xlabel("Metric score", fontsize=9)
            if row == 0 and col == 0:
                ax.legend(loc="lower right", fontsize=7)

    fig.suptitle(
        "Per-pair scatter: metric score vs human F1 (RQ1 + RQ2 visualisation; N=39 pairs/panel)",
        fontsize=12, fontweight="bold", y=0.995,
    )
    fig.supxlabel("metric score", fontsize=9)
    fig.supylabel("human F1", fontsize=9)
    fig.subplots_adjust(left=0.06, right=0.98, top=0.96, bottom=0.06, wspace=0.30, hspace=0.55)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
