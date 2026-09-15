# Scramjet 1D CFD

## Project Goal

Develop a quasi-one-dimensional, compressible-flow CFD solver and reproducible study workflow for scramjet and dual-mode ramjet combustors.

## Current Status

Current stage: **P11.2B heated-case preparation and evidence closure.** P10 overall verification and validation is complete at accepted SHA `cac804a30f325ddf1875ab5188353cdbbf9e5de6`. P11.1 study infrastructure is implemented and verified. P11.2A has a formally verified, literature-backed, physical-scale non-reactive public-surrogate baseline. P11.2B adds a regression-verified direct prescribed line heat-release interface and source-backed heat-release/geometry infrastructure, but promotion of a formal heated validation case remains evidence-gated.

The preferred P11.2B independent-validation chain is the Jin–Liu model-B configuration. Its axial geometry, study-layer radial area law, and the mapping from Jin's wall-friction coefficient convention to the repository Darcy factor are now resolved. Formal promotion is still blocked by the remaining source-evidence gaps tracked in `artifacts/p11_2b/p11_2b_readiness.json`: validation-condition identity, the exact station-3 inlet state, the numerical wall-friction coefficient used by the source case, and a same-condition heat-release shape plus absolute energy scale.

No P11.2 result is an LBW/YBW classification. P11.3 will separately freeze the authoritative LBW/YBW definitions and discrimination criterion before any regime map is produced.

## Solver Foundation

P3 is complete: ideal-gas thermodynamics, primitive/conservative conversion, Euler physical flux, Rusanov numerical flux, finite-volume spatial residual, SSP-RK3, transmissive boundaries, CFL time stepping, a transient solver loop, a Sod-type shock-tube smoke test, automated tests, and GitHub Actions CI form the constant-area baseline solver.

P4 adds variable-area quasi-one-dimensional geometry and validates the inviscid, adiabatic, constant-gamma area physics. P5 adds raw Steger-Warming flux-vector splitting alongside Rusanov and validates smooth-flow convergence, dissipation behaviour, shock robustness, and near-sonic finite-state behaviour.

P6 adds prescribed Darcy wall friction and wall heat flux. P7 adds prescribed local and distributed fuel mass/momentum/energy injection. P8 adds prescribed distributed combustion heat release. P9 adds physical inlet/outlet boundaries and steady convergence/robustness diagnostics. P10 closes integrated verification and validation with auditable exact-SHA evidence.

## Implemented Physics and Study Interfaces

- Compressible perfect-gas flow
- Variable-area duct
- Prescribed Darcy-factor wall-friction momentum source
- Prescribed wall-heat-flux energy source
- Prescribed local and distributed fuel mass/momentum/energy injection
- Mapping from prescribed axial fuel mass-flow distribution `d(mdot_f)/dx` to a local volumetric source
- Prescribed burned-fuel/LHV combustion heat-release path
- Direct prescribed line heat-release input `Qdot'(x) [W/m]`, conservatively mapped to the energy equation as `Qdot'/A`
- Source-backed P11 study ledgers, case gates, readiness artifacts, and reproducible case outputs

The direct heat-release path and the burned-fuel/LHV path are mutually exclusive so the same energy cannot be counted twice.

## Implemented Numerical Methods

- Rusanov and raw Steger-Warming flux-vector-splitting interface fluxes
- First-order piecewise-constant finite volumes
- Third-order SSP Runge-Kutta time integration
- CFL-based time stepping
- Transient and steady quasi-one-dimensional solve paths
- Automated conservation, convergence, sensitivity, robustness, and regression tests

## Current Scientific Boundary

The code now supports physically scaled non-reactive studies and prescribed heated studies, but a direct heat-addition interface is not by itself a validated combustion model. The current model does not resolve transverse-jet mixing, cavity recirculation, finite-rate chemistry, ignition, species transport, or multidimensional shock/boundary-layer separation.

The next accepted milestone is a **source-consistent formal P11.2B heated validation case**. Only after that evidence chain is closed should P11.3 define the LBW/YBW criterion and build a regime/transition map.

## Development Philosophy

Each physical model and scientific claim is introduced independently, source-traced where applicable, and validated before stronger claims are allowed. See `docs/` for the frozen scope, mathematical model, numerical method, V&V record, staged roadmap, and P11 study plan.
