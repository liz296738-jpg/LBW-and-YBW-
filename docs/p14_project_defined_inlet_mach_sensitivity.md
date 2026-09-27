# P14 — Project-Defined Inlet-Mach Sensitivity Protocol

## Scientific question

How sensitive is the accepted project-defined H2 teacher-path solution to the prescribed **supersonic inlet Mach number** when the inlet static pressure, static temperature, dry-air composition, combustor geometry, equivalence ratio, injector location, mixing closure, fuel state and numerical controls are held fixed?

This is a **project-defined sensitivity study**. It is not a source reproduction, experimental validation, flight-Mach performance map, or combustion-mode classifier.

## Why study Mach 2.0--2.6?

The sampled interval is supported as an engineering-relevant context by three separate pieces of evidence, but none of them is allowed to redefine the current project model:

1. Cao's teacher-provided Case 2 reports isolator-entrance Mach 2.12 for an H2 case. Its inlet composition and unresolved spatial inputs differ from the current project baseline, so it is source context rather than a reproduction.
2. Shome (2025), *Physics of Fluids*, DOI `10.1063/5.0267063`, reports comparison of a quasi-one-dimensional H2-air scramjet isolator-combustor model with higher-fidelity CFD at inlet Mach 2 and equivalence ratio 0.2.
3. Byun & Choi (2026), *Journal of Propulsion and Power*, DOI `10.2514/1.B39243`, experimentally compare isolator entrance Mach 2.2, 2.4 and 2.6. Their cavity geometry and surrogate fuel differ from this project, so the measurements support variable relevance/range context only, not P14 validation.

The project therefore samples `M_target = 2.0, 2.2, 2.4, 2.6` as a **project-defined, literature-anchored even grid**. The repository does not call 2.0--2.6 a teacher admissible range or a validation interval.

Machine-readable source context: `cases/studies/data/p14_inlet_mach_literature_context.json`

## Boundary parameterization

The existing teacher boundary prescribes static `p/T/u`. P14 freezes static pressure at 55 kPa, static temperature at 800 K, and the teacher dry-air inlet composition (`phi=eta=0` at the boundary).

For each target Mach, the project derives the inlet speed from the same thermochemistry used by the solver:

`a = sqrt(gamma(T,Y) R(Y) T)`

`u = M_target a`.

Because `p`, `T` and inlet composition remain fixed, inlet density `rho = p/(R T)` is invariant across P14. Therefore `m_dot_air = rho u A_in` is proportional to target Mach.

The equivalence ratio remains frozen at `phi=0.20`, so the teacher fuel-flow definition gives `m_dot_f = phi f_st m_dot_air`. Fuel mass flow therefore changes proportionally with air mass flow. This is a dependent consequence of preserving equivalence ratio, **not** a second independently varied study factor.

This distinction is important: P14 is a **fixed-static-state inlet-Mach sensitivity**. It does not hold total pressure or total temperature fixed, so it must not be described as a flight-Mach performance sweep.

## Frozen controls

P14 reuses the P11.4 project-defined H2 controls:

- 0.40 m mild linear-divergence combustor;
- 0.0040 to 0.0050 m2 area;
- 0.040 m fixed height;
- nominal injector target coordinate 0.08 m, realized at the frozen nearest cell center (0.070 m on 20 cells and 0.075 m on 40 cells);
- H2 fuel, `phi=0.20`;
- `C_m=30`, parallel-injection branch;
- injected fuel temperature 450 K;
- injected fuel axial velocity 120 m/s;
- explicit wall-heat-gradient input = 0 while Eq.11.26 mapping is source-gated;
- variable-thermochemistry Rusanov production path;
- SSP-RK3;
- CFL = 0.5;
- teacher Eq.11.46 metric with project numerical tolerance `2e-5`;
- max steps = 20,000.

Only the target inlet Mach is selected independently.

## Pre-registered algebraic expectations

Before CFD results are inspected:

1. inlet sound speed must be identical for every point because `T` and inlet composition are fixed;
2. inlet velocity must be exactly proportional to target Mach;
3. inlet density must be invariant;
4. inlet air mass flow must be proportional to target Mach;
5. fuel mass flow must be proportional to air mass flow while the fuel/air mass ratio remains invariant;
6. no monotonic response is assumed in minimum/maximum Mach, pressure, temperature, convergence steps, or conservation diagnostics.

Items 1--5 are implementation/closure contracts. Item 6 prevents post-hoc interpretation of nonlinear CFD extrema as though algebra alone predicted them.

## Numerical design

Each target Mach is computed on 20 and 40 cells. The two-grid comparison is a **robustness diagnostic only**; it cannot establish formal Richardson/GCI or grid independence.

For converged points P14 records target and actual inlet Mach, derived inlet velocity, inlet air mass flow, injected fuel mass flow, teacher Eq.11.46 density-change metric, normalized residual, normalized mass/momentum/energy inventory diagnostics, min/max Mach, min/max static pressure, and min/max static temperature.

## Status and claim policy

A point may be reported as `CONVERGED` only when it satisfies the frozen project tolerance applied to teacher Eq.11.46 and remains thermodynamically admissible.

The existing project-defined normalized mass-inventory QA gate remains 0.5%. Momentum and energy inventories remain finite nonnegative diagnostics without invented hard thresholds.

If the preserved forward-flow friction guard triggers, the point is recorded as `solver/model-domain inadmissible`. It is **not** relabelled as unstart, ramjet/scramjet, dual-mode transition, or a physical Mach boundary.

P14 cannot by itself establish a universal optimum inlet Mach, a flight-Mach performance law under fixed total conditions, experimental validation, Cao Case 2 reproduction, a combustion-mode/unstart classifier, formal grid independence from the 20/40 comparison, validity of the unresolved Eq.11.26 wall-heat mapping, or validity of variable-thermochemistry Steger-Warming production flux.

The protocol is frozen before the dedicated CFD workflow is interpreted.
