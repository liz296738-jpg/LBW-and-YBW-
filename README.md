# Scramjet 1D CFD

## Project Goal

Develop a quasi-one-dimensional, compressible-flow CFD solver and reproducible study workflow for scramjet and dual-mode ramjet combustors, with the **teacher-provided one-dimensional CFD / “second scheme” as the primary model target**.

> Naming note: `LBW` and `YBW` in the repository name are people/project identifiers. They are **not combustion-mode labels** and must never be interpreted as physical states.

## Current Status

Current stage: **teacher-reference second-scheme alignment and physical-closure completion.**

P0-P10 established the numerical/verification foundation. P11.1 added reproducible parametric-study infrastructure. P11.2A established a literature-backed public cold-flow surrogate. P11.2B now includes an accepted, deliberately scoped NASA Burrows-Kurkov **reduced-order computational-reference benchmark**; this supporting benchmark is useful for verification but is not the teacher's primary requested deliverable.

The uploaded teacher material confirms that our main numerical route is substantially correct: unsteady quasi-one-dimensional conservation equations, variable area, friction/heat/mass-addition source terms, first-order upwind/Steger-Warming spatial treatment, third-order TVD Runge-Kutta advancement, CFL stepping, and steady convergence. The remaining work is concentrated in the **teacher-reference physical closure layer**, especially variable thermochemistry/composition and empirical mixing/combustion closures.

The earlier plan to interpret `LBW`/`YBW` as combustion modes was incorrect and has been abandoned. Combustion-mode-transition studies remain a later scientific application after the teacher-reference model is complete.

## Solver Foundation

Implemented and verified infrastructure includes:

- conservative quasi-one-dimensional mass, momentum, and energy equations;
- variable-area duct source treatment;
- prescribed Darcy wall-friction momentum source;
- prescribed wall-heat-flux energy source;
- prescribed local/distributed fuel mass, momentum, and total-enthalpy addition;
- prescribed burned-fuel/LHV and direct line-heat-release surrogate interfaces;
- Rusanov and raw Steger-Warming flux-vector splitting;
- first-order finite volumes/upwind interface treatment;
- third-order SSP/TVD Runge-Kutta;
- CFL-based time stepping;
- physical/transmissive boundary-condition infrastructure;
- steady convergence, robustness, conservation, grid, and regression tests.

The direct prescribed `Qdot'(x)` path remains a useful **reduced-order surrogate**. It is not automatically equivalent to the teacher-reference reacting formulation.

## Teacher-Reference Alignment

Detailed review:

`docs/teacher_reference_alignment.md`

Machine-readable status:

`cases/studies/data/teacher_reference_alignment.json`

Strongly aligned already:

- unsteady quasi-1D conservative PDE structure;
- area, friction, wall heat, and mass/momentum/enthalpy source architecture;
- Steger-Warming FVS;
- first-order spatial discretization;
- third-order TVD/SSP RK;
- CFL-controlled stepping;
- compatible supersonic inflow / zero-gradient-like outflow capability.

Main gaps to close:

1. temperature- and composition-dependent mixture thermodynamics (`cp(T)`, `h(T)`, `R(Y)`, `gamma(T,Y)`);
2. teacher-reference mixing efficiency / mixing-length closure;
3. equivalence-ratio and fuel-specific composition closure;
4. teacher empirical friction and wall-heat closures as optional models;
5. near-sonic Steger-Warming eigenvalue smoothing once its epsilon policy is source-frozen;
6. integrated teacher-reference case and regression evidence.

A compatibility implementation of the teacher's relative-density steady criterion (Chapter 11 Eq. 11.46) is being added alongside—not in place of—the existing normalized residual criterion.

## Energy-Accounting Rule

The teacher reference distinguishes external wall/additional heat from chemical-reaction energy. When variable composition and species enthalpy are introduced, the same chemical energy must not be counted both through species/enthalpy changes and again through the direct prescribed heat-release source.

This is a project-level invariant: **no silent double counting of chemical energy.**

## Supporting V&V Work

The NASA Burrows-Kurkov and Jin/Liu evidence chains remain in the repository because they improve solver verification, provenance, and reduced-order benchmarking. They are supporting V&V assets, not substitutes for implementing the teacher-provided model.

## Development Philosophy

Each physical model and scientific claim is introduced independently, source-traced where applicable, tested, and validated before stronger claims are allowed. Teacher-provided material has priority for the target model; public literature supplements it rather than redefining the project goal.
