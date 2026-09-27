# Project paper

The canonical continuously maintained paper is:

- [main_paper_zh.md](main_paper_zh.md) — Chinese main paper source.

## Maintenance policy

- This Markdown file is the single source of truth for the paper.
- Word/PDF files are release snapshots generated from the Markdown source.
- Data-driven Figures 2--4 are regenerated from frozen acceptance JSON with `python tools/build_paper_figures.py`; the figure script does not run CFD or create new evidence.
- `paper/evidence_map.json` maps result/limitation sections and paper figures to the exact repository evidence that supports them.
- Only results that have entered the repository acceptance/evidence workflow are promoted from "in progress" to paper conclusions.
- When a stronger accepted result supersedes an older result, historical provenance remains in the repository while the paper adopts the latest accepted evidence.
- Source-gated physics must remain explicitly unresolved until authoritative evidence or a separately validated new model branch closes the gap.
- Project-selected tolerances, case parameters and study designs remain labelled as project-defined.

Version v0.1 includes the accepted P11.4, NASA Burrows-Kurkov reduced-order benchmark, and P12 evidence. P13 C_m sensitivity is intentionally listed as in progress until its dedicated CFD workflow produces reviewed acceptance evidence. The first P13/P11.4 maintenance reruns reached the former 45-minute GitHub Actions timeout while executing multiple CFD solves sequentially. The workflows have since been redesigned to run frozen grid/case points as independent parallel jobs and to aggregate their JSON outputs without rerunning the solver. This changes CI scheduling only: equations, case inputs, grid levels, tolerances, guards, and scientific acceptance rules are unchanged.
