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
| P7 | Complete | Generic fuel injection | Prescribed local and distributed injection source | Formal prescribed-source validation |
| P8 | Complete | Generic combustion surrogate | Prescribed combustion heat-release capability | Controlled validation |
| P9 | Complete | Boundary/stability improvements | Physical boundaries and steady convergence diagnostics | Edge-case and robustness suite |
| P10 | Complete | Verification & validation | Accepted integrated evidence closure | Auditable evidence and exact-SHA gates |
| P11.1-P11.2 | Complete / supporting | Public studies and reduced-order benchmarks | Parametric framework, cold surrogate, NASA heated benchmark | Evidence-gated reproducible outputs |
| P11.3 | **Complete on the defensible H2/C2H4 teacher path; explicit source gaps retained** | Teacher-reference second-scheme building blocks | Variable thermo + closures + sources + boundaries + integrated Rusanov march | Equation-by-equation regression and source audit |
| P11.4 | **Baseline accepted; exact Cao Case 2 reproduction source-blocked** | Integrated teacher-path case and reproduction evidence | Project-defined H2 steady case, grid audit, conservation audit, Case 2 evidence gate | Convergence, conservation, grid trend, strict claim boundary |
| P12 | **Active / criterion source-frozen, broader claims evidence-gated** | Project-defined continuous response with scoped Cao thermal-throat criterion | Guarded response sweep plus source-faithful Eq. (3-2) criterion application | No invented tolerances; guard/nonconvergence never promoted to physical mode claims |

## Naming Correction

`LBW` and `YBW` are **people/project identifiers**, not physical combustion modes. No stage may define an `LBW/YBW classifier`, `LBW/YBW regime map`, or infer physical meaning from those labels.

## Teacher-Reference Authority

The primary target is the model family documented in the teacher-provided material:

- photographed Chapter 11, **“双模态冲压燃烧室一维数值模拟”**;
- 曹瑞峰, **《面向控制的超燃冲压发动机一维建模研究》**;
- 曹瑞峰, **《超燃冲压发动机燃烧模态转换及其控制方法研究》**.

Public NASA/Jin/Liu work remains supporting V&V, not a replacement for the teacher target.

## P11.3 — Teacher-Reference Second-Scheme Building Blocks

### Numerical / boundary path — ACCEPTED

Implemented and verified:

- unsteady quasi-one-dimensional conservative finite-volume formulation;
- first-order interface treatment;
- SSP/TVD-RK3;
- CFL stepping;
- teacher static `p/T/u` inlet adapter;
- first-order/zero-gradient outlet semantics;
- teacher Eq. 11.46 maximum relative-density diagnostic;
- boundary-complete variable-composition **Rusanov** solver.

Teacher Eqs. 11.42-11.44 Steger-Warming are retained as an audited source-transcription path. Their calorically-perfect limit is verified, but the examined teacher/Cao sources do not provide a defensible variable-thermochemistry energy correction or a numerical epsilon policy. Therefore the integrated variable-thermochemistry path remains Rusanov.

### Variable thermochemistry — ACCEPTED for H2/C2H4

Implemented:

- source-backed piecewise thermochemistry for `H2`, `O2`, `N2`, `Ar`, `H2O`, `C2H4`, `CO2`;
- `cp(T)`, absolute `h(T)`, internal energy, mixture molecular weight, `R(Y)`, `gamma(T,Y)`;
- bounded `e -> T` recovery;
- conservative/primitive conversion;
- per-cell variable-composition state recovery;
- source-valid temperature guards and no silent mass-fraction renormalization.

`C10H22` remains source-gated rather than guessed.

### Mixing / combustion / composition closures — ACCEPTED for lean H2/C2H4

Implemented from Chapter 11:

- Eq. 11.18 combustion-efficiency identity;
- Eq. 11.19 parallel / normal / strut raw mixing correlations;
- Eq. 11.20 mixing length;
- Eqs. 11.21-11.24 stoichiometry and equivalence ratio;
- lean fuel-specific composition relations for the supported H2/C2H4 path;
- explicit project adapter `eta=min(eta_m_raw,1)` separated from the raw teacher correlation;
- spatial algebraic `phi -> L_m -> eta_m -> eta -> Yi` closure held fixed during one prescribed operating-condition pseudo-time solve.

No unsourced species-transport PDE system has been added.

### Source vector / friction / energy bookkeeping — ACCEPTED with one wall-heat source gap

Implemented:

- Eq. 11.38 localized fuel mass source;
- injected axial momentum source;
- injected total-enthalpy source using the same absolute species-enthalpy convention;
- Eq. 11.25 wall friction with exact `f_D=4f` mapping;
- single-injector mapping with upstream air-only cells and no fuel double counting;
- explicit dimensional wall-specific-heat-gain-gradient input channel.

Hard boundaries:

- geometric `p dA/dx` is not duplicated;
- chemical energy represented through composition-dependent absolute species energy is not re-added through an independent chemical `Qdot`;
- Eq. 11.26 has not been converted into dimensional `d(delta q)/dx` because the source mapping is incomplete.

## P11.4 — Integrated Baseline and Reproduction Evidence

### P11.4A Project-defined H2 integrated baseline — ACCEPTED

A clearly labelled `PROJECT_DEFINED_INTEGRATED_SMOKE_CASE` is accepted. It is not a source reproduction.

The accepted path combines teacher-compatible geometry/boundaries, H2 injection, algebraic composition, variable thermochemistry, Eq. 11.25 friction, Eq. 11.38 source terms, SSP-RK3, CFL stepping, and Eq. 11.46 steady closeout.

### P11.4B Three-level numerical grid audit — ACCEPTED

Accepted levels: 20 / 40 / 80 cells.

All levels satisfy the Eq. 11.46 density-change gate. Successive changes decrease for the recorded extrema. The record intentionally does **not** claim formal asymptotic grid independence.

Machine-readable record:

`cases/studies/data/p11_4_grid_convergence_acceptance.json`

### P11.4C Discrete conservation audit — ACCEPTED

The 80-cell accepted state is checked using the same semi-discrete RHS as the solver. The normalized mass-inventory rate is below the accepted 0.5% inlet-flow gate. Momentum and energy inventory rates are reported and should be normalized in later response studies, but no unsourced threshold is retroactively imposed on them.

### P11.4D Cao doctoral Case 2 — SOURCE IDENTITY / INLET FROZEN, FORMAL REPRODUCTION BLOCKED

Frozen source record:

`cases/studies/data/teacher_cao_case2_source.json`

Already frozen from the dissertation:

- Case identity and locator;
- `H2` fuel;
- `Ma=2.12`;
- `rho=0.28 kg/m^3`;
- `p=46.7 kPa`;
- `T=521 K`;
- `u=977 m/s`;
- reported `k=1.33`;
- `phi=0.2`;
- inlet `YN2=0.64`, `YO2=0.22`, `YH2O=0.13`, `YAr=0.01`;
- `Tw=900 K`;
- reported grid spacings `0.0001 m` and `0.001 m`.

Formal reproduction remains blocked by missing exact source `A(x)`, prescribed `Yi(x)` spatial information, and the original fuel/source spatial convention. The accepted project-defined H2 geometry/closure must not be substituted for those missing inputs.

## P12 — Evidence-Gated Response / Mode-Criterion Application

P12 remains a **project-defined continuous response study**. A defensible source-defined thermal-throat criterion has now been frozen from Cao Ruifeng Eq. (3-2): within that criterion's documented scope, the scram side has `min(Ma(x)) > 1`, the ram side has `min(Ma(x)) < 1`, and the critical thermal throat is `Ma=1`. The source does not provide a floating-point sonic tolerance, so any numerical tolerance must remain an explicit project choice rather than a source claim.

Safe current outputs include:

- Mach, pressure, temperature, velocity and density responses;
- composition fields;
- Eq. 11.46 convergence status;
- normalized mass/momentum/energy conservation diagnostics;
- explicit solver-admissibility status;
- the scoped Cao Eq. (3-2) thermal-throat side when the numerical point is otherwise accepted and the criterion is evaluated on its documented domain.

The accepted project-defined H2 response sweep has converged `phi=0.10` and `phi=0.20` points under the authoritative Eq. 11.46 `2e-5` maximum relative-density-change gate. The cold-start `phi=0.30` point is `solver/model-domain inadmissible` because the existing forward-flow guard triggers; it receives no physical mode label.

Grid-refined project-defined evidence also records `phi=0.24` on the Eq. (3-2) scram side for 20/40/80 cells, while `phi=0.26` is solver/model-domain inadmissible on all three grids. This is a grid-convergence trend/criterion application only and does **not** establish a grid-independent transition equivalence ratio.

A solver guard, nonconvergence, or isolated Mach observation outside the frozen criterion scope is not by itself evidence of unstart or a broader physical combustion-mode transition. Broader categorical classification remains blocked by source-compatible isolator/shock-train state variables, geometry, and any additional observables required by the source.

## Remaining Source Gaps

The remaining scientific gaps are now narrow and explicit:

- compatible `C10H22` thermochemistry if the pseudo-kerosene branch becomes necessary;
- Eq. 11.26 dimensional wall-heat mapping;
- variable-thermochemistry Steger-Warming production correction and Eq. 11.44 epsilon policy;
- Cao Case 2 exact spatial geometry/composition/source information;
- source-compatible isolator/shock-train state variables and geometry for broader categorical mode-transition claims.

## Supporting P11.2 Work

P11.2A remains an accepted public cold-flow surrogate. P11.2B remains an accepted scoped NASA Burrows-Kurkov reduced-order computational-reference benchmark. Jin/Liu remains supporting evidence with known source gaps.

These assets verify solver behavior and evidence discipline; they do not change the teacher-reference model priority.
