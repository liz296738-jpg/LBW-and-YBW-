# Development Roadmap

| Stage | Status | Goal | Main deliverable | Acceptance idea |
| --- | --- | --- | --- | --- |
| P0 | Complete | Scope definition | Frozen scope and model plan | Architectural review |
| P1 | Complete | Project skeleton | Package, documentation, test setup | Import and pytest smoke test |
| P2 | Complete | Thermodynamics & state conversion | Tested constant-gas state utilities | Unit and physical checks |
| P3 | Complete | Baseline 1D Euler solver | Source-free solver | Conservation checks |
| P4 | Complete | Variable area | Quasi-1D geometry support | Controlled-area case |
| P5 | Complete | Baseline schemes | Rusanov / calorically-perfect Steger-Warming + RK3 + CFL | Controlled convergence and robustness cases |
| P6 | Complete | Generic friction & heat transfer | Separate prescribed source models | Per-model validation |
| P7 | Complete | Generic fuel injection | Prescribed local and distributed injection source | Formal prescribed-source model validation |
| P8 | Complete | Generic combustion surrogate | Prescribed combustion heat-release capability | Controlled validation complete |
| P9 | Complete | Boundary/stability improvements | Physical boundaries and steady convergence diagnostics | Edge-case and robustness test suite |
| P10 | Complete | Verification & validation | Accepted integrated evidence closure | Auditable evidence, claims, limitations, and exact-SHA gates |
| P11.1-P11.2 | Complete / supporting | Reproducible public studies and reduced-order benchmarks | Parametric framework, cold surrogate, heated NASA benchmark | Evidence-gated reproducible outputs |
| P11.3 | **Core path complete; two source gaps explicitly gated** | Close teacher-reference “second scheme” building blocks | Variable thermo + teacher closures + sources + boundaries + integrated Rusanov march | Equation-by-equation regression and source audit |
| P11.4 | **In Progress** | Integrated teacher-path case and reference reproduction | Steady case, convergence/grid study, source-defined reproduction where possible | Source-backed inputs, convergence, conservation and grid checks |
| P12 | Planned | Combustion-mode-transition application | Mode-transition study using teacher/Cao definitions | Only after P11.4 baseline acceptance |

## Naming Correction

`LBW` and `YBW` are **people/project identifiers**, not physical combustion modes. No roadmap stage may define an `LBW/YBW classifier`, `LBW/YBW regime map`, or infer any physical meaning from those labels.

## Teacher-Reference Authority

The primary target is the model family documented in the teacher-provided material:

- photographed Chapter 11, **“双模态冲压燃烧室一维数值模拟”**;
- 曹瑞峰, **《面向控制的超燃冲压发动机一维建模研究》**;
- 曹瑞峰, **《超燃冲压发动机燃烧模态转换及其控制方法研究》**.

The teacher asked the group to learn the CFD equations and first build the one-dimensional model as the more accurate second scheme. Public NASA/Jin/Liu work remains supporting V&V, not a replacement for this target.

Detailed matrix: `docs/teacher_reference_alignment.md`.

## P11.3 — Teacher-Reference Second-Scheme Building Blocks

### A. Numerical and boundary compatibility — READY on the defensible integrated path

Implemented and verified:

- unsteady quasi-one-dimensional conservative finite-volume formulation;
- first-order interface treatment;
- SSP/TVD-RK3;
- CFL stepping;
- teacher static `p/T/u` supersonic inlet adapter;
- first-order/zero-gradient outlet semantics;
- teacher Eq. (11.46) maximum relative-density diagnostic;
- boundary-complete variable-composition **Rusanov** compatibility solver.

Teacher Eqs. (11.42)-(11.44) Steger-Warming were also transcribed and independently audited. The literal formula is valid in the calorically-perfect constant-property limit, but under the project's source-backed variable `cp(T,Y)` and absolute species energy it does not reconstruct the physical Euler energy flux. The teacher/Cao sources examined so far do not supply a variable-thermochemistry correction. Therefore:

- literal teacher Steger-Warming remains an isolated source-transcription/audit path;
- no guessed energy-reference correction is introduced;
- no numerical Eq. (11.44) `epsilon` is guessed;
- the integrated production-compatibility path remains Rusanov unless an authoritative missing convention is recovered.

Source audit: `docs/teacher_steger_warming_source_audit.md`.

### B. Variable thermochemistry — READY for H2/C2H4 path

Implemented and regression-tested:

- source-backed piecewise species thermochemistry for H2, O2, N2, Ar, H2O, C2H4 and CO2;
- `cp(T)`, absolute `h(T)`, internal energy, mixture molecular weight, `R(Y)`, `gamma(T,Y)`;
- bounded `e -> T` recovery;
- conservative/primitive state conversion;
- per-cell variable-composition state recovery;
- source-valid temperature-range guards and no silent mass-fraction renormalization.

`C10H22` remains source-gated because a compatible traceable thermochemistry dataset has not been frozen. That does not block the H2/C2H4 teacher path.

### C. Mixing / combustion / composition closures — READY for lean H2/C2H4

Implemented from the photographed Chapter 11 source:

- Eq. (11.18) combustion efficiency identity;
- Eq. (11.19) parallel / normal / strut raw mixing-efficiency correlations;
- Eq. (11.20) mixing length;
- Eqs. (11.21)-(11.24) stoichiometry and equivalence ratio;
- Eqs. (11.27)-(11.29) lean fuel-specific composition relations;
- explicit project adapter `eta=min(eta_m_raw,1)` separated from the raw correlation;
- spatial algebraic `phi -> L_m -> eta_m -> eta -> Y_i` closure held fixed for one prescribed operating condition during pseudo-time.

The transcribed teacher model is treated as a three-flow-equation model with algebraic composition closure; no unsourced species-transport PDE system has been added.

### D. Source vector / friction / energy bookkeeping — READY with one wall-heat blocker

Implemented:

- Eq. (11.38) localized fuel mass source;
- injected axial momentum source;
- injected total-enthalpy source using the same absolute species-enthalpy convention;
- teacher Eq. (11.25) wall friction and exact `f_D=4f` mapping;
- single-injector finite-volume mapping that leaves upstream cells air-only and prevents fuel double counting;
- explicit dimensional wall-specific-heat-gain-gradient input channel.

Hard scientific boundaries:

- geometric `p dA/dx` remains only in the quasi-1D Euler operator and is not duplicated;
- chemical energy carried by composition-dependent absolute species energy is not also re-added through an independent chemical `Qdot`;
- the photographed Eq. (11.26) heat correlation has **not** been converted into dimensional `d(delta q)/dx` because the required dimensional mapping has not been uniquely frozen from source evidence.

A formal integrated case may therefore set the explicit wall-heat channel to zero as a declared model-scope choice, but may not claim this reproduces Eq. (11.26).

### E. Integrated compatibility solver — READY; steady closeout in P11.4

The repository now contains a source-enabled, variable-composition SSP-RK3 solver with teacher inlet/outlet semantics and the Eq. (11.38) source vector. The accepted integrated numerical flux is Rusanov for the reasons above.

P11.4 now adds the teacher Eq. (11.45)/(11.46) steady pseudo-time closeout and turns this infrastructure into reproducible cases rather than continuing to add isolated modules.

## P11.4 — Integrated Case, Reference Reproduction, and Parameter Study

### P11.4A Steady closeout — IN PROGRESS

Current work adds:

- Eq. (11.46) variable-thermochemistry density-change stopping criterion using conservative density directly;
- an independent normalized semi-discrete residual for robustness reporting;
- Eq. (11.45)-compatible spectral timestep using explicit `NumericalConfig.cfl`;
- optional explicit `dt0` cap, with **no guessed default** because the photographed source does not provide a numerical value.

For teacher compatibility, production cases should use `cfl=0.5` unless a different case-specific choice is explicitly documented.

### P11.4B Cao doctoral Case 2 evidence — SOURCE INLET FROZEN, FULL REPRODUCTION BLOCKED

Machine-readable source record:

`cases/studies/data/teacher_cao_case2_source.json`

Frozen Table 2-2 inputs:

- fuel `H2`;
- `Ma2=2.12`;
- `rho2=0.28 kg/m^3`;
- `p2=46.7 kPa`;
- `T2=521 K`;
- `u2=977 m/s`;
- reported `k=1.33`;
- `phi=0.2`;
- inlet mass fractions `YN2=0.64`, `YO2=0.22`, `YH2O=0.13`, `YAr=0.01`;
- wall temperature `Tw=900 K`;
- reported comparison grid spacings `0.0001 m` and `0.001 m`.

The source explicitly states that Case 2 prescribes species-composition changes instead of solving a selected finite-rate chemical mechanism, while variable heat capacity and multicomponent properties are solved during the calculation.

Formal Case 2 reproduction remains blocked until the exact source geometry `A(x)` and prescribed `Yi(x)` profiles are frozen. The Cao Case 2 vitiated inlet must also not be silently conflated with the photographed Chapter 11 dry-air single-injector composition basis.

### P11.4C Project-defined integrated smoke case — NEXT

Before claiming source reproduction, run a clearly labeled `PROJECT_DEFINED_INTEGRATED_SMOKE_CASE` through the complete accepted Chapter 11 H2/C2H4 path. Every non-source input must be marked as a project choice, and the wall-heat channel remains explicitly zero until Eq. (11.26) dimensional mapping is recovered.

Acceptance sequence:

1. converge with teacher Eq. (11.46) and report the independent normalized residual;
2. verify positive/source-valid thermodynamic states;
3. audit fuel mass, momentum and energy/source bookkeeping;
4. run at least three grid levels;
5. freeze pressure, temperature, velocity/Mach and composition outputs;
6. only then begin parameter sweeps.

### P11.4D Source-defined parameter study — AFTER BASELINE ACCEPTANCE

Use equivalence ratio, injection/mixing parameters, inlet condition or other source-defined controls only after one baseline integrated case passes convergence and grid checks.

## P12 — Mode-Transition Application

Combustion-mode transition is scientifically relevant because it appears in the Cao reference set. It is **not** an `LBW/YBW` classification task.

The Cao doctoral thesis includes a precombustion shock-train model and transonic mode-solution workflow. P12 may use those definitions only after P11.4 establishes a reliable baseline integrated model and only after the required source geometry/observables are frozen.

## Supporting P11.2 Work

P11.2A remains an accepted physical-scale public cold-flow surrogate. P11.2B remains an accepted scoped NASA Burrows-Kurkov reduced-order computational-reference benchmark. The Jin-Liu exact-reproduction chain remains useful evidence but has known source gaps.

These assets verify solver behavior and evidence discipline; they do not change the teacher-reference model priority.

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

The Euler foundation, variable-area formulation, baseline Steger-Warming/RK3/CFL path, generic wall sources, prescribed fuel injection, and prescribed heat-release capabilities remain accepted reusable infrastructure.
