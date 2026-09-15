# P11 Parametric Study Plan

## Scientific scope

P11 converts the verified quasi-one-dimensional solver into reproducible study workflows while keeping numerical controls, physical inputs, modelling assumptions, and scientific claims separate.

`LBW` and `YBW` remain literal project labels until P11.3 freezes an authoritative discrimination criterion. Mach extrema, sonic fractions, sonic margin, and sonic-crossing count are diagnostics only.

## Stage breakdown

- P11.1 Parametric Study Foundation + controlled similarity pilot — framework implemented and verified; framework-only claim.
- **P11.2A Source-backed public surrogate cold-flow baseline + isolator-length diagnostic — IMPLEMENTED AND FORMALLY VERIFIED.**
- **P11.2B prescribed heat-release interface + closure infrastructure — IMPLEMENTED AND REGRESSION-VERIFIED; formal heated case still evidence-gated.**
- P11.3 Literature/teacher-defined LBW/YBW criterion + regime/transition map — planned after a defensible P11.2B heated case exists.
- P11.4 Integrated LBW/YBW comparison, robustness, interpretation, and study closure — planned.

P11.2A uses the public source ledger `cases/studies/data/p11_2_public_surrogate_source.json`. It must never be described as a Cao-thesis reproduction. P11.2B now has a verified direct heat-addition interface, but no formal heated engine case is accepted until one internally consistent evidence chain supplies a source-backed geometry/inflow definition and either an absolute `Qdot'(x)` profile or a normalized shape plus its matching absolute energy scale.

## P11.1 controlled pilot

P11.1 verifies study infrastructure using smooth quasi-one-dimensional isentropic cases. Its pressure-scale sweep is a framework control rather than an engine operating-condition claim. Wall friction, wall heat flux, fuel injection, and combustion inputs remain inactive in that pilot.

The P11.1 result establishes study metadata, repeatability, metrics, and controlled parameter-matrix machinery. It is not an engine calibration or experimental validation.

## P11.2A accepted source and model

The public surrogate source is Li et al. (2025), *Sensitive factors of ethylene combustion heat release under different combustion modes in scramjet engine*, DOI `10.7527/S1000-6893.2024.30944`.

Direct source evidence includes inlet Mach `2.52`, total temperature `1650 K`, total pressure `1.34 MPa`, dimensioned engine geometry, total ethylene operating points, and published one-factor geometry/injection levels.

The accepted reduced-order geometry keeps `H=H1` through `L1+L2`, varies main-passage height linearly `H1 -> H2` through `L3`, and sets `A(x)=W H(x)`. Cavity recirculation volume is not added to the one-dimensional core area. `gamma=1.4` and `R=287 J/(kg K)` remain explicit perfect-gas assumptions.

### P11.2A formal acceptance record

- code SHA: `9032d5e8304ac6022ba7c4f185b170c6ba9cddd2`
- Test workflow run `34880624298`: `801 passed in 47.01 s`
- dedicated formal workflow run `34880624357`: success
- runtime artifact `10362683519`
- artifact SHA-256 `364ea31e3395e0080ad7a426f20e4fc53dc438efb4b53147ed3dcc3fcb759789`

Baseline `P11A-PUBLIC-COLD-BASE` converged to residual `9.83971e-9`. The source-backed `L1=0.560 -> 0.280 m` variation also converged, but after removing the axial shift its overlapping fields agree to about `1e-10` relative. This is a model-scope finding: an inviscid, source-free constant-area isolator has no mechanism for the experimental reactive isolator-length sensitivity.

## P11.2B implemented infrastructure

The production solver supports a direct prescribed line heat-release input

`heat_release_rate_per_length = Qdot'(x) [W/m]`

in `quasi_1d_rhs`, `quasi_1d_rhs_transmissive`, `solve_quasi_1d`, and `solve_quasi_1d_steady`. It is mapped through the existing verified P8 semantics as `qdot_vol=Qdot'/A`, adds energy only, and is mutually exclusive with the burned-fuel/LHV path so the same energy cannot be counted twice.

The heat-release source ledger `cases/studies/data/p11_2b_heat_release_model_source.json` contains the core heat-release sources:

- **SRC07 — Cao et al. (2020):** one-dimensional teacher-lineage evidence that combustor heat-release distribution affects mode-transition boundary;
- **SRC08 — Jin et al. (2026):** experimental supersonic-combustion heat-release data, source-backed Eq. 7 / Eq. 8 functional forms, Eq. 11 energy relation, and the Liu model-B validation claim;
- **SRC09 — Tian et al. (2012):** modified quasi-one-dimensional heat-release inference checked with pressure and TDLAS measurements;
- **SRC10 — Liu et al. (2019):** primary axisymmetric model-A/model-B experiment explicitly reused by Jin.

Supporting records keep geometry and cross-source conflicts separate from the heat-release formula ledger:

- `cases/studies/data/p11_2b_jin_liu_condition_discrepancy.json` — freezes the Jin/Liu model/phi conflict;
- `cases/studies/data/p11_2b_liu_model_b_geometry_source.json` — freezes the source-backed model-B axial geometry and coordinate transform using SRC10, SRC11, and SRC12.

Study utilities implement the source-backed mathematical transforms without assigning unsupported operating-condition values:

- Eq. 7 normalized quasi-Gaussian shape;
- Eq. 8 asymmetric quasi-Gaussian shape downstream of heat-release initiation;
- exact finite-volume scaling of a normalized shape to a caller-supplied total thermal power;
- Eq. 11 cumulative total-temperature energy diagnostic;
- total-enthalpy-ratio diagnostics that keep dimensionless evidence separate from an absolute energy scale.

The Eq. 8 formula itself is unambiguous. Its case-specific parameters are not: the accessible Jin record gives raw Case-10 `x_c=98` and `k=5.6`, but the project will not freeze them until the coordinate/unit convention is tied to matching `x_i`, `x_m`, and an absolute energy scale.

## P11.2B Jin–Liu model-B validation candidate

This is the preferred independent validation path because Jin explicitly chooses Liu's cavity-free circular model B as closer to quasi-one-dimensional assumptions.

### Axial geometry already closed

The repository no longer treats source-to-solver axial mapping as a blocker.

SRC10 places station 3 / the most-upstream injector at `291.4 mm` downstream of the inlet lip. SRC12 independently gives an inlet length of `37.43 mm`; adding the SRC10 `254 mm` isolator yields `291.43 mm`, a `0.03 mm` closure residual. SRC12's `296 mm` constant-diameter run to the cavity leading edge also equals `254 + 42 mm` exactly.

Using the source-stated cavity floor/depth/ramp dimensions, the closeout-ramp axial projection is

`11 / tan(22.5 deg) = 26.55635 mm`.

Thus the model-B replacement tube corresponding to the cavity module is `61.55635 mm`, and the downstream diverging section begins `103.55635 mm` after station 3. The frozen coordinate convention is:

- `x_solver=0` at station 3 / injector;
- `x_solver = x_source - 0.2914 m` for SRC10 inlet-referenced coordinates;
- divergence start `x=0.10355635 m`;
- combustor exit `x=0.46055635 m`.

Independent total-length reconstructions close SRC11's approximately `752 mm` model within `0.044 mm` and SRC12's `752.43 mm` reconstruction within `0.444 mm`. These are retained as consistency checks, not fit parameters.

### Remaining geometry ambiguity

The downstream combustor is described as having a `2 deg cone angle`, but the recovered authoritative wording does not yet define whether this is the wall half-angle or full included angle. Because the two interpretations produce materially different area relief, the radial `A(x)` law remains blocked until this convention is source-resolved.

### Validation-condition identity remains unresolved

Jin states **model B, `phi=1.04`, experimental `M4=2.27`**. Liu Table 2 gives **model B, `phi=1.03`, `M4=2.27`**, while its exact `phi=1.04` ethylene row is **model A** with `M4=1.76`. A later same-geometry LES study uses the cavity-present configuration at `phi=1.04`; this is only contextual corroboration and is explicitly forbidden from overriding the primary-source conflict.

No automatic rounding, typo correction, or cross-model substitution is allowed.

## P11.2B formal-case evidence paths

`cases/studies/p11_2b_case_gate.py` makes case promotion explicit. Every candidate must have one source/case identity, traceable locators, and a source-to-solver axial coordinate mapping in metres. It then must satisfy one of two mutually distinct evidence paths:

1. **Normalized Eq. 8 path:** source-backed `x_i`, `x_m`, `x_c`, and `k` plus a separate matching absolute energy scale (total heat-release power, or stagnation-enthalpy increment plus mass flow).
2. **Absolute tabulated path:** a source-backed `x [m]` / `Qdot'(x) [W/m]` distribution. It already includes both shape and absolute scale, so the gate rejects a second independent `absolute_energy` scale.

The current ledger declares no formal candidate. The machine-readable readiness state is therefore correctly blocked rather than silently filled with assumptions.

## P11.2 input status

| Required input | P11.2A status | P11.2B status |
| --- | --- | --- |
| Physical axial scale / main-passage geometry | FROZEN surrogate mapping | **model-B axial stations FROZEN; radial area growth still gated on 2-deg convention** |
| Source-to-solver axial coordinate mapping | P11.2A-specific mapping | **Jin–Liu model-B mapping FROZEN** |
| Inlet total conditions and Mach | SOURCE + DERIVED primitive state | available for several source cases; exact validation station-3 state still case-specific |
| Direct solver energy-source interface | NOT USED | **IMPLEMENTED + TESTED** |
| Normalized axial heat-release functional form | NOT USED | **SOURCE-BACKED Eq. 7 / Eq. 8 IMPLEMENTED** |
| Absolute tabulated `Qdot'(x)` profile | NOT USED | **ALTERNATIVE FORMAL PATH; NOT YET RECOVERED** |
| Absolute heat-addition scale for normalized model | NOT USED | **REQUIRED WITH Eq. 8; NOT YET FROZEN** |
| Matching case-specific `x_i`, `x_m`, `x_c`, `k` | NOT USED | **REQUIRED FOR Eq. 8 PATH; NOT YET FROZEN** |
| Validation condition identity | NOT APPLICABLE | **BLOCKED: Jin B/1.04 vs Liu B/1.03 and A/1.04 conflict** |
| Axial fuel mass-source distribution | NOT USED | not required for direct heat-only surrogate; required for stronger P7 model |
| Fuel axial velocity / total enthalpy | NOT USED | not required for direct heat-only surrogate; required for stronger P7 model |
| Wall friction / heat transfer | DISABLED | optional; source/closure required if enabled |
| Isolator-length factor | FORMALLY EXECUTED; inert in cold-flow model | potentially meaningful after heat addition / additional physics |
| Injection-distance factor | DEFERRED | requires injection representation |
| Cavity-depth factor | DEFERRED | requires reduced-order cavity closure |
| LBW/YBW criterion | NOT FROZEN | P11.3 responsibility |

## P11.2B decision rule

A formal heated case must use an internally consistent evidence chain. Geometry, inflow, heat-release shape, and energy scale may not be borrowed from unrelated experiments and then presented as a reproduction.

The minimal admissible energy-only P11.2B case requires:

1. source-backed geometry and inflow;
2. one complete heat-release evidence path defined above;
3. explicit mapping into solver `Qdot'(x)` and `x`;
4. convergence and boundary-applicability checks;
5. a claim level no stronger than the evidence supports.

A stronger case including fuel mass and momentum additionally needs axial fuel distribution, fuel velocity, and fuel total enthalpy. Total fuel flow alone is never converted into a uniform source by default.

## Remaining P11.2B blockers

For the preferred Jin–Liu model-B validation, four bounded items remain:

1. resolve the model/`phi` identity conflict;
2. recover Jin Fig. 14's exact axial heat-release shape or fitted parameters with traceable coordinates;
3. recover the corresponding absolute stagnation-enthalpy increment plus mass flow / station-3 absolute enthalpy, or an absolute `Qdot'(x)` profile;
4. resolve the `2 deg cone angle` convention before freezing radial area growth.

The station-3 absolute x coordinate and axial divergence-start position are no longer open blockers and must not be reintroduced as such.

## Mode-classification policy

No P11.2 result may automatically be labelled LBW or YBW. The Jin paper's BL/LDD/SDC heat-release modes and quantitative separation/kinetic criteria are useful physical context but are not automatically equivalent to the project's LBW/YBW labels. P11.3 must freeze definitions, source locators, observables, and thresholds separately.

## Metric metadata contract

Each formal study must report symbol, units, definition, interpretation, scope, source status, and whether the metric is a scientific gate or a diagnostic. Physical inputs must additionally record source ID/locator, raw value, SI conversion, and derivation status (`source`, `derived`, `model-assumption`, `numerical-control`, or `deferred`).

## Current limitations

- quasi-one-dimensional calorically perfect gas;
- experimental vitiated-air composition is not species-resolved;
- no explicit transverse-jet mixing, cavity recirculation, finite-rate chemistry, ignition, or species transport;
- shock-train / separation physics is not yet integrated into the P11.2A geometry study;
- a direct heat-addition interface is not itself a validated combustion model;
- no authoritative LBW/YBW discrimination criterion has yet been frozen.
