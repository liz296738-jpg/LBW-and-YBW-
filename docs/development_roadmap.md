# Development Roadmap

| Stage | Status | Goal | Main deliverable | Acceptance idea |
| --- | --- | --- | --- | --- |
| P0 | Complete | Scope definition | Frozen scope and model plan | Architectural review |
| P1 | Complete | Project skeleton | Package, documentation, test setup | Import and pytest smoke test |
| P2 | Complete | Thermodynamics & state conversion | Tested constant-gas state utilities | Unit and physical checks |
| P3 | Complete | Baseline 1D Euler solver | Source-free solver | Conservation checks |
| P4 | Complete | Variable area | Quasi-1D geometry support | Controlled-area case |
| P5 | Complete | Steger-Warming + RK3 + CFL | Validated Rusanov / Steger-Warming quasi-1D schemes | Controlled convergence and robustness cases |
| P6 | Complete | Generic friction & heat transfer | Separate prescribed source models | Per-model validation |
| P7 | Complete | Generic fuel injection | Prescribed local and distributed injection source | Formal prescribed-source model validation |
| P8 | Complete | Generic combustion surrogate | Prescribed combustion heat-release capability | Controlled validation complete |
| P9 | Complete | Boundary/stability improvements | Physical boundaries and steady convergence diagnostics | Edge-case and robustness test suite |
| P10 | Complete | Verification & validation | Accepted integrated evidence closure | Auditable evidence, claims, limitations, and exact-SHA gates |
| P11.1-P11.2 | Complete / accepted supporting work | Reproducible studies and public reduced-order benchmarks | Parametric framework, cold surrogate, heated NASA benchmark | Evidence-gated reproducible outputs |
| P11.3 | **In Progress** | Close teacher-reference “second scheme” | Thermochemical + mixing/combustion + teacher numerical compatibility | Equation-by-equation traceability and regression tests |
| P11.4 | Planned | Teacher-reference integrated reproduction / parametric study | Reproducible reference cases and sensitivity outputs | Source-backed agreement and grid/convergence checks |
| P12 | Planned | Combustion-mode-transition application | Mode-transition study using teacher/Cao definitions | Only after P11.3-P11.4 are accepted |

## Naming Correction

`LBW` and `YBW` are **people/project identifiers**, not physical combustion modes. No roadmap stage may define an `LBW/YBW classifier`, `LBW/YBW regime map`, or any other physical interpretation from those names.

The previous P11.3 wording that treated those labels as modes was incorrect and is superseded by this roadmap.

## Teacher-Reference Authority

The primary target is the model family documented in the teacher-provided material:

- photographed Chapter 11, **“双模态冲压燃烧室一维数值模拟”**;
- 曹瑞峰, **《面向控制的超燃冲压发动机一维建模研究》**;
- 曹瑞峰, **《超燃冲压发动机燃烧模态转换及其控制方法研究》**.

The teacher explicitly asked the group to learn the CFD equations and first build the one-dimensional model, describing this as a second, more accurate scheme. Public NASA/Jin/Liu work is supporting V&V, not a replacement for this target.

Detailed matrix: `docs/teacher_reference_alignment.md`.

## P11.3 Breakdown — Teacher-Reference Second Scheme

### P11.3A Numerical compatibility — In Progress

Already aligned:

- unsteady quasi-1D conservation form;
- first-order finite-volume/upwind treatment;
- Steger-Warming FVS;
- third-order TVD/SSP-RK3;
- CFL stepping;
- compatible physical/transmissive boundary infrastructure.

Closeout items:

- add Chapter 11 Eq. 11.46 maximum relative-density iteration change as a compatibility diagnostic while retaining the stronger normalized residual gate;
- preserve the teacher's inlet `p/T/u` and first-order extrapolation semantics through case adapters/configuration;
- add Eq. 11.44 near-sonic Steger-Warming smoothing only after the smoothing parameter policy is explicitly source-frozen. Do not guess `epsilon`.

### P11.3B Variable thermochemistry — Planned next

Implement an isolated, tested thermochemical layer for the teacher-reference equations around Eqs. 11.30-11.35:

- species `cp(T)` and `h(T)` polynomial evaluation;
- mixture molecular weight / gas constant from composition;
- mixture `cp`, `h`, `cv`, and `gamma` from temperature and composition;
- explicit validity ranges and coefficient provenance;
- no replacement of the constant-gas baseline until the variable-property path is independently verified.

The NASA-Burrows-Kurkov study utility already demonstrates source-backed NASA7 polynomial evaluation for a fixed-composition reduction; that code is useful scaffolding but is not yet the production variable-thermo model.

### P11.3C Mixing / combustion / composition closures — Planned

Transcribe and independently test the teacher-reference closures before solver integration:

- mixing efficiency and mixing length (Eqs. 11.19-11.20);
- stoichiometric/equivalence-ratio definitions (Eqs. 11.21-11.24);
- fuel-specific composition approximations (Eqs. 11.27-11.29);
- fuel/injection configuration metadata.

The existing prescribed injection and direct heat-release interfaces remain useful low-level interfaces and V&V controls. They are not the final closure.

### P11.3D Friction / wall heat / energy bookkeeping — Planned

Add teacher-reference empirical friction and wall-heat closures (around Eqs. 11.25-11.26) as **optional source models**, preserving the generic prescribed Darcy/heat-flux interfaces.

Energy bookkeeping is a hard gate: external wall/additional heat is not identical to chemical reaction heat. When chemical energy is represented through composition-dependent enthalpy, it must not also be silently added through the direct `Qdot'(x)` surrogate.

### P11.3E Integrated teacher model — Planned

Compose the verified pieces into one teacher-reference case only after P11.3A-D pass focused tests. Required outputs include source provenance, convergence diagnostics, mass/momentum/energy audits, and clearly separated model assumptions.

## P11.4 — Reference Reproduction and Parameter Study

Once P11.3 is complete:

1. reproduce a source-defined geometry and operating condition from the teacher/Cao references;
2. verify grid and convergence behavior;
3. compare pressure, temperature, velocity/Mach, and any source-available quantities;
4. perform source-defined parameter sweeps only after the baseline case is accepted.

## P12 — Mode-Transition Application

Combustion-mode transition remains scientifically relevant because it appears in the Cao reference set. It is **not** an `LBW/YBW` classification task.

A P12 transition criterion must be taken from the teacher/Cao model definition and must be observable within the completed one-dimensional model. This stage is deliberately deferred until the physical closures needed by the teacher's second scheme are available.

## Supporting P11.2 Work

P11.2A remains an accepted physical-scale public cold-flow surrogate. P11.2B remains an accepted scoped NASA Burrows-Kurkov reduced-order computational-reference benchmark. The Jin-Liu exact-reproduction chain remains useful evidence but has known source gaps.

These assets are retained because they verify solver behavior and evidence discipline; they do not change the teacher-reference model priority.

## Historical Completed Stages

### P10

- P10.1 V&V Foundation + Conservation — Complete.
- P10.2 Grid / Spatial Convergence — Complete.
- P10.3 CFL / Temporal / Scheme Sensitivity — Complete.
- P10.4 Integrated Evidence / Closure — Complete.

### P9

- P9.1 Physical Boundary Foundation — Complete.
- P9.2 Subsonic Outlet Pressure BC — Complete.
- P9.3 Subsonic Inlet / Characteristic BC — Complete.
- P9.4 Convergence / Robustness — Complete.

### P3-P8

The Euler foundation, variable-area formulation, Steger-Warming/RK3/CFL path, generic wall sources, prescribed fuel injection, and prescribed heat-release capabilities remain accepted reusable infrastructure.
