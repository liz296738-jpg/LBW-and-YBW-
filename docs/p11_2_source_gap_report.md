# P11.2 Authoritative Source and Baseline Gap Report

## Status

`P11.2A FORMALLY VERIFIED — SOURCE-BACKED PUBLIC COLD-FLOW SURROGATE`

`P11.2B HEAT-RELEASE INTERFACE/CLOSURE IMPLEMENTED — FORMAL HEATED CASE STILL EVIDENCE-GATED`

The original P11.2 blocker combined two separate problems: missing solver support for a source-backed axial heat-release law and missing evidence for one complete physical heated case. The solver/interface problem is solved. P11.2B now has a direct `Qdot'(x)` interface, source-backed Eq. 7/Eq. 8 closure utilities, regression tests, evidence records, and a formal-case promotion gate. The remaining blocker is a physical case-definition/provenance problem, not missing numerical plumbing.

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
| SRC08 | Jin et al. (2026), DOI `10.1016/j.combustflame.2026.114876` | experimental heat-release / 1-D closure paper | Eq. 7, Eq. 8, Eq. 11 and model-B validation context |
| SRC09 | Tian et al. (2012), DOI `10.2514/6.2012-5833` | modified quasi-1D experiment/model paper | pressure-fitted heat-release distributions checked with TDLAS |
| SRC10 | Liu et al. (2019), DOI `10.2514/1.J058391` | primary axisymmetric experiment explicitly reused by Jin | strongest public independent validation candidate |
| SRC11 | Liu et al. (2019), AIAA 2019-1681, DOI `10.2514/6.2019-1681` | same-program experimental geometry source | independent overall-length and cavity-replacement description |
| SRC12 | Liu & Yao (2021), AIAA 2021-3536, DOI `10.2514/6.2021-3536` | same-geometry numerical reconstruction | dimensional cross-check only; never allowed to override primary experimental conflicts |

Machine-readable records:

- `cases/studies/data/p11_2_public_surrogate_source.json`
- `cases/studies/data/p11_2b_heat_release_model_source.json`
- `cases/studies/data/p11_2b_jin_liu_condition_discrepancy.json`
- `cases/studies/data/p11_2b_liu_model_b_geometry_source.json`

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

The study layer contains:

- Jin Eq. 7 normalized quasi-Gaussian profile;
- Jin Eq. 8 asymmetric quasi-Gaussian profile downstream of heat-release initiation;
- exact finite-volume scaling from normalized shape to caller-supplied total power;
- Jin Eq. 11 cumulative total-temperature energy integral;
- total-enthalpy-ratio diagnostics that preserve dimensionless evidence without inventing an absolute energy scale.

Therefore the project no longer lacks a mathematically defined path from source-backed heat-release evidence to the verified P8 energy equation.

## SRC08 / SRC09 evidence boundary

SRC08 reports a Mach-2.52, `T0=1650 K`, `P0=1.3 MPa`, ethylene-fueled direct-connected experiment and a quasi-Gaussian one-dimensional heat-release model. Its Eq. 8 depends on `Q*_m`, `x_i`, `x_m`, `x_c`, and `k`. Case-10 text reports raw `x_c=98`, `k=5.6`, fit `R^2=0.997`, and cumulative heat fraction `0.92` at `x_c`, but matching `x_i`, `x_m`, coordinate convention, and absolute thermal power are not frozen.

SRC09 supplies four quasi-one-dimensional operating cases with Mach number, total temperature, air mass flow, equivalence ratio, and reported combustion efficiency. Its heat-release distributions were inferred from pressure and checked with TDLAS temperature/velocity data. The accessible text does not tabulate a complete solver-ready axial heat-release profile or unambiguously expose every fuel/LHV convention required for an absolute-power reconstruction, so no formal profile is manufactured from it.

## Strongest validation candidate: SRC08 + SRC10, cross-checked by SRC11/SRC12

Jin et al. explicitly validate their quasi-Gaussian model using the cavity-free circular **model B** experiment of Liu et al. Jin states that this geometry more closely satisfies quasi-one-dimensional assumptions than cavity/corner-flow configurations.

SRC10 provides a `254 mm` long, `35 mm` diameter constant-area isolator; fuel injection `291.4 mm` downstream of the inlet lip through sixteen `0.75 mm` sonic nozzles inclined `45 deg` backward; a cavity leading edge `42 mm` downstream of the injector in model A; a `35 mm` floor, `11 mm` depth and `22.5 deg` closeout ramp; and a `357 mm` downstream diverging combustor described as `2 deg cone angle`. Model B replaces the cavity module with a constant `35 mm` tube.

For reacting ethylene cases, Liu uses average `gamma=1.31` and `cp=1255 J/(kg K)`, obtains exit Mach from static/pitot measurements, and evaluates exit stagnation enthalpy with a heat-flux probe. Table 2 gives a model-B ethylene condition at `phi=1.03` with `M4=2.27`, `pt4=17383.8 Pa`, `pt4/pt3=0.39`, and `Ht4/Ht3=1.16`.

Jin reports theoretical exit Mach `2.24` versus experimental `2.27`, and states that the validation heat-release distribution used the quasi-Gaussian model together with the experimental PLIF image and measured exit stagnation-enthalpy increment.

## Geometry/coordinate gap that is now closed

The station and divergence locations no longer require visual digitization.

First, SRC10 places station 3 / the most-upstream injector at `291.4 mm` downstream of the inlet lip. SRC12 independently gives a `37.43 mm` inlet and SRC10 gives a `254 mm` isolator:

`37.43 + 254 = 291.43 mm`.

The `0.03 mm` difference from `291.4 mm` is retained as a rounding-level cross-check. A second identity closes exactly:

`254 mm isolator + 42 mm injector-to-cavity distance = 296 mm`,

matching SRC12's constant-diameter run from inlet end to cavity leading edge.

Second, the cavity closeout ramp has axial projection

`11 / tan(22.5 deg) = 26.55635 mm`,

so the corresponding model-B replacement-tube module is

`35 + 26.55635 = 61.55635 mm`.

The divergence therefore begins

`42 + 61.55635 = 103.55635 mm`

downstream of station 3. With `x_solver=0` at station 3, the frozen axial coordinates are:

- divergence start: `x=0.10355635 m`;
- combustor exit: `x=0.46055635 m`;
- source-to-solver transform for SRC10 inlet-referenced x: `x_solver = x_source - 0.2914 m`.

The reconstruction closes SRC11's `752 mm` overall length within about `0.044 mm`; using SRC12's full-scale dimensions closes its `752.43 mm` length within about `0.444 mm`. These are consistency residuals, not fitted parameters.

Therefore **source-to-solver axial coordinate mapping is no longer an open blocker**.

One geometry interpretation remains unresolved: the recovered sources call the downstream section a `2 deg cone angle`, but do not yet unambiguously state whether that is the wall half-angle or full included angle. Because this changes the radius and area growth materially, the radial `A(x)` law remains evidence-gated.

## Validation-condition conflict remains open

Jin labels the independent validation as model B with `phi=1.04` and experimental `M4=2.27`.

Liu Table 2 instead gives:

- model B, C2H4, `phi=1.03`: `M4=2.27`, `Ht4/Ht3=1.16`;
- model A, C2H4, exactly `phi=1.04`: `M4=1.76`, `Ht4/Ht3=1.29`.

SRC12 separately studies the cavity-present geometry at `phi=1.04`. This is contextual evidence only and cannot prove a typo in Jin or replace the primary experimental record. The repository therefore records the conflict as `UNRESOLVED_CROSS_MODEL_EQUIVALENCE_RATIO_CONFLICT` and forbids silent rounding or cross-model substitution.

## Formal-case promotion gate

`cases/studies/p11_2b_case_gate.py` separates solver capability from scientific case readiness. Every formal candidate requires one declared case identity, traceable locators, and an explicit source-to-solver coordinate mapping.

It accepts one of two heat-release evidence paths:

1. **normalized Eq. 8 path:** source-backed `x_i`, `x_m`, `x_c`, `k` plus a separate source-backed total heat-release power, or stagnation-enthalpy increment plus mass flow, for that same condition;
2. **absolute tabulated path:** a traceable `x [m]` / `Qdot'(x) [W/m]` table, which already contains both shape and absolute energy scale and therefore must not be given a second independent absolute-energy scale.

Cross-source/cross-condition mixing is rejected. `candidate_formal_cases` remains empty, so the machine-readable status remains:

`BLOCKED_PENDING_SOURCE_BACKED_ABSOLUTE_PROFILE_OR_SHAPE_PLUS_ENERGY`

## Primary remaining blockers

The preferred Jin–Liu model-B chain is now blocked by four precisely bounded items:

1. **condition identity:** resolve Jin model-B `phi=1.04` versus Liu model-B `phi=1.03` / model-A `phi=1.04`;
2. **axial heat-release shape:** recover the exact Fig. 14 shape or fitted `Q_m/x_i/x_m/x_c/k` values with traceable coordinates;
3. **absolute energy scale:** recover Jin's measured stagnation-enthalpy increment and matching mass flow / station-3 absolute enthalpy, or an already-absolute `Qdot'(x)` table;
4. **radial area law:** resolve whether `2 deg cone angle` denotes wall half-angle or included angle.

The old blocker “freeze full source-to-solver axial coordinate mapping” is closed and must not reappear in readiness reporting.

If P7 fuel mass addition is later activated, axial fuel mass-source distribution, fuel axial velocity, and fuel specific total enthalpy are additionally required. They are not required for the minimal direct-energy surrogate.

## Confirmed Cao-thesis evidence retained

SRC02 still provides useful locatable records, including an idealized Chapter-2 inlet case, Chapter-3 `gamma=1.4` and kerosene `Hf=42,000 kJ/kg` for that cycle model, and Chapter-5 isolator-entry conditions for several ground-test flight-Mach settings. These records remain useful but do not authorize mixing unrelated thesis cases into one artificial baseline.

## Next development decision

Continue evidence recovery on the Jin–Liu model-B chain before inventing a synthetic heated baseline. Publisher supplementary material or an author-provided data table is preferred for the Fig. 14 shape and absolute energy inputs. Low-resolution figure reading, untracked digitization, nominal-geometry mass-flow inference, and cross-condition parameter mixing remain prohibited.

In parallel, the teacher-designated Cao materials remain the preferred source for the project's ultimate mode-transition lineage. No formal reactive curve is promoted until one evidence chain passes the gate.
