# Development Roadmap

| Stage | Status | Goal | Main deliverable | Acceptance idea |
| --- | --- | --- | --- |
| P0 | Complete | Scope definition | Frozen scope and model plan | Architectural review |
| P1 | Complete | Project skeleton | Package, documentation, test setup | Import and pytest smoke test |
| P2 | Complete | Thermodynamics & state conversion | Tested gas and state utilities | Unit and physical checks |
| P3 | In Progress | Baseline 1D Euler solver | Source-free solver | Conservation checks |
| P4 | Planned | Variable area | Quasi-1D geometry support | Controlled-area case |
| P5 | Planned | Steger-Warming + RK3 + CFL | Planned formal numerical scheme | Stability and convergence checks |
| P6 | Planned | Friction & heat transfer | Separate source models | Per-model validation |
| P7 | Planned | Fuel injection | Injection source model | Mass/momentum/energy checks |
| P8 | Planned | Combustion | Heat-release model | Controlled combustion validation |
| P9 | Planned | Boundary/stability improvements | Robust boundary handling | Edge-case test suite |
| P10 | Planned | Verification & validation | Verified cases and comparisons | Conservation, benchmark, and grid checks |
| P11 | Planned | Parametric studies | Reproducible study workflow | Repeatable case outputs |

## P3 Breakdown

- P3.1 Euler physical flux — Complete
- P3.2 Numerical interface flux — Planned
- P3.3 Spatial residual — Planned
- P3.4 Time integration — Planned
- P3.5 Baseline solver — Planned
