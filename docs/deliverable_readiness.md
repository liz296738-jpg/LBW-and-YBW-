# Course Deliverable Readiness Gate

This checklist separates **implemented/accepted evidence** from the stronger claim that the course project is fully deliverable. A checked item must point to evidence already accepted on `main`; an unchecked item must remain explicit rather than being inferred from solver behavior.

## Accepted core evidence

- [x] Reproducible project-defined H2 integrated case (`cases/studies/data/p11_4_project_defined_h2_smoke_acceptance.json`).
- [x] Teacher Eq. 11.46 maximum relative-density-change convergence is the authoritative steady-state gate; normalized residual is an independent diagnostic, not a second invented hard threshold.
- [x] Three-level 20/40/80 numerical grid trend (`cases/studies/data/p11_4_grid_convergence_acceptance.json`). This is a grid-convergence trend, not a formal asymptotic grid-independence/GCI claim.
- [x] Discrete mass, momentum, and energy inventory-rate diagnostics are available and normalized by documented inlet natural scales. Mass retains the accepted 0.5% gate; momentum and energy remain quantitative diagnostics without unsourced acceptance thresholds.
- [x] P12 project-defined equivalence-ratio response evidence is machine-readable (`cases/studies/data/p12_project_defined_response_sweep_acceptance.json`).
- [x] The stricter Eq. 11.46 `2e-5` continuation evidence is frozen (`cases/studies/data/p12_thermal_throat_continuation_acceptance.json`).
- [x] P12 thermal-throat grid-sensitivity evidence is frozen (`cases/studies/data/p12_thermal_throat_grid_sensitivity_acceptance.json`).
- [x] Forward-flow guard failures are recorded as `solver/model-domain inadmissible`; they are not interpreted as unstart or combustion-mode transitions.
- [x] Source/assumption boundaries and known blockers are maintained in `README.md`, `docs/development_roadmap.md`, `docs/teacher_reference_alignment.md`, and the evidence records.

## Required presentation/package closeout before marking the course project complete

- [x] Freeze one documented, copy-paste run command for the accepted H2 integrated baseline and one for the accepted P12 response study, with expected output locations (`docs/deliverable_runbook.md`).
- [ ] Freeze a compact deliverable results package containing the accepted convergence history, key axial distributions (`Mach`, `p`, `T`, `u`, `rho`, composition), 20/40/80 grid comparison, normalized mass/momentum/energy inventory diagnostics, and accepted equivalence-ratio response results.
- [ ] Add a single manifest mapping every plotted/tabulated deliverable result to its machine-readable acceptance/evidence record and provenance.
- [ ] Run the complete ordinary test suite and the relevant P12 numerical workflows on the final packaging commit; record the exact accepted commit/workflow provenance.

Until all unchecked items above are closed, the repository may describe P11.4/P12 evidence as accepted where applicable, but must **not** mark the overall course project as `deliverable complete`.

## Scientific claim boundaries that remain after packaging

Packaging completion does not remove source blockers. In particular:

- Cao Case 2 is not a formal reproduction without exact source `A(x)`, prescribed `Yi(x)` spatial information/rule, and the original fuel/source spatial convention.
- The integrated variable-thermochemistry production path remains Rusanov unless a defensible source resolves the Steger-Warming energy-reference/epsilon issues.
- Eq. 11.26 is not converted into a dimensional wall-heat source without a defensible source mapping.
- The scoped Cao Eq. (3-2) thermal-throat criterion must not be generalized into broader ramjet/scramjet/dual-mode/unstart labels without the required source-compatible observables and geometry.
