"""Build the quantitative_results_walkthrough.ipynb notebook.

Run from the repo root:

    python Notebooks/_build_walkthrough.py

The notebook is generated programmatically so we can keep the markdown
content in clean Python literals rather than hand-written JSON.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def md(*lines: str) -> Dict[str, Any]:
    """A markdown cell with the given source lines joined."""
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [ln + "\n" for ln in lines],
    }


def code(*lines: str) -> Dict[str, Any]:
    """A code cell with the given source lines joined."""
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [ln + "\n" for ln in lines],
    }


# --------------------------------------------------------------------------
# Cell content. Order matters.
# --------------------------------------------------------------------------

cells: List[Dict[str, Any]] = []

# §1 Title
cells.append(md(
    "# domain-model-metrics: quantitative-results walkthrough",
    "",
    "**A narrated walkthrough of the 5-metric × 39-pair benchmark.**",
    "",
    "This notebook loads the pre-computed per-metric results from",
    "`Quantitative-Analysis/Results/results_metrik{1..5}.json`, computes",
    "the headline MAD table, the RQ2 consistency statistics, and the",
    "per-element no-free-lunch finding, and reproduces the published",
    "figures.",
    "",
    "It is *read-only* with respect to the data — no metric re-runs",
    "are needed, and the whole notebook executes in a few seconds.",
    "",
    "**Dataset.** 8 reference UML domain models (LabTracker, CelO, TSS,",
    "SHAS, OTS, Block, TileO, HBMS) × 5 LLM prompting settings (`0shot`,",
    "`1shot_BTMS`, `1shot_H2S`, `2shots`, `CoT`) = **39 comparison",
    "pairs** (SHAS_0shot is missing). Each pair has a single-rater human",
    "F1 ground truth for Class, Attribute, Association.",
    "",
    "**Ground truth.** The human F1 was produced by the dissertation",
    "author using the c1/c2/c3/c4 reverse-engineered grading scheme.",
    "Single-rater ground truth is a known limitation of the source",
    "project; see `Publication/publication.md` for the full discussion.",
))

# §2 Setup
cells.append(md("## 1. Setup"))
cells.append(code(
    "import json",
    "from pathlib import Path",
    "",
    "import matplotlib",
    "matplotlib.use('Agg')  # headless-safe",
    "import matplotlib.pyplot as plt",
    "",
    "import domain_model_metrics as dmm",
    "from domain_model_metrics import get_metric, list_metrics",
    "from domain_model_metrics.workflow import MetricResult, MetricWorkflow",
    "",
    "REPO_ROOT = Path('.').resolve()",
    "RESULTS_DIR = REPO_ROOT / 'Quantitative-Analysis' / 'Results'",
    "DATASET_PATH = REPO_ROOT / 'data' / 'combined-data.json'",
    "",
    "print('domain_model_metrics', dmm.__version__)",
    "print('Supported metrics:', list_metrics())",
    "print('Dataset exists:', DATASET_PATH.exists())",
))

# §3 Run a single metric
cells.append(md(
    "## 2. Run a single metric",
    "",
    "Compute the similarity between two PlantUML strings using",
    "`get_metric(\"metrik-1\")`. The result is a 3-key dict whose keys",
    "(`class_score`, `attribute_score`, `association_score`) align with",
    "the human-evaluated categories.",
))
cells.append(code(
    "# Use the canonical LabTracker / 0shot pair from the bundled dataset.",
    "with open(DATASET_PATH) as f:",
    "    data = json.load(f)",
    "lab = data['models']['LabTracker']",
    "ref_puml = lab['reference_plantuml']",
    "gen_puml = lab['generated_plantuml']['0shot']",
    "human = lab['metrics']['0shot']",
    "",
    "m = get_metric('metrik-1')",
    "result = m.compute(ref_puml, gen_puml)",
    "print(f\"{m.name} v{m.version}\")",
    "for k, v in result.items():",
    "    print(f'  {k:18s} = {v:.4f}')",
    "print()",
    "print('Human F1 ground truth for the same pair:')",
    "for cat, vals in human.items():",
    "    print(f'  {cat:13s} F1 = {vals[\"f1\"]:.4f}')",
))

# §4 Run all 5 on the 39-pair benchmark (read pre-computed JSONs)
cells.append(md(
    "## 3. Load the pre-computed per-metric results",
    "",
    "Re-running all 5 metrics on the full 39-pair benchmark takes",
    "≈ 40 minutes (Metrik-4 and Metrik-5 alone take ≈ 17 minutes each",
    "because they use NLTK / WordNet graph traversals).",
    "",
    "For a quick walkthrough we load the pre-computed results JSONs from",
    "`Quantitative-Analysis/Results/`. These were produced once on the",
    "source `diss-metrik` project and are bundled verbatim in this",
    "release.",
))
cells.append(code(
    "per_metric = {}",
    "for n in (1, 2, 3, 4, 5):",
    "    p = RESULTS_DIR / f'results_metrik{n}.json'",
    "    with open(p) as f:",
    "        per_metric[f'metrik-{n}'] = json.load(f)",
    "",
    "for name, payload in per_metric.items():",
    "    md = payload.get('metadata', {})",
    "    print(f\"{name}  N={len(payload['comparisons']):2d}  ts={md.get('generated_timestamp', 'n/a')}\")",
))

# §5 Headline MAD table
cells.append(md(
    "## 4. Headline results: the MAD table",
    "",
    "**MAD** = mean absolute deviation between the metric's score and the",
    "human F1, averaged over the 39 (model, setting) pairs. Lower is",
    "better. The table below is reproduced from",
    "`Metric-Implementation/README.md` (the source `diss-metrik` project)",
    "and is bit-exact with the values produced by",
    "`compare_metrics.py::compute_mads`.",
    "",
    "| Metrik | Class MAD | Attr MAD | Assoc MAD | Overall MAD |",
    "|-------:|----------:|---------:|----------:|------------:|",
    "| 1      | 0.1471    | 0.2318   | 0.1309    | 0.1699      |",
    "| 2      | 0.1867    | 0.1501   | 0.1834    | 0.1734      |",
    "| 3      | 0.1720    | 0.2127   | 0.1258    | 0.1702      |",
    "| 4      | 0.0866    | 0.1365   | 0.2745    | 0.1658      |",
    "| **5**  | **0.0738**| 0.1460   | 0.2582    | **0.1593**  |",
    "",
    "A few observations:",
    "",
    "- The 5 metrics are **indistinguishable on overall MAD** (0.16–0.17",
    "  across the board).",
    "- They diverge sharply on the **per-element** decomposition.",
    "  Metrik-5 is best on Class, Metrik-4 is best on Attribute,",
    "  Metrik-3 is best on Association.",
    "- **Metrik-4 and Metrik-5 trade off** Class / Attribute accuracy",
    "  for Association accuracy — both implement the same Triandini S-1",
    "  pipeline with different projection choices.",
))
cells.append(code(
    "def compute_mad(payload, element):",
    "    \"\"\"MAD = mean |metric_score - human_f1| over all comparisons.\"\"\"",
    "    deltas = []",
    "    for comp in payload['comparisons'].values():",
    "        delta = comp['delta'].get(f'{element}_vs_f1', 0)",
    "        deltas.append(abs(delta))",
    "    return sum(deltas) / len(deltas) if deltas else 0.0",
    "",
    "rows = []",
    "for name, payload in per_metric.items():",
    "    rows.append({",
    "        'Metrik': name,",
    "        'Class MAD':  compute_mad(payload, 'class'),",
    "        'Attr MAD':   compute_mad(payload, 'attribute'),",
    "        'Assoc MAD':  compute_mad(payload, 'association'),",
    "    })",
    "for r in rows:",
    "    overall = (r['Class MAD'] + r['Attr MAD'] + r['Assoc MAD']) / 3",
    "    r['Overall MAD'] = overall",
    "",
    "header = f\"{'Metrik':<10} | {'Class MAD':>9} | {'Attr MAD':>9} | {'Assoc MAD':>10} | {'Overall MAD':>11}\"",
    "print(header)",
    "print('-' * len(header))",
    "for r in rows:",
    "    print(f\"{r['Metrik']:<10} | {r['Class MAD']:>9.4f} | {r['Attr MAD']:>9.4f} | {r['Assoc MAD']:>10.4f} | {r['Overall MAD']:>11.4f}\")",
))

# §6 The no-free-lunch finding
cells.append(md(
    "## 5. The no-free-lunch finding",
    "",
    "Beyond the *level* question (RQ1, the MAD), each metric is also",
    "characterised by a *consistency* question (RQ2, the spread of the",
    "per-pair distance from the human). The RQ2 statistic we use here is",
    "**residual std** (std of signed `metric − human` across the 39",
    "pairs); lower is more consistent.",
    "",
    "**RQ1 and RQ2 are answered by *different* metrics on every element.**",
    "",
    "| Element     | RQ1 best (lowest MAD) | RQ2 best (lowest ResStd) | RQ2 best (highest r) |",
    "|-------------|-----------------------|--------------------------|----------------------|",
    "| Class       | Metrik-5 (0.074)      | Metrik-4                 | Metrik-4 (r = 0.424) |",
    "| Attribute   | Metrik-4 (0.137)      | Metrik-3                 | Metrik-3 (r = 0.654) |",
    "| Association | Metrik-3 (0.126)      | Metrik-4                 | Metrik-4 (r = 0.417) |",
    "",
    "**6 out of 6 picks differ.** Below we recompute the RQ1 / RQ2",
    "decision table directly from the bundled JSONs.",
))
cells.append(code(
    "import statistics",
    "",
    "def rq2_stats(payload, element):",
    "    \"\"\"Return (mad, residual_std, |bias|, pearson_r) for one element.\"\"\"",
    "    residuals, m_scores, h_scores = [], [], []",
    "    for comp in payload['comparisons'].values():",
    "        d = comp['delta']",
    "        if f'{element}_vs_f1' not in d:",
    "            continue",
    "        residuals.append(d[f'{element}_vs_f1'])",
    "        m_scores.append(comp['metric_results'][f'{element}_score'])",
    "        h_scores.append(comp['human_metrics'][element.title()]['f1'])",
    "    n = len(residuals)",
    "    mad = sum(abs(r) for r in residuals) / n",
    "    bias = sum(residuals) / n",
    "    rstd = (sum((r - bias) ** 2 for r in residuals) / (n - 1)) ** 0.5",
    "    mx, hx = statistics.mean(m_scores), statistics.mean(h_scores)",
    "    sxx = sum((m - mx) ** 2 for m in m_scores)",
    "    syy = sum((h - hx) ** 2 for h in h_scores)",
    "    sxy = sum((m - mx) * (h - hx) for m, h in zip(m_scores, h_scores))",
    "    r = sxy / (sxx * syy) ** 0.5 if sxx > 0 and syy > 0 else 0.0",
    "    return mad, rstd, abs(bias), r",
    "",
    "elements = ['class', 'attribute', 'association']",
    "stats = {n: {e: rq2_stats(p, e) for e in elements} for n, p in per_metric.items()}",
    "",
    "print(f\"{'Element':<12} | {'RQ1 best (MAD)':<22} | {'RQ2 best (ResStd)':<22} | {'RQ2 best (r)':<22}\")",
    "print('-' * 80)",
    "for e in elements:",
    "    rows = [(n, s[e][0], s[e][1], s[e][3]) for n, s in stats.items()]",
    "    rq1  = min(rows, key=lambda x: x[1])",
    "    rq2s = min(rows, key=lambda x: x[2])",
    "    rq2r = max(rows, key=lambda x: x[3])",
    "    print(f\"{e:<12} | {rq1[0]+' (MAD='+format(rq1[1],'.4f')+')':<22} | \"",
    "          f\"{rq2s[0]+' (RStd='+format(rq2s[2],'.4f')+')':<22} | \"",
    "          f\"{rq2r[0]+' (r='+format(rq2r[3],'+.3f')+')':<22}\")",
))

# §7 The 4 qualitative patterns
cells.append(md(
    "## 6. The four qualitative failure-mode patterns",
    "",
    "The RQ2 statistics split the 15 (metric, element) cells into four",
    "qualitative patterns:",
    "",
    "1. **Pure constant offset** — calibratable by a shift. Example:",
    "   Metrik-4 on Association has `MAD = 0.275`, `bias = +0.274`,",
    "   slope ≈ 0.51. The metric consistently overshoots by ~0.27.",
    "2. **Linear rescalable** — calibratable by slope + intercept.",
    "   Example: Metrik-3 on Attribute has `r = 0.654` (highest of any",
    "   cell), `slope = 0.763`. A linear map turns it into a usable score.",
    "3. **Random noise** — uncorrectable. Example: Metrik-3 on",
    "   Association has `r = 0.049` — the metric is statistically",
    "   independent of the human F1 on this element.",
    "4. **Close but doesn't track ordering** — low MAD, low r. Example:",
    "   Metrik-5 on Class has the lowest MAD (0.074) but `r = 0.177`;",
    "   it disagrees about *ranking* the 39 pairs even though the",
    "   average error is small.",
    "",
    "The practical takeaway: **picking a metric is a (RQ1, RQ2,",
    "use-case) design choice, not a 'use the best one' choice.**",
    "Pick the lowest MAD per element for a single quality score; pick",
    "the highest Pearson r per element for a leaderboard ranking; pick",
    "low `|bias|/MAD` with non-zero r for a calibratable number.",
))

# §8 Per-pair scatter
cells.append(md(
    "## 7. Per-pair scatter: metric score vs human F1",
    "",
    "Each panel below is one (metric, element) pair. The 39 scatter",
    "points are the per-comparison scores; the dashed black line is",
    "`y = x` (the ideal metric); the solid red line is the OLS fit",
    "`human = intercept + slope × metric`.",
    "",
    "A tight scatter along the red line means the metric preserves the",
    "*ordering* of human-rated pairs (high Pearson r). A scatter that",
    "follows y = x closely means the metric is *well-calibrated* (low",
    "MAD).",
))
cells.append(code(
    "fig, axes = plt.subplots(5, 3, figsize=(11, 12), squeeze=False)",
    "element_labels = [('class', 'Class'), ('attribute', 'Attribute'), ('association', 'Association')]",
    "",
    "for row, (name, payload) in enumerate(per_metric.items()):",
    "    for col, (el_key, el_label) in enumerate(element_labels):",
    "        ax = axes[row][col]",
    "        xs, ys = [], []",
    "        for comp in payload['comparisons'].values():",
    "            xs.append(comp['metric_results'][f'{el_key}_score'])",
    "            ys.append(comp['human_metrics'][el_label]['f1'])",
    "        ax.scatter(xs, ys, s=18, alpha=0.7, edgecolor='black', linewidth=0.3)",
    "        ax.plot([0, 1], [0, 1], 'k--', alpha=0.4)",
    "        # OLS line",
    "        if xs:",
    "            mx, my = statistics.mean(xs), statistics.mean(ys)",
    "            sxx = sum((x - mx) ** 2 for x in xs)",
    "            sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))",
    "            slope = sxy / sxx if sxx > 0 else 0",
    "            intercept = my - slope * mx",
    "            xline = [0.0, 1.0]",
    "            yline = [max(0, min(1, intercept + slope * x)) for x in xline]",
    "            ax.plot(xline, yline, 'r-', alpha=0.6)",
    "            mad, rstd, abias, r = rq2_stats(payload, el_key)",
    "            ax.set_title(f\"{name} / {el_label}\\nMAD={mad:.3f}  r={r:+.2f}\", fontsize=9)",
    "        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect('equal')",
    "        ax.grid(':', alpha=0.3)",
    "        if row == 4:",
    "            ax.set_xlabel('metric score', fontsize=8)",
    "        if col == 0:",
    "            ax.set_ylabel('human F1', fontsize=8)",
    "",
    "fig.suptitle('Per-pair scatter: metric score vs human F1 (N=39 pairs / panel)', fontsize=12, fontweight='bold')",
    "fig.tight_layout(rect=[0, 0, 1, 0.97])",
    "fig.savefig('per_pair_scatter.png', dpi=120, bbox_inches='tight')",
    "plt.show()",
))

# §9 Final summary
cells.append(md(
    "## 8. Summary",
    "",
    "This walkthrough covered:",
    "",
    "- **The 5 metrics** and their source papers (table in §1 of the README).",
    "- **The 39-pair benchmark** (8 reference models × 5 LLM settings).",
    "- **The headline MAD table** (table in §4 above): the 5 metrics are",
    "  tied on overall MAD (0.16–0.17) but diverge per element.",
    "- **The no-free-lunch finding**: RQ1 (lowest MAD) and RQ2 (lowest",
    "  residual std) are answered by different metrics on every element.",
    "- **The 4 qualitative patterns** (constant offset / linear rescalable /",
    "  random noise / close-but-doesn't-track-ordering).",
    "- **The practical takeaway**: pick a metric by (RQ1, RQ2, use-case)",
    "  rather than searching for the single 'best' metric.",
    "",
    "For the full discussion (including per-metric failure-mode taxonomy",
    "and the planned LOO-CV ensemble metric), see the source",
    "`diss-metrik` publication plan:",
    "https://github.com/VasiliySeibert/diss-metrik/blob/main/Publication/publication.md",
))

# §10 References
cells.append(md(
    "## 9. References",
    "",
    "The 4 source papers that the 5 metrics implement:",
    "",
    "- **Singh, P., Boubekeur, Y. & Mussbacher, G. (2022).** *Detecting",
    "  mistakes in a domain model.* MODELS '22 Companion, pp. 257–266.",
    "  ACM. DOI: [10.1145/3550356.3561583](https://doi.org/10.1145/3550356.3561583)",
    "  → Metrik-1.",
    "- **Čech, P. (2019).** *Matching UML class models using graph edit",
    "  distance.* Expert Systems with Applications 130, 206–224.",
    "  DOI: [10.1016/j.eswa.2019.04.008](https://doi.org/10.1016/j.eswa.2019.04.008)",
    "  → Metrik-2.",
    "- **Yuan, Z., Yan, L. & Ma, Z. (2020).** *Structural similarity measure",
    "  between UML class diagrams based on UCG.* Requirements Engineering",
    "  25(2), 213–229.",
    "  DOI: [10.1007/s00766-019-00317-w](https://doi.org/10.1007/s00766-019-00317-w)",
    "  → Metrik-3.",
    "- **Triandini, E. (2021).** *Automated Class Diagram Assessment using",
    "  Semantic and Structural Similarities.* International Journal of",
    "  Intelligent Engineering Systems.",
    "  DOI: [10.22266/IJIES2021.0430.06](https://doi.org/10.22266/IJIES2021.0430.06)",
    "  → Metrik-4 and Metrik-5.",
))


# --------------------------------------------------------------------------
# Notebook assembly
# --------------------------------------------------------------------------

notebook: Dict[str, Any] = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.11",
            "mimetype": "text/x-python",
            "codemirror_mode": {"name": "ipython", "version": 3},
            "pygments_lexer": "ipython3",
            "nbconvert_exporter": "python",
        },
        "title": "domain-model-metrics: quantitative-results walkthrough",
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}


def main() -> None:
    out = Path(__file__).resolve().parent / "quantitative_results_walkthrough.ipynb"
    out.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out}  ({len(cells)} cells)")


if __name__ == "__main__":
    main()