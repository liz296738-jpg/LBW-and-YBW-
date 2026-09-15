# Scramjet 1D CFD

## Project Goal

Develop a quasi-one-dimensional, compressible-flow CFD solver and reproducible study workflow for scramjet and dual-mode ramjet combustors.

## Current Status

Current stage: **P11.3 definition-first mode-transition work.** P10 overall verification and validation is complete. P11.1 study infrastructure is implemented and verified. P11.2A has a formally verified, literature-backed, physical-scale non-reactive public-surrogate baseline. P11.2B now has an accepted public heated **reduced-order computational-reference benchmark** based on the NASA Burrows–Kurkov case.

The accepted NASA P11.2B chain uses official public NASA data, checksum-tracked Wind-US reference assets, source-backed duct geometry, a vitiated-gas effective thermodynamic reduction, conservative moment-matched reduced-domain inlet/exit states, and signed reference-derived energy/momentum closures. A 40/80/160/320-cell study converges and the finest-grid exit Mach, pressure, and temperature remain within about 1% of the frozen conservative reference target. The acceptance is intentionally scoped: it is a reduced-order solver/reduction consistency benchmark, **not** finite-rate chemistry validation, species validation, or an unsupported scalar reduction of the nonuniform experimental exit profiles.

The Jin–Liu model-B route remains preserved as an advanced scramjet-specific heated-validation candidate. Its exact reproduction remains evidence-blocked rather than filled with guessed values.

P11.3 has now frozen a peer-reviewed general dual-mode taxonomy and transition-physics evidence chain. The cited literature shows that precombustion shock/isolator state and the combustor-entry flow state are central mode observables; a minimum Mach or downstream Mach value by itself is not a universal mode criterion. The literal project labels `LBW` and `YBW` remain unresolved until an explicit teacher/project source defines them, so no classifier or regime map is yet promoted.

## Solver Foundation

P3 is complete: ideal-gas thermodynamics, primitive/conservative conversion, Euler physical flux, Rusanov numerical flux, finite-volume spatial residual, SSP-RK3, transmissive boundaries, CFL time stepping, a transient solver loop, a Sod-type shock-tube smoke test, automated tests, and GitHub Actions CI form the constant-area baseline solver.

P4 adds variable-area quasi-one-dimensional geometry and validates inviscid, adiabatic, constant-gamma area physics. P5 adds raw Steger-Warming flux-vector splitting alongside Rusanov and validates smooth-flow convergence, dissipation behaviour, shock robustness, and near-sonic finite-state behaviour.

P6 adds prescribed Darcy wall friction and wall heat flux. P7 adds prescribed local and distributed fuel mass/momentum/energy injection. P8 adds prescribed distributed combustion heat release. P9 adds physical inlet/outlet boundaries and steady convergence/robustness diagnostics. P10 closes integrated verification and validation with auditable exact-SHA evidence.

## Implemented Physics and Study Interfaces

- Compressible calorically-perfect-gas flow
- Variable-area duct
- Prescribed Darcy-factor wall-friction momentum source
- Prescribed wall-heat-flux energy source
- Prescribed local and distributed fuel mass/momentum/energy injection
- Mapping from prescribed axial fuel mass-flow distribution `d(mdot_f)/dx` to a local volumetric source
- Prescribed burned-fuel/LHV combustion heat-release path
- Direct prescribed nonnegative line heat-release input `Qdot'(x) [W/m]`, conservatively mapped as `Qdot'/A`
- Separate signed net-energy and signed net-axial-momentum extensions for explicitly labelled reduced-order reference-derived studies
- Source-backed P11 evidence ledgers, case gates, readiness artifacts, public-data acquisition workflows, and reproducible study outputs

The direct combustion heat-release path and burned-fuel/LHV path are mutually exclusive. The signed reduced-order source extensions are kept semantically separate from chemical heat release and from Darcy wall friction.

## Implemented Numerical Methods

- Rusanov and raw Steger-Warming flux-vector-splitting interface fluxes
- First-order piecewise-constant finite volumes
- Third-order SSP Runge-Kutta time integration
- CFL-based time stepping
- Transient and steady quasi-one-dimensional solve paths
- Automated conservation, convergence, grid-refinement, sensitivity, robustness, and regression tests

## P11 Evidence State

### P11.2A

Accepted source-backed public cold-flow surrogate and isolator-length diagnostic.

### P11.2B

Accepted scoped benchmark:

`cases/studies/data/p11_2b_nasa_bk_benchmark_acceptance.json`

Status:

`FORMAL_REDUCED_ORDER_REFERENCE_BENCHMARK_ACCEPTED`

with:

- `benchmark_ready = true`
- `formal_experimental_validation_ready = false`

Detailed report:

`docs/p11_2b_nasa_bk_benchmark_acceptance.md`

### P11.3

Definition evidence:

`cases/studies/data/p11_3_mode_definition_source.json`

Readiness:

- general mode taxonomy: ready
- transition-mechanism evidence: ready
- project-specific `LBW` / `YBW` mapping: not ready
- solver-observable mapping: not ready
- classifier: not ready
- regime map: not ready

No published facility-specific pressure ratio or equivalence-ratio transition value is silently promoted to a universal project threshold.

## Current Scientific Boundary

The solver supports physically scaled non-reactive studies, prescribed heated studies, and a rigorously scoped public reduced-order heated benchmark. It does not resolve transverse-jet mixing, cavity recirculation, finite-rate chemistry, ignition, species transport, or multidimensional shock/boundary-layer separation.

The current production study model also does not contain the dedicated strength-adaptable isolator/precombustion-shock model used by some published quasi-one-dimensional multimode methods. Therefore a future P11.3 classifier must first map available solver/domain observables to a source-backed mode definition; it may not infer shock-train state from an unrelated scalar diagnostic.

## Development Philosophy

Each physical model and scientific claim is introduced independently, source-traced where applicable, and validated before stronger claims are allowed. Missing evidence remains an explicit blocker rather than being replaced by guessed inputs or silent physics changes. See `docs/` for the frozen scope, mathematical model, numerical method, V&V record, roadmap, and P11 evidence reports.
