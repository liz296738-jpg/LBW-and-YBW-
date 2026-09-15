# Development Roadmap

| Stage | Status | Goal | Main deliverable | Acceptance idea |
| --- | --- | --- | --- | --- |
| P0 | Complete | Scope definition | Frozen scope and model plan | Architectural review |
| P1 | Complete | Project skeleton | Package, documentation, test setup | Import and pytest smoke test |
| P2 | Complete | Thermodynamics & state conversion | Tested gas and state utilities | Unit and physical checks |
| P3 | Complete | Baseline 1D Euler solver | Source-free solver | Conservation checks |
| P4 | Complete | Variable area | Quasi-1D geometry support | Controlled-area case |
| P5 | Complete | Steger-Warming + RK3 + CFL | Validated Rusanov / Steger-Warming quasi-1D schemes | Controlled convergence and robustness cases |
| P6 | Complete | Friction & heat transfer | Separate source models | Per-model validation |
| P7 | Complete | Fuel injection | Prescribed local and distributed injection source | Formal prescribed-source model validation |
| P8 | Complete | Combustion | Validated prescribed combustion heat-release capability | P8.1-P8.4 controlled validation complete |
| P9 | Complete | Boundary/stability improvements | Physical boundaries and steady convergence diagnostics | Edge-case and robustness test suite |
| P10 | Complete | Verification & validation | Accepted integrated evidence closure | Auditable evidence, claims, limitations, and exact-SHA gates |
| P11 | In Progress | Physical parametric studies and mode-transition work | Source-traceable studies, heated benchmark, definition-gated mode map | Evidence-gated promotion and reproducible outputs |

## P10 Breakdown

- P10.1 V&V Foundation + Conservation — Complete (accepted SHA `32eb50cd687da6e23a4cb2269bc31120fbff2b3e`, Test run `34638173666`).
- P10.2 Grid / Spatial Convergence — Complete (accepted SHA `ce27e3fd841362432791f45f3c8ad53a3002ecf4`, dedicated run `34686588293`, artifact `10295429740`).
- P10.3 CFL / Temporal / Scheme Sensitivity — Complete (accepted SHA `bc9963f66cb64f043254b34532863b97432cc287`, Test run `34700186067`, dedicated run `34700559898`, artifact `10299894650`).
- P10.4 Integrated Evidence / Closure — Complete (accepted SHA `cac804a30f325ddf1875ab5188353cdbbf9e5de6`, dedicated run `34833172796`, artifact `10343052217`).

## P11 Breakdown

- P11.1 Parametric Study Foundation + controlled similarity pilot — **Implemented and verified**; framework-only claim.
- P11.2A Source-backed public surrogate cold-flow baseline + isolator-length diagnostic — **Implemented and formally verified** at accepted code SHA `9032d5e8304ac6022ba7c4f185b170c6ba9cddd2`; standard Test run `34880624298`, dedicated run `34880624357`, artifact `10362683519`.
- P11.2B Public heated reduced-order benchmark — **FORMALLY ACCEPTED WITH SCOPED CLAIMS.** NASA Burrows–Kurkov is the accepted public computational-reference benchmark; the Jin–Liu exact-reproduction chain remains preserved but evidence-blocked.
- P11.3 Authoritative mode definition + project-label/observable mapping + regime/transition map — **IN PROGRESS, DEFINITION-FIRST.** General dual-mode taxonomy is frozen; `LBW`/`YBW` project semantics and solver-observable mapping remain gated before classifier implementation.
- P11.4 Integrated LBW/YBW comparison, robustness, interpretation, and study closure — Planned after P11.3 classification semantics are source-backed and verified.

## P11.2B Accepted NASA Burrows–Kurkov Benchmark

P11.2B is no longer blocked on the first defensible heated benchmark. The accepted route is documented in:

- `cases/studies/data/p11_2b_nasa_bk_benchmark_acceptance.json`
- `docs/p11_2b_nasa_bk_benchmark_acceptance.md`
- `docs/p11_2b_nasa_bk_validation_candidate.md`

The accepted chain includes:

- official public NASA experiment/reference assets with checksum-tracked acquisition;
- normalized public exit-plane experimental profiles retained as independent context;
- source-backed quasi-one-dimensional duct geometry;
- explicit vitiated-gas calorically-perfect thermodynamic reduction;
- legacy Wind-US Common File extraction with repository-owned tooling;
- conservative moment-matched reduced-domain inlet and exit targets;
- signed NASA-reference-derived line-energy and axial-momentum closures kept semantically separate from chemical heat release and wall friction;
- converged heated candidate and lower-gamma sensitivity;
- 40/80/160/320-cell convergence study.

At 320 cells the reference-gamma result differs from the conservative exit target by approximately `-0.567%` in Mach, `+0.827%` in static pressure, and `+0.512%` in static temperature, while 160-to-320 refinement changes are of order `1e-5` relative.

Acceptance scope:

`FORMAL_REDUCED_ORDER_REFERENCE_BENCHMARK_ACCEPTED`

with:

- `benchmark_ready = true`
- `formal_experimental_validation_ready = false`

The second flag remains false deliberately: the public experimental outputs are strongly nonuniform transverse probe profiles, and the project does not invent an unsupported one-dimensional experimental bulk scalar. This benchmark does not validate finite-rate chemistry, species transport, an experimentally measured axial chemical heat-release profile, or LBW/YBW classification.

### Jin–Liu status

The Jin–Liu model-B chain remains useful advanced evidence, but its exact formal reproduction is still blocked by the known same-condition source gaps: condition identity, exact station-3 state, numerical `Cf`, and complete heat-release shape/absolute scale. These gaps do not reopen the accepted NASA reduced-order benchmark.

## P11.3 Current Gate

Machine-readable evidence:

`cases/studies/data/p11_3_mode_definition_source.json`

Readiness implementation:

`cases/studies/p11_3_mode_definition_readiness.py`

Current state:

- general dual-mode taxonomy — **READY**;
- transition-mechanism evidence — **READY**;
- condition-specific threshold evidence — **READY**;
- project-specific `LBW` / `YBW` semantics — **NOT YET RESOLVED**;
- solver/domain observable mapping to the literature definitions — **NOT YET RESOLVED**;
- universal scalar threshold — **NOT AVAILABLE / MUST NOT BE INVENTED**;
- classifier — **BLOCKED**;
- regime map — **BLOCKED**.

### Frozen P11.3 scientific rules

1. Mode may not be classified solely from the minimum Mach anywhere in the domain.
2. Published dual-mode definitions place strong weight on the precombustion shock/isolator state and the flow state near the combustor entrance.
3. Downstream reacceleration to supersonic speed may occur after ram-mode establishment, so downstream `Mach > 1` is not by itself a scram-mode proof.
4. Wall-pressure and equivalence-ratio transition values reported for one facility remain condition-specific unless transferability is established.
5. Hysteresis and oscillatory transition behavior justify a transition/uncertain state when observables do not support an unambiguous classification.

The current production study model does not contain Tian et al.'s dedicated strength-adaptable precombustion shock model and does not resolve multidimensional shock-train/separation physics. P11.3 must therefore map available project observables to an admissible definition before implementing any label logic.

## P9 Breakdown

- P9.1 Physical Boundary Foundation — Complete
- P9.2 Subsonic Outlet Pressure BC — Complete
- P9.3 Subsonic Inlet / Characteristic BC — Complete
- P9.4 Convergence / Robustness — Complete

## P3 Breakdown

- P3.1 Euler physical flux — Complete
- P3.2 Rusanov numerical interface flux — Complete
- P3.3 Finite-volume spatial residual — Complete
- P3.4 SSP-RK3 time integration — Complete
- P3.5 Baseline solver — Complete

## P4 Breakdown

- P4.1 Area geometry representation — Complete
- P4.2 Quasi-1D area-weighted residual + geometric source — Complete
- P4.3 Variable-area solver integration — Complete
- P4.4 Controlled-area validation — Complete

## P5 Breakdown

- P5.1 Steger-Warming single-state flux splitting — Complete
- P5.2 Steger-Warming interface numerical flux — Complete
- P5.3 Quasi-1D solver integration / scheme selection — Complete
- P5.4 Steger-Warming validation and comparison — Complete

## P6 Breakdown

- P6.1 Wall Friction Source Model — Complete
- P6.2 Wall Heat-Transfer Source Model — Complete
- P6.3 Source Composition / Solver Integration — Complete
- P6.4 Friction / Heat Validation — Complete

## P7 Breakdown

- P7.1 Prescribed Local Fuel Injection Source — Complete
- P7.2 Quasi-1D Injection Distribution / Composition — Complete
- P7.3 Solver Integration — Complete
- P7.4 Fuel-Injection Validation — Complete

## P8 Breakdown

- P8.1 Prescribed Local Combustion Heat-Release Source — Complete
- P8.2 Distributed / Fuel-Linked Heat-Release Closure — Complete
- P8.3 Solver Integration — Complete
- P8.4 Combustion Validation — Complete
