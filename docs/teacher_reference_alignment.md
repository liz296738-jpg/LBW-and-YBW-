# Teacher-reference alignment review

## Authority and naming boundary

The teacher-provided Chapter 11 material and the two Cao Ruifeng theses remain the primary project authority. Public NASA/Jin/Liu work is supporting V&V only.

`LBW` and `YBW` are people/project identifiers, not combustion-mode labels.

## Current alignment status

The defensible H2/C2H4 teacher path is now integrated and regression-tested on the production Rusanov route. Implemented teacher-aligned elements include quasi-1D conservative finite-volume equations, variable area, SSP/TVD-RK3, CFL stepping, static p/T/u inlet and zero-gradient outlet semantics, Eq. 11.46 maximum relative-density convergence reporting, source-backed variable thermochemistry, lean H2/C2H4 algebraic composition closure, Eqs. 11.18-11.24 mixing/stoichiometric relations, Eq. 11.25 friction, and Eq. 11.38 fuel mass/momentum/total-enthalpy source channels.

The accepted `PROJECT_DEFINED_INTEGRATED_SMOKE_CASE` is implementation/V&V evidence, not a source reproduction. Its 20/40/80-cell grid audit and discrete conservation audit are accepted. Mass inventory uses the existing 0.5% inlet-flow gate; momentum and energy inventory rates remain dimensionless diagnostics without invented acceptance thresholds.

## Numerical-path boundary

Teacher Eqs. 11.42-11.44 Steger-Warming remain an audited source-transcription path. The calorically-perfect limit is verified, but the available teacher/Cao evidence does not provide a defensible variable-thermochemistry energy-reference correction or numerical Eq. 11.44 epsilon policy. The integrated variable-thermochemistry path therefore remains Rusanov. This is an explicit blocker, not an invitation to guess a correction.

## Thermochemistry and energy accounting

Source-backed piecewise thermochemistry is frozen for `H2`, `O2`, `N2`, `Ar`, `H2O`, `C2H4`, and `CO2`. `C10H22` remains source-gated.

Absolute species enthalpy includes sensible plus chemical/zero-point contribution. Composition change and an independent direct chemical `Qdot` must not represent the same chemical energy twice. External wall/additional heat remains a separate channel.

The dimensional mapping from photographed Eq. 11.26 to the exact wall-specific-heat-gain-gradient input remains unresolved and must not be invented.

## Cao Case 2 evidence gate

The source record is no longer missing. The Cao Case 2 identity and Table 2-2 inlet evidence are frozen, including H2 fuel, `Ma=2.12`, `rho=0.28 kg/m^3`, `p=46.7 kPa`, `T=521 K`, `u=977 m/s`, reported `k=1.33`, `phi=0.2`, inlet composition, `Tw=900 K`, and reported grid spacings.

Formal source reproduction remains blocked by three unresolved spatial inputs:

1. exact source `A(x)`;
2. exact prescribed `Yi(x)` spatial profiles/rule;
3. original fuel/injection/source spatial convention.

The project-defined geometry or algebraic closure must not substitute for these missing source inputs.

## P12 response-study boundary

P12 currently permits project-defined continuous response studies. Accepted outputs include Mach, pressure, temperature, velocity, density, composition, Eq. 11.46 convergence status, dimensionless conservation diagnostics, and solver-admissibility status.

The source-backed Cao Eq. (3-2) thermal-throat criterion may be reported exactly within its documented scope, but a forward-flow guard trigger, nonconvergence, or a single local Mach observation must not be promoted into an `unstart`, `ramjet`, `scramjet`, or `dual-mode` physical claim outside the frozen criterion scope.

The grid-refined project-defined evidence currently shows `phi=0.24` remaining on the Eq. (3-2) scram side for 20/40/80 cells, while `phi=0.26` is solver/model-domain inadmissible on all three grids. This does not establish a grid-independent transition equivalence ratio.

## Remaining explicit blockers

- compatible `C10H22` thermochemistry if that branch becomes necessary;
- dimensional Eq. 11.26 wall-heat mapping;
- variable-thermochemistry Steger-Warming production energy compatibility and Eq. 11.44 epsilon policy;
- Cao Case 2 exact `A(x)`, `Yi(x)`, and source/injection spatial convention;
- source-compatible isolator/shock-train state variables and geometry required for broader categorical mode-transition classification.

## Governing evidence records

- `docs/development_roadmap.md`
- `docs/teacher_steger_warming_source_audit.md`
- `docs/p12_cao_source_mode_criteria.md`
- `docs/p12_cao_criterion_application.md`
- `cases/studies/data/p11_4_project_defined_h2_smoke_acceptance.json`
- `cases/studies/data/p11_4_grid_convergence_acceptance.json`
- `cases/studies/data/p11_4_cao_case2_evidence_gate.json`
- `cases/studies/data/p12_project_defined_response_sweep_acceptance.json`
- `cases/studies/data/p12_cao_mode_criterion_source.json`
- `cases/studies/data/teacher_cao_case2_source.json`
- `cases/studies/data/teacher_reference_alignment.json`
