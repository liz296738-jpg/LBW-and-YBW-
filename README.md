# Scramjet 1D CFD

## Project Goal

Develop a quasi-one-dimensional compressible-flow CFD solver and reproducible study workflow for scramjet and dual-mode ramjet combustors, with the **teacher-provided one-dimensional CFD / “second scheme” as the primary model target**.

> Naming note: `LBW` and `YBW` in the repository name are people/project identifiers. They are **not combustion-mode labels** and must never be interpreted as physical states.

## Current Status

Current stage: **P12 source-criterion application, after acceptance of the P11.4 project-defined H2 integrated baseline.**

The teacher-reference implementation path is substantially complete for the lean `H2` / `C2H4` branch. Accepted P11.4 evidence includes the clearly labelled `PROJECT_DEFINED_INTEGRATED_SMOKE_CASE`, teacher Eq. 11.46 convergence reporting, positive/source-valid states, a 20/40/80-cell grid trend, discrete conservation diagnostics, reproducible 80-cell profiles, and the explicit Cao Case 2 evidence gate.

The Cao Case 2 source identity and Table 2-2 inlet evidence are frozen. Formal reproduction is **not** claimed because the exact source `A(x)`, prescribed `Yi(x)` spatial profiles/rule, and original fuel/source spatial convention remain incomplete.

P12 has frozen the scoped Cao Eq. (3-2) thermal-throat criterion. The accepted project-defined H2 response sweep converges at `phi=0.10` and `phi=0.20` under the authoritative Eq. 11.46 `2e-5` density-change gate. A composition-consistent warm-start continuation at 20 cells also converges at `phi=0.22` and `phi=0.24`; all accepted points remain on the scoped Eq. (3-2) scram side. At the same `2e-5` gate, `phi=0.26` triggers the preserved forward-flow guard and is recorded only as `solver/model-domain inadmissible`, with no physical mode label. The older `1e-4` near-sonic `phi=0.26` continuation evidence is superseded and is not accepted transition evidence.

Grid-refined project-defined evidence separately records `phi=0.24` on the Eq. (3-2) scram side for 20/40/80 cells while `phi=0.26` is solver/model-domain inadmissible on all three grids. This is a grid-convergence trend/criterion application only; no grid-independent transition equivalence ratio is claimed.

## Implemented Teacher-Path Physics and Numerics

Implemented and regression-tested infrastructure includes quasi-1D conservative mass/momentum/energy equations, variable area, source-backed variable thermochemistry, bounded state recovery, teacher Eqs. 11.18-11.25 and 11.38 source/closure relations, teacher-compatible boundaries, first-order finite-volume interfaces, SSP/TVD-RK3, CFL stepping, Eq. 11.46 density-change diagnostics, Rusanov production flux, normalized mass/momentum/energy inventory diagnostics, the scoped Cao thermal-throat criterion, and grid/conservation/robustness evidence.

The direct prescribed `Qdot'(x)` capability remains only a reduced-order surrogate/V&V interface. Chemical reaction energy is not silently counted both through composition-dependent absolute species energy and through an independent heat-release source.

## Deliberately Gated Items

The following items are intentionally **not guessed**:

1. `C10H22` thermochemistry compatible with the frozen teacher/CHEMKIN convention;
2. the dimensional mapping needed to turn photographed Eq. 11.26 into the exact `d(delta q)/dx` energy-source input;
3. a production variable-thermochemistry Steger-Warming energy correction and a numerical Eq. 11.44 epsilon policy;
4. the missing Cao Case 2 spatial geometry/composition/source information required for formal reproduction;
5. source-compatible isolator/shock-train state variables and geometry required to attach the detailed Cao Table 3-1 classifier to the current integrated production path.

Teacher Eqs. 11.42-11.44 Steger-Warming are retained as a separately audited source-transcription path. Their classic closed form is valid in the calorically-perfect constant-property limit, but the examined teacher/Cao sources do not provide a defensible correction for the project's variable `cp(T,Y)` plus absolute species-energy formulation. The integrated variable-thermochemistry solver therefore remains on Rusanov rather than inventing an energy-reference fix.

## Key Evidence Records

- `docs/development_roadmap.md`
- `docs/teacher_reference_alignment.md`
- `docs/teacher_steger_warming_source_audit.md`
- `docs/p12_project_defined_mode_transition_foundation.md`
- `docs/p12_cao_source_mode_criteria.md`
- `docs/p12_cao_criterion_application.md`
- `cases/studies/data/p11_4_project_defined_h2_smoke_acceptance.json`
- `cases/studies/data/p11_4_grid_convergence_acceptance.json`
- `cases/studies/data/p11_4_cao_case2_evidence_gate.json`
- `cases/studies/data/p12_project_defined_response_sweep_acceptance.json`
- `cases/studies/data/p12_thermal_throat_continuation_acceptance.json`
- `cases/studies/data/p12_cao_mode_criterion_source.json`
- `cases/studies/data/teacher_cao_case2_source.json`
- `cases/studies/data/teacher_reference_alignment.json`

## Supporting V&V Work

The NASA Burrows-Kurkov and Jin/Liu evidence chains remain supporting V&V assets. They improve solver verification, provenance, and reduced-order benchmarking, but they do not replace the teacher-provided model or permit stronger source-reproduction claims than the available evidence supports.

## Development Philosophy

Correctness > verifiability > readability > extensibility > performance.

Every physical model and scientific claim is introduced independently, source-traced where applicable, and tested before stronger claims are allowed. Missing evidence is recorded as a blocker rather than filled with invented parameters.
