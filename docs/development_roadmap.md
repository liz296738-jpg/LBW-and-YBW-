# Development Roadmap

| Stage | Goal | Main deliverable | Acceptance idea |
| --- | --- | --- | --- |
| P0 | Scope definition | Frozen scope and model plan | Architectural review |
| P1 | Project skeleton | Package, documentation, test setup | Import and pytest smoke test |
| P2 | Thermodynamics & state conversion | Tested gas and state utilities | Unit and physical checks |
| P3 | Baseline 1D Euler solver | Source-free solver | Conservation checks |
| P4 | Variable area | Quasi-1D geometry support | Controlled-area case |
| P5 | Steger-Warming + RK3 + CFL | Planned formal numerical scheme | Stability and convergence checks |
| P6 | Friction & heat transfer | Separate source models | Per-model validation |
| P7 | Fuel injection | Injection source model | Mass/momentum/energy checks |
| P8 | Combustion | Heat-release model | Controlled combustion validation |
| P9 | Boundary/stability improvements | Robust boundary handling | Edge-case test suite |
| P10 | Verification & validation | Verified cases and comparisons | Conservation, benchmark, and grid checks |
| P11 | Parametric studies | Reproducible study workflow | Repeatable case outputs |

