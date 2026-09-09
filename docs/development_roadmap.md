# Development Roadmap

| Stage | Status | Goal | Main deliverable | Acceptance idea |
| --- | --- | --- | --- | --- |
| P0 | Complete | Scope definition | Frozen scope and model plan | Architectural review |
| P1 | Complete | Project skeleton | Package, documentation, test setup | Import and pytest smoke test |
| P2 | Complete | Thermodynamics & state conversion | Tested gas and state utilities | Unit and physical checks |
| P3 | Complete | Baseline 1D Euler solver | Source-free solver | Conservation checks |
| P4 | Complete | Variable area | Quasi-1D geometry support | Controlled-area case |
| P5 | Complete | Steger-Warming + RK3 + CFL | Validated Rusanov / Steger-Warming quasi-1D schemes | Controlled convergence and robustness cases |
| P6 | Planned | Friction & heat transfer | Separate source models | Per-model validation |
| P7 | Planned | Fuel injection | Injection source model | Mass/momentum/energy checks |
| P8 | Planned | Combustion | Heat-release model | Controlled combustion validation |
| P9 | Planned | Boundary/stability improvements | Robust boundary handling | Edge-case test suite |
| P10 | Planned | Verification & validation | Verified cases and comparisons | Conservation, benchmark, and grid checks |
| P11 | Planned | Parametric studies | Reproducible study workflow | Repeatable case outputs |

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
