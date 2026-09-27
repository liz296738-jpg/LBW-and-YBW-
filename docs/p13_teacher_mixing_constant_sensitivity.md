# P13 — Teacher Eq.11.20 Mixing-Constant Sensitivity Protocol

## Scientific question

How sensitive is the accepted project-defined H2 teacher-path solution to the teacher Eq.11.20 mixing-length constant `C_m` when every other case input and numerical control is held fixed?

This is a **predefined sensitivity study**, not a source reproduction, calibration exercise, optimization, or experimental validation.

## Source-backed factor domain

Teacher Chapter 11 Eq.11.20 gives the admissible range

`25 <= C_m <= 60`.

The project does not infer a probability distribution or a preferred value inside that interval.

The study samples:

- `C_m=25`: source-range lower bound;
- `C_m=30`: already frozen project baseline;
- `C_m=42.5`: project-defined arithmetic midpoint;
- `C_m=60`: source-range upper bound.

The *range* is source-backed. The *sampling design* is project-defined.

## Pre-registered algebraic expectation

For the current baseline, the injection branch is `parallel`. Teacher Eq.11.20 gives a mixing length of the form

`L_m = K(phi,b) C_m`

for fixed equivalence ratio `phi` and combustor height `b`. Therefore, over this one-factor-at-a-time study,

`L_m proportional to C_m`.

For parallel injection, teacher Eq.11.19 gives

`eta_m,raw = x / L_m`.

Thus, at a fixed downstream position and with every other baseline input fixed:

- increasing `C_m` must increase `L_m`;
- increasing `C_m` must not increase the raw mixing efficiency;
- the project adapter `eta=min(eta_m,raw,1)` must likewise not increase.

These are algebraic closure checks. They are **not predictions of monotonic Mach, pressure, or temperature response**, because the coupled quasi-1D solution also contains area, friction, injection, thermochemistry, and nonlinear conservation effects.

### Baseline geometry implication from Eq.11.20

For the frozen baseline `phi=0.20` and combustor height `b=0.040 m`, the lean Eq.11.20 branch gives:

| C_m | complete-mixing length L_m (m) | relation to 0.32 m injector-to-exit distance |
| ---: | ---: | --- |
| 25.0 | 0.25249 | complete mixing can be reached before the geometric exit |
| 30.0 | 0.30299 | complete mixing can be reached only near the geometric exit |
| 42.5 | 0.42924 | complete mixing is not reached within the current combustor length |
| 60.0 | 0.60598 | complete mixing is not reached within the current combustor length |

The available geometric distance is `0.40 - 0.08 = 0.32 m`. This comparison follows directly from the frozen project geometry and the teacher Eq.11.20 closure; it does not use any P13 CFD result. It therefore provides a pre-solution explanation for why the lower and upper parts of the `C_m` range may behave differently, while still making no monotonic prediction for coupled Mach, pressure, or temperature extrema.

## Frozen controls

The study reuses the P11.4 baseline input ledger:

`cases/studies/data/p11_4_project_defined_h2_input_provenance.json`

Only `C_m` changes. In particular, the following remain frozen:

- project-defined combustor geometry;
- inlet static pressure, temperature, and axial velocity;
- H2 equivalence ratio `phi=0.20`;
- injector position;
- parallel-injection branch;
- injected-fuel temperature and axial velocity;
- zero explicit wall-heat gradient while Eq.11.26 mapping remains source-gated;
- production Rusanov flux;
- SSP-RK3/CFL controls;
- teacher Eq.11.46 convergence metric with separately frozen project numerical tolerance.

## Numerical design

The primary factor study uses 20 and 40 cells.

The two-grid comparison is intentionally a **robustness diagnostic only**. It is insufficient to establish an asymptotic range, formal Richardson extrapolation, or a GCI/grid-independence claim.

For every converged point, the study records:

- teacher Eq.11.46 density-change metric;
- normalized residual diagnostic;
- normalized mass/momentum/energy inventory diagnostics;
- minimum/maximum Mach;
- minimum/maximum static pressure;
- minimum/maximum static temperature;
- injected fuel mass flow.

The prescribed injected fuel mass flow must remain invariant with `C_m`; otherwise the study would be changing more than one factor.

## Acceptance and interpretation rules

A computational point may be reported as converged only if it satisfies the frozen project tolerance applied to the teacher Eq.11.46 metric and remains thermodynamically admissible.

The 0.5% mass-inventory gate is retained as an explicitly **project-defined QA threshold**, not as a teacher/paper/NASA/ASME universal standard. Momentum and energy inventory values remain quantitative diagnostics without invented hard thresholds.

If the preserved forward-flow guard triggers, the point is recorded as `solver/model-domain inadmissible`. It is not labelled as unstart, ramjet, scramjet, or a physical combustion-mode transition.

## Claims that are prohibited from this study

P13 alone cannot establish:

- an “optimal” `C_m`;
- the true physical `C_m` for Cao Case 2 or another engine;
- experimental validation;
- formal Cao Case 2 reproduction;
- a grid-independent transition boundary;
- an unstart or broad dual-mode classifier;
- validity of the unresolved Eq.11.26 wall-heat mapping;
- validity of a variable-thermochemistry Steger--Warming production flux.

## External context

Peer-reviewed reduced-order scramjet studies support mixing-limited / mixing-efficiency modeling as a legitimate engineering-model component, but they do not supply the teacher Eq.11.20 coefficient range or identify the correct `C_m` for this project. See `docs/peer_reviewed_cross_validation.md`.

This protocol is frozen before interpreting the P13 CFD output so that result selection does not redefine the scientific question after the fact.
