# P11.2 Authoritative Source and Baseline Gap Report

## Status

`P11.2A FORMALLY VERIFIED — SOURCE-BACKED PUBLIC COLD-FLOW SURROGATE`

`P11.2B HEAT-RELEASE INTERFACE/CLOSURE IMPLEMENTED — FORMAL HEATED CASE STILL EVIDENCE-GATED`

The original P11.2 blocker combined two separate problems: missing solver support for a source-backed axial heat-release law and missing evidence for one complete physical heated case. The first problem is now solved. P11.2B has a direct `Qdot'(x)` interface, source-backed Eq. 7/Eq. 8 closure utilities, regression tests, and a formal-case evidence gate. The remaining blocker is now purely a case-definition/provenance problem.

The public P11.2A surrogate does **not** replace the teacher-designated Cao Ruifeng material and must not be cited as a Cao-thesis reproduction.

## Source inventory

| ID | Source | Authority / role | Current use |
| --- | --- | --- | --- |
| SRC01 | teacher instruction screenshots | project instruction | establishes the Cao Ruifeng material as teacher-designated reference |
| SRC02 | Cao Ruifeng doctoral thesis (2016) | project-designated thesis | candidate inlet records, kerosene LHV, combustion-mode context |
| SRC03 | Cao Ruifeng master's thesis (2011) | project-designated modelling reference | one-dimensional modelling context; no complete solver-ready heated case frozen yet |
| SRC04 | *Theory and Application of Hypersonic Aerodynamic Layout*, Ch. 11 | project technical reference | generalized one-dimensional source-term semantics |
| SRC05 | repository solver / P3–P10 verification evidence | implementation authority | accepted numerical capability |
| SRC06 | Li et al. (2025), DOI `10.7527/S1000-6893.2024.30944` | peer-reviewed experiment | P11.2A geometry, inflow, operating points, Table-4 factors |
| SRC07 | Cao et al. (2020), DOI `10.1016/j.ast.2019.105590` | Cao-lineage one-dimensional study | confirms heat-release distribution as a mode-transition influence |
| SRC08 | Jin et al. (2026), DOI `10.1016/j.combustflame.2026.114876` | experimental heat-release / 1-D closure paper | Eq. 7, Eq. 8, Eq. 11 and independent model-B validation context |
| SRC09 | Tian et al. (2012), DOI `10.2514/6.2012-5833` | modified quasi-1D experiment/model paper | pressure-fitted heat-release distributions checked with TDLAS |
| SRC10 | Liu et al. (2019), DOI `10.2514/1.J058391` | axisymmetric experimental source explicitly reused by Jin | strongest public independent validation candidate recovered so far |

Machine-readable ledgers:

- `cases/studies/data/p11_2_public_surrogate_source.json`
- `cases/studies/data/p11_2b_heat_release_model_source.json`

Focused validation note:

- `docs/p11_2b_jin_liu_validation_candidate.md`

## P11.2A closure

SRC06 supplies source-backed inflow, geometry, fuel operating points, and Table-4 factor levels. P11.2A freezes an explicit reduced-order core-flow mapping, keeps cavity recirculation outside `A(x)`, and uses the existing perfect-gas assumptions `gamma=1.4`, `R=287 J/(kg K)`. Fuel, burn, wall-friction, and wall-heat sources remain disabled.

Formal acceptance:

- source/code SHA: `9032d5e8304ac6022ba7c4f185b170c6ba9cddd2`
- standard Test run `34880624298`: `801 passed in 47.01 s`
- dedicated formal run `34880624357`: success
- runtime artifact `10362683519`
- artifact SHA-256 `364ea31e3395e0080ad7a426f20e4fc53dc438efb4b53147ed3dcc3fcb759789`

The baseline and `L1=560 -> 280 mm` cases both converge. After removing the expected coordinate shift, their overlapping cold-flow fields agree to about `1e-10` relative. This demonstrates that the inviscid source-free constant-area isolator contains no mechanism for the experimental reactive isolator-length sensitivity.

## P11.2B software gap that is closed

The production solver accepts a direct line heat-release distribution `Qdot'(x) [W/m]`, maps it conservatively to `Qdot'/A [W/m^3]`, and adds energy only. It is mutually exclusive with the existing burned-fuel/LHV energy path to prevent double counting.

Regression coverage establishes that zero direct heat preserves the legacy path, the new input affects only the energy source, direct heat is equivalent to the burned-fuel/LHV path when both represent the same `Qdot'(x)`, invalid profiles are rejected, and both transient and steady pseudo-time propagation are covered.

A full-suite checkpoint at commit `72d953f42e3f1ab578701db2ec9441a8c5b2be69` passed GitHub Actions run `34884490236` with `846 passed in 43.51 s`. Later evidence/ledger changes remain subject to the same full-suite CI.

The study layer contains:

- Jin Eq. 7 normalized quasi-Gaussian profile;
- Jin Eq. 8 asymmetric quasi-Gaussian profile downstream of heat-release initiation;
- exact finite-volume scaling from normalized shape to caller-supplied total power;
- Jin Eq. 11 cumulative total-temperature energy integral.

Therefore the project no longer lacks a mathematically defined path from source-backed heat-release evidence to the verified P8 energy equation.

## SRC08 / SRC09 evidence boundary

SRC08 reports a Mach-2.52, `T0=1650 K`, `P0=1.3 MPa`, ethylene-fueled direct-connected experiment and a quasi-Gaussian one-dimensional heat-release model. Its Eq. 8 depends on `Q*_m`, `x_i`, `x_m`, `x_c`, and `k`. Case-10 text reports raw `x_c=98`, `k=5.6`, fit `R^2=0.997`, and cumulative heat fraction `0.92` at `x_c`, but matching `x_i`, `x_m`, coordinate convention, and absolute thermal power are not frozen.

SRC09 supplies four quasi-one-dimensional operating cases with Mach number, total temperature, air mass flow, equivalence ratio, and reported combustion efficiency. Its heat-release distributions were inferred from pressure and checked with TDLAS temperature/velocity data. The accessible text does not tabulate a complete solver-ready axial heat-release profile or unambiguously expose every fuel/LHV convention required for an absolute-power reconstruction, so no formal profile is manufactured from it.

## New strongest validation candidate: SRC08 + SRC10

Jin et al. explicitly validate their quasi-Gaussian model using the cavity-free circular **model B** experiment of Liu et al. This is important because Jin states that the geometry more closely satisfies quasi-one-dimensional assumptions than cavity/corner-flow configurations.

Liu's source provides a highly usable geometry chain: a `254 mm` long, `35 mm` diameter constant-area isolator; fuel injection `291.4 mm` downstream of the inlet lip through sixteen `0.75 mm` sonic nozzles inclined `45 deg` backward; and a `2 deg`, `357 mm` long diverging combustor. Model B replaces the cavity module with a constant `35 mm` tube before the diverging section. Liu also explicitly defines the engine x-axis and locates its origin at the center of the inlet.

For reacting ethylene cases, Liu uses average `gamma=1.31` and `cp=1255 J/(kg K)`, obtains exit Mach from static/pitot measurements, and evaluates exit stagnation enthalpy with a heat-flux probe. Table 2 gives a model-B ethylene condition at `phi=1.03` with `M4=2.27`, `pt4=17383.8 Pa`, `pt4/pt3=0.39`, and `Ht4/Ht3=1.16`.

Jin's validation discussion reports theoretical exit Mach `2.24` versus experimental `2.27`, and says the heat-release distribution was estimated from the Jin model together with the experimental PLIF image and measured exit stagnation-enthalpy increment. This strongly links the Jin validation to Liu's model-B dataset.

However, Jin labels the test as model B with `phi=1.04`, whereas Liu Table 2 lists the matching experimental `M4=2.27` row at `phi=1.03`. The repository explicitly records this as `UNRESOLVED_1.04_VS_1.03_DISCREPANCY`. It is not silently rounded away.

The Jin–Liu chain is stored under `candidate_validation_chains`, not `candidate_formal_cases`.

## Why the Jin–Liu case is still blocked

Four evidence items remain before exact reproduction is allowed:

1. resolve whether Jin `phi=1.04` and Liu model-B `phi=1.03` refer to the same physical run / rounding convention;
2. recover the heat-release shape or fitted quasi-Gaussian parameters used for this exact validation condition with a retained extraction record;
3. recover the **absolute** stagnation-enthalpy increment and the matching mass flow required to scale the heat-release profile; `Ht4/Ht3=1.16` is not converted into an absolute increment without a traceable station-3 enthalpy value;
4. freeze the full source-to-solver axial coordinate mapping for the validation domain.

The ACT-II facility paper documents several arc-heater characterization mass flows (`7.3`, `13.3`, `22.2 g/s`), but the repository does not assign any of them to the Liu validation run without direct evidence.

## Confirmed Cao-thesis evidence retained

SRC02 still provides useful locatable records, including an idealized Chapter-2 inlet case, Chapter-3 `gamma=1.4` and kerosene `Hf=42,000 kJ/kg` for that cycle model, and Chapter-5 isolator-entry conditions for several ground-test flight-Mach settings. These records remain useful but do not authorize mixing unrelated thesis cases into one artificial baseline.

## Formal-case promotion gate

`cases/studies/p11_2b_case_gate.py` separates solver capability from scientific case readiness. Every formal candidate requires one declared case identity, traceable locators, and an explicit source-to-solver coordinate mapping.

It accepts one of two heat-release evidence paths:

1. **normalized Eq. 8 path:** source-backed `x_i`, `x_m`, `x_c`, `k` plus a separate source-backed total heat-release power, or stagnation-enthalpy increment plus mass flow, for that same condition;
2. **absolute tabulated path:** a traceable `x [m]` / `Qdot'(x) [W/m]` table, which already contains both shape and absolute energy scale and therefore must not be given a second independent absolute-energy scale.

Cross-source/cross-condition mixing is rejected. `candidate_formal_cases` remains empty, so the machine-readable status remains:

`BLOCKED_PENDING_SOURCE_BACKED_ABSOLUTE_PROFILE_OR_SHAPE_PLUS_ENERGY`

`cases/studies/p11_2b_readiness.py` writes this status as deterministic JSON. `--require-ready` converts the readiness state into a hard execution gate for a formal heated run.

## Primary remaining blocker

The formal P11.2B evidence gap is now precisely defined. The project needs one complete internally consistent case with:

- source-backed geometry/inflow and coordinate mapping;
- either an absolute axial `Qdot'(x) [W/m]` table, or normalized heat-release parameters plus a matching absolute heat-addition scale;
- boundary/convergence checks under the heated state.

If P7 fuel mass addition is later activated, axial fuel mass-source distribution, fuel axial velocity, and fuel specific total enthalpy are additionally required. They are not required for the minimal direct-energy surrogate.

## Next development decision

The first evidence priority is now the Jin–Liu model-B chain because it is an independent experiment explicitly selected by Jin for quasi-one-dimensional validation. Continue evidence recovery there before inventing a synthetic heated baseline or transplanting Jin parameters into the P11.2A Li geometry.

In parallel, the teacher-designated Cao materials remain the preferred source for the project's ultimate mode-transition lineage. No formal reactive curve is promoted until one evidence chain passes the gate.
