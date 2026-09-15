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
| P11 | In Progress | Physical parametric studies and mode-transition work | Source-traceable study cases, heated validation, then LBW/YBW map | Evidence-gated case promotion and reproducible outputs |

## P10 Breakdown

- P10.1 V&V Foundation + Conservation — Complete (accepted SHA `32eb50cd687da6e23a4cb2269bc31120fbff2b3e`, Test run `34638173666`)
- P10.2 Grid / Spatial Convergence — Complete (accepted SHA `ce27e3fd841362432791f45f3c8ad53a3002ecf4`, dedicated run `34686588293`, artifact `10295429740`)
- P10.3 CFL / Temporal / Scheme Sensitivity — Complete (accepted SHA `bc9963f66cb64f043254b34532863b97432cc287`, Test run `34700186067`, dedicated run `34700559898`, artifact `10299894650`)
- P10.4 Integrated Evidence / Closure — Complete (accepted SHA `cac804a30f325ddf1875ab5188353cdbbf9e5de6`, dedicated run `34833172796`, artifact `10343052217`)

## P11 Breakdown

- P11.1 Parametric Study Foundation + controlled similarity pilot — **Implemented and verified**; framework-only claim.
- P11.2A Source-backed public surrogate cold-flow baseline + isolator-length diagnostic — **Implemented and formally verified** at accepted code SHA `9032d5e8304ac6022ba7c4f185b170c6ba9cddd2`; standard Test run `34880624298`, dedicated run `34880624357`, artifact `10362683519`.
- P11.2B Prescribed heat-release interface + source-backed closure/validation preparation — **Implemented and regression-verified; formal heated case remains evidence-gated.**
- P11.3 Authoritative LBW/YBW criterion + regime/transition map — Planned after a defensible P11.2B heated case is accepted.
- P11.4 Integrated LBW/YBW comparison, robustness, interpretation, and study closure — Planned.

### P11.2B current gate

Already resolved for the preferred Jin–Liu model-B chain:

- source-to-solver axial coordinate mapping and model-B axial geometry;
- study-layer radial area law using the source-corroborated `2 deg` wall-divergence interpretation;
- direct `Qdot'(x) [W/m]` solver interface and normalized heat-release closures;
- Jin wall-friction coefficient convention mapping to repository Darcy factor (`f_D = 4 Cf`).

Formal heated-case promotion remains blocked until the same physical case provides:

1. a resolved Jin/Liu validation-condition identity;
2. the exact station-3 / combustor-inlet boundary state;
3. the numerical wall-friction coefficient used by the validation case, or direct evidence that it was neglected;
4. a source-backed absolute heat-release profile, or a complete normalized heat-release shape plus matching absolute energy scale.

The authoritative machine-readable state is `artifacts/p11_2b/p11_2b_readiness.json`.

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
