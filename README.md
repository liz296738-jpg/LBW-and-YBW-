# Scramjet 1D CFD

## Project Goal

Develop a quasi-one-dimensional compressible-flow CFD solver and reproducible study workflow for scramjet and dual-mode ramjet combustors, with the **teacher-provided one-dimensional CFD / “second scheme” as the primary model target**.

> Naming note: `LBW` and `YBW` in the repository name are people/project identifiers. They are **not combustion-mode labels** and must never be interpreted as physical states.

## Current Status

Current stage: **P12 source-criterion application, after acceptance of the P11.4 project-defined H2 integrated baseline.**

The teacher-reference implementation path is substantially complete for the lean `H2` / `C2H4` branch. The repository contains the accepted chain from variable thermochemistry and algebraic composition closure through quasi-1D finite-volume marching, teacher-compatible source terms, boundary conditions, steady stopping diagnostics, and reproducible integrated cases.

Accepted P11.4 evidence includes:

- a clearly labelled `PROJECT_DEFINED_INTEGRATED_SMOKE_CASE` for H2;
- teacher Eq. 11.46 steady convergence reporting plus an independent normalized residual diagnostic;
- positive/source-valid thermodynamic states;
- a 20/40/80-cell numerical grid audit with decreasing successive changes in the reported extrema;
- a discrete conservation audit with normalized mass-inventory rate below the accepted 0.5% inlet-flow gate and normalized momentum/energy diagnostics;
- reproducible full 80-cell flow/composition profile artifacts;
- an explicit evidence gate for Cao Ruifeng doctoral Case 2.

The Cao Case 2 source identity and Table 2-2 inlet evidence are frozen. Formal reproduction is **not** claimed because the exact source `A(x)`, prescribed `Yi(x)` spatial profiles/rule, and original fuel/source spatial convention remain incomplete.

P12 has now recovered a defensible source-defined broad combustion-mode criterion directly from Cao Ruifeng's doctoral dissertation. For the thermal-throat distinction, Eq. (3-2) defines the scram side by `min(Ma(x)) > 1`, the ram side by `min(Ma(x)) < 1`, and the transition boundary at the critical thermal throat `Ma=1`. The source gives no floating-point sonic tolerance, so numerical tolerance is always an explicit project choice.

The accepted project-defined H2 response sweep has converged points at `phi=0.10` and `phi=0.20`; both remain on the Cao source-defined scram side. The cold-start `phi=0.30` point triggers the existing forward-flow model-domain guard and is deliberately left without a physical mode label. A guarded warm-start continuation is the next numerical step; it does not weaken the guard or convert numerical failure into a physical transition.

## Implemented Teacher-Path Physics and Numerics

Implemented and regression-tested infrastructure includes:

- unsteady quasi-one-dimensional conservative mass, momentum, and energy equations;
- variable-area geometry and non-duplicated `p dA/dx` treatment;
- source-backed piecewise thermochemistry for `H2`, `O2`, `N2`, `Ar`, `H2O`, `C2H4`, and `CO2`;
- `cp(T)`, absolute `h(T)`, internal energy, mixture molecular weight, `R(Y)`, and `gamma(T,Y)`;
- bounded internal-energy-to-temperature inversion;
- conservative/primitive conversion for per-cell variable composition;
- teacher Eq. 11.18 combustion-efficiency identity;
- teacher Eq. 11.19 mixing-efficiency correlations and Eq. 11.20 mixing length;
- teacher Eqs. 11.21-11.24 stoichiometry/equivalence-ratio relations;
- teacher lean `H2` / `C2H4` composition closures;
- single-injector finite-volume mapping with upstream air-only cells and no fuel double counting;
- teacher Eq. 11.38 fuel mass, axial momentum, and total-enthalpy source channels;
- teacher Eq. 11.25 friction with explicit `f_D=4f` mapping;
- teacher static `p/T/u` inlet and first-order/zero-gradient outlet semantics;
- first-order finite-volume interface treatment;
- SSP/TVD-RK3 integration;
- CFL-controlled pseudo-time stepping;
- teacher Eq. 11.46 maximum relative-density stopping diagnostic;
- Rusanov integrated numerical flux for the variable-thermochemistry production path;
- normalized mass/momentum/energy discrete inventory diagnostics;
- source-defined Cao thermal-throat criterion and source-faithful Table 3-1 utility;
- grid, conservation, robustness, and regression evidence.

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
- `cases/studies/data/p12_cao_mode_criterion_source.json`
- `cases/studies/data/teacher_cao_case2_source.json`
- `cases/studies/data/teacher_reference_alignment.json`

## Supporting V&V Work

The NASA Burrows-Kurkov and Jin/Liu evidence chains remain supporting V&V assets. They improve solver verification, provenance, and reduced-order benchmarking, but they do not replace the teacher-provided model or permit stronger source-reproduction claims than the available evidence supports.

## Development Philosophy

Correctness > verifiability > readability > extensibility > performance.

Every physical model and scientific claim is introduced independently, source-traced where applicable, and tested before stronger claims are allowed. Missing evidence is recorded as a blocker rather than filled with invented parameters.
