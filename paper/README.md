# Project paper

The canonical continuously maintained paper is:

- [main_paper_zh.md](main_paper_zh.md) — Chinese main paper source.

## Maintenance policy

- This Markdown file is the single source of truth for the paper.
- Word/PDF files are release snapshots generated from the Markdown source.
- Data-driven Figures 2--5 are regenerated from frozen acceptance JSON with `python tools/build_paper_figures.py`; the figure script does not run CFD or create new evidence.
- `paper/evidence_map.json` maps result/limitation sections and paper figures to the exact repository evidence that supports them.
- Only results that have entered the repository acceptance/evidence workflow are promoted from "in progress" to paper conclusions.
- When a stronger accepted result supersedes an older result, historical provenance remains in the repository while the paper adopts the latest accepted evidence.
- Source-gated physics must remain explicitly unresolved until authoritative evidence or a separately validated new model branch closes the gap.
- Project-selected tolerances, case parameters and study designs remain labelled as project-defined.

Version v0.2 adds the reviewed P13 teacher-range `C_m` sensitivity acceptance to the previously accepted P11.4, NASA Burrows-Kurkov reduced-order benchmark, and P12 evidence. P13 is a project-defined sensitivity study over the teacher Eq.11.20 source range; it does not establish an optimum `C_m`, experimental validation, formal Cao Case 2 reproduction, or grid independence. The P13/P11.4 maintenance workflows use independent parallel CFD jobs plus artifact-only aggregation; this changes CI scheduling only, not equations, case inputs, grid levels, tolerances, guards, or scientific acceptance rules.
