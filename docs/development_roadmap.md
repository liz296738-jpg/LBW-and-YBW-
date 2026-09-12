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
| P10 | In Progress | Verification & validation | P10.3 CFL, RK3 temporal, and scheme sensitivity | Conservation, convergence, and sensitivity checks |
| P11 | Planned | Parametric studies | Reproducible study workflow | Repeatable case outputs |

## P10 Breakdown

- P10.1 V&V Foundation + Conservation — Complete (accepted SHA `32eb50cd687da6e23a4cb2269bc31120fbff2b3e`, Test run `34638173666`)
- P10.2 Grid / Spatial Convergence — Complete (accepted SHA `ce27e3fd841362432791f45f3c8ad53a3002ecf4`, dedicated run `34686588293`, artifact `10295429740`)
- P10.3 CFL / Temporal / Scheme Sensitivity — In progress; preflight and dedicated formal workflow implemented
- P10.4 Integrated Evidence / Closure — Not started

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

- P4.1 Area geometry representation - Complete
- P4.2 Quasi-1D area-weighted residual + geometric source - Complete
- P4.3 Variable-area solver integration - Complete
- P4.4 Controlled-area validation - Complete

## P5 Breakdown

- P5.1 Steger-Warming single-state flux splitting - Complete
- P5.2 Steger-Warming interface numerical flux - Complete
- P5.3 Quasi-1D solver integration / scheme selection - Complete
- P5.4 Steger-Warming validation and comparison - Complete

## P6 Breakdown

- P6.1 Wall Friction Source Model - Complete
- P6.2 Wall Heat-Transfer Source Model - Complete
- P6.3 Source Composition / Solver Integration - Complete
- P6.4 Friction / Heat Validation - Complete (normalized residual classification and hard gates)

## P7 Breakdown

- P7.1 Prescribed Local Fuel Injection Source - Complete
- P7.2 Quasi-1D Injection Distribution / Composition - Complete
- P7.3 Solver Integration - Complete
- P7.4 Fuel-Injection Validation - Complete (exact source, conservation, scaling, CFL sensitivity, and controlled transient)

## P8 Breakdown

- P8.1 Prescribed Local Combustion Heat-Release Source - Complete
- P8.2 Distributed / Fuel-Linked Heat-Release Closure - Complete
- P8.3 Solver Integration - Complete
- P8.4 Combustion Validation - Complete
