# P11 Parametric Study Plan

## Scientific scope

P11 converts the verified quasi-one-dimensional solver into reproducible study workflows while keeping numerical controls, physical inputs, modelling assumptions, and scientific claims separate.

`LBW` and `YBW` remain literal project labels until P11.3 freezes an authoritative discrimination criterion. Mach extrema, sonic fractions, sonic margin, and sonic-crossing count are diagnostics only.

## Stage breakdown

- P11.1 Parametric Study Foundation + controlled similarity pilot — framework implemented and verified; framework-only claim.
- **P11.2A Source-backed public surrogate cold-flow baseline + isolator-length diagnostic — IMPLEMENTED AND FORMALLY VERIFIED.**
- **P11.2B prescribed heat-release interface + closure infrastructure — IMPLEMENTED AND REGRESSION-VERIFIED; formal reactive parameter set still evidence-gated.**
- P11.3 Literature/teacher-defined LBW/YBW criterion + regime/transition map — planned after a defensible P11.2B heated case exists.
- P11.4 Integrated LBW/YBW comparison, robustness, interpretation, and study closure — planned.

P11.2A uses the public source ledger `cases/studies/data/p11_2_public_surrogate_source.json`. It must never be described as a Cao-thesis reproduction. P11.2B now has a verified direct heat-addition interface, but no formal heated engine case is accepted until one internally consistent source supplies or supports both absolute heat addition and axial shape parameters.

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

The production solver now supports a direct prescribed line heat-release input

`heat_release_rate_per_length = Qdot'(x) [W/m]`

in `quasi_1d_rhs`, `quasi_1d_rhs_transmissive`, `solve_quasi_1d`, and `solve_quasi_1d_steady`. It is mapped through the existing verified P8 semantics as `qdot_vol=Qdot'/A`, adds energy only, and is mutually exclusive with the burned-fuel/LHV path so the same energy cannot be counted twice.

The source ledger `cases/studies/data/p11_2b_heat_release_model_source.json` currently contains:

- **SRC07 — Cao et al. (2020):** one-dimensional teacher-lineage evidence that combustor heat-release distribution affects mode-transition boundary;
- **SRC08 — Jin et al. (2026):** experimental supersonic-combustion heat-release data and source-backed quasi-Gaussian Eq. 7 / asymmetric Eq. 8 functional forms plus the Eq. 11 total-temperature energy relation;
- **SRC09 — Tian et al. (2012):** modified quasi-one-dimensional heat-release inference validated against pressure and TDLAS measurements, including four published operating cases and combustion efficiencies.

Study utilities now implement the source-backed mathematical transforms without assigning unsupported operating-condition values:

- Eq. 7 normalized quasi-Gaussian shape;
- Eq. 8 asymmetric quasi-Gaussian shape downstream of heat-release initiation;
- exact finite-volume scaling of a shape to a caller-supplied total thermal power;
- Eq. 11 cumulative total-temperature energy diagnostic.

The Eq. 8 formula itself is now unambiguous. Its case-specific parameters are not: the accessible Jin record gives raw Case-10 `x_c=98` and `k=5.6`, but the project will not freeze them until the coordinate/unit convention is tied to matching `x_i`, `x_m`, and absolute heat-addition evidence.

The first P11.2B regression closure passed on commit `e36cfb124f9bd0a8ddb3be6d548f79a751fdf471`: GitHub Actions run `34882069673` completed with `828 passed in 60.67 s`. Later closure-form and evidence-ledger additions must continue to pass the same full regression suite before acceptance.

## P11.2 input status

| Required input | P11.2A status | P11.2B status |
| --- | --- | --- |
| Physical axial scale / main-passage geometry | FROZEN surrogate mapping | available as starting geometry or source-specific validation geometry |
| Inlet total conditions and Mach | SOURCE + DERIVED primitive state | available for several source cases |
| Direct solver energy-source interface | NOT USED | **IMPLEMENTED + TESTED** |
| Normalized axial heat-release functional form | NOT USED | **SOURCE-BACKED Eq. 7 / Eq. 8 IMPLEMENTED** |
| Absolute total heat addition | NOT USED | **PRIMARY BLOCKER** for formal heated case |
| Matching case-specific `x_i`, `x_m`, `x_c`, `k` | NOT USED | **PRIMARY BLOCKER** unless recovered from one consistent case |
| Axial fuel mass-source distribution | NOT USED | not required for energy-only surrogate; required for stronger P7 model |
| Fuel axial velocity / total enthalpy | NOT USED | not required for energy-only surrogate; required for stronger P7 model |
| Wall friction / heat transfer | DISABLED | optional; source/closure required if enabled |
| Isolator-length factor | FORMALLY EXECUTED; inert in cold-flow model | potentially meaningful after heat addition / additional physics |
| Injection-distance factor | DEFERRED | requires injection representation |
| Cavity-depth factor | DEFERRED | requires reduced-order cavity closure |
| LBW/YBW criterion | NOT FROZEN | P11.3 responsibility |

## P11.2B decision rule

A formal heated case must use an internally consistent evidence chain. Geometry, inflow, total heat addition, and axial heat-release shape may not be borrowed from unrelated experiments and then presented as a reproduction.

The minimal admissible energy-only P11.2B case requires:

1. source-backed geometry and inflow;
2. source-backed or transparently derived absolute total heat addition;
3. source-backed axial shape parameters for the same case;
4. explicit mapping into `Qdot'(x)`;
5. convergence and boundary-applicability checks;
6. a claim level no stronger than the evidence supports.

A stronger case including fuel mass and momentum additionally needs axial fuel distribution, fuel velocity, and fuel total enthalpy. Total fuel flow alone is never converted into a uniform source by default.

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
