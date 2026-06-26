# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- LOO-CV ensemble metric (Metrik-6) tracing a Pareto curve in the
  (RQ1, RQ2) plane.
- Bootstrap confidence intervals on per-metric MAD values.

## [1.0.0] - 2026-06-26

The canonical first public release. The intermediate patch versions
**v1.0.1, v1.0.2, v1.0.3, v1.0.4, v1.0.5** were published earlier on
the same day and retired 2026-06-26 to align the version string in
the source tree with the GitHub Release tag and the Zenodo version
DOI. They were never cited externally. Their archived commit SHAs
(preserved for provenance) are listed at the bottom of this entry.

### Added
- First public FAIR4RS release of the `domain-model-metrics` package.
- Five domain-model similarity metrics (Metrik-1..5) implemented in
  `Metric-Implementation/`, each with three design iterations
  (`Implementation-1`, `Implementation-2`, `Implementation-3` for
  Metrik-1..3 and `Implementation_1`, `Implementation_2`,
  `Implementation_3` for Metrik-4..5).
- Per-metric PlantUML parser bundled with each metric
  (`Metric-Implementation/Metrik-N/Parser/`).
- Per-metric design specs (`Specification/s1.md`, `s2.md`).
- Per-metric invariant validators and test scripts (`Testset/`).
- Quantitative-analysis workflow (`Quantitative-Analysis/Workflow/`).
- Runnables for each metric (`Quantitative-Analysis/RunMetrics/`).
- Bundled 39-pair dataset (`data/combined-data.json`):
  8 reference domain models × 5 LLM prompting settings (`0shot`,
  `1shot_BTMS`, `1shot_H2S`, `2shots`, `CoT`) with human-evaluated
  F1 ground truth for Class, Attribute, Association.
- Pre-computed per-metric results JSONs in
  `Quantitative-Analysis/Results/`.
- Thin Python wrapper package `domain_model_metrics` providing a
  uniform `MetricProtocol` API over the 5 canonical implementations.
- Cross-metric comparison tool (`domain_model_metrics.compare`).
- Walkthrough notebook
  (`Notebooks/quantitative_results_walkthrough.ipynb`) narrating the
  headline MAD table and the no-free-lunch finding.
- FAIR4RS metadata: `CITATION.cff` (CFF 1.2.0),
  `codemeta.json` (CodeMeta 2.0), Zenodo integration enabled.
- GitHub Actions CI on Python 3.11 and 3.12.
- `pyproject.toml` (PEP 621) with `pip install domain-model-metrics`.

### Headline result
- The 5 metrics are nearly tied on overall MAD (0.16–0.17) but diverge
  sharply on per-element MAD — see README §"Results" for Table 1.

### README structure
The README is organised as: (1) the five metric definitions,
(2) §Results with Table 1 + per-element narratives,
(3) §Implementation methodology with the spec → invariants →
`@icontract` → code pattern diagram, (4) §Discussion with
RQ1/RQ2 + per-use-case selection + 4 qualitative failure-mode
patterns + 2 risks + validity of the human F1 ground truth, and
(5) §Repository layout + §How this repository maps to FAIR4RS +
§Citing this software.

### Notes
- Public API: `domain_model_metrics.get_metric("metrik-N").compute(ref, gen)`.
- No code change since the v1.0.1 patch series (v1.0.1..v1.0.5 were
  metadata + README-only). All 26 tests pass, 2 skipped (Metrik-4/5 slow).

### Archived intermediate versions (retired 2026-06-26, never cited)
| Tag | Commit SHA |
|-----|------------|
| v1.0.1 | `c112d3b2be53ec52dad53f28dd916ba67c1feb4f` |
| v1.0.2 | `abd5745fac1c1775d4cbbffcdc22e02d5825b050` |
| v1.0.3 | `47fa20ec7d879c2ac11e54cbb540e33e680d0688` |
| v1.0.4 | `1d4b419affe84002870565d4d10f2abac4a20255` |
| v1.0.5 | `e0e1c34fb6a6f6f69def698c0555f2fccf07558d` |
| v1.0.0 (pre-retirement, first commit of the repo) | `054441f589d6d9c6ac493d005e7f58894fe99cae` |