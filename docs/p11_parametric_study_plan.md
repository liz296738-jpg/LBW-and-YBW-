# P11 Parametric Study Plan

## Scientific scope

P11 converts the verified quasi-one-dimensional solver into reproducible study workflows while keeping numerical controls, physical inputs, modelling assumptions, and scientific claims separate.

`LBW` and `YBW` remain literal project labels until P11.3 freezes an authoritative discrimination criterion. Mach extrema, sonic fractions, sonic margin, and sonic-crossing count are diagnostics only.

## Stage breakdown

- P11.1 Parametric Study Foundation + controlled similarity pilot — framework implemented and verified; framework-only claim.
- **P11.2A Source-backed public surrogate cold-flow baseline + isolator-length diagnostic — IMPLEMENTED AND FORMALLY VERIFIED.**
- P11.2B Reactive physical baseline / prescribed heat-release closure — evidence-gated; next development target.
- P11.3 Literature/teacher-defined LBW/YBW criterion + regime/transition map — planned after P11.2B.
- P11.4 Integrated LBW/YBW comparison, robustness, interpretation, and study closure — planned.

P11.2A uses the public source ledger `cases/studies/data/p11_2_public_surrogate_source.json`. It must never be described as a Cao-thesis reproduction. P11.2B remains reserved for a stronger source-backed reactive case or explicitly documented prescribed-heat-release surrogate.

## P11.1 controlled pilot

P11.1 verifies study infrastructure using smooth quasi-one-dimensional isentropic cases. Its pressure-scale sweep is a framework control rather than an engine operating-condition claim. Wall friction, wall heat flux, fuel injection, and combustion inputs remain inactive in that pilot.

The P11.1 result establishes study metadata, repeatability, metrics, and controlled parameter-matrix machinery. It is not an engine calibration or experimental validation.

## P11.2A accepted source and model

The public surrogate source is Li et al. (2025), *Sensitive factors of ethylene combustion heat release under different combustion modes in scramjet engine*, DOI `10.7527/S1000-6893.2024.30944`.

Direct source evidence includes:

- inlet Mach `2.52`, total temperature `1650 K`, total pressure `1.34 MPa`, and vitiated-air composition (Table 1);
- dimensioned engine geometry (Fig. 2 / Table 2);
- total ethylene flow and injector-module operating points (Table 3);
- one-factor levels for isolator length, injection distance, cavity depth, and throat size (Table 4).

The accepted P11.2A reduced-order mapping uses the source-backed `L1/L2/L3/W/H1/H2`, keeps `H=H1` through `L1+L2`, varies the main-passage height linearly `H1 -> H2` through `L3`, and sets `A(x)=W H(x)`. Cavity recirculation volume is not added to the one-dimensional core area. The project perfect-gas values `gamma=1.4` and `R=287 J/(kg K)` remain explicit model assumptions.

Fuel injection, prescribed combustion, wall friction, and wall heat transfer are disabled in P11.2A because the paper does not provide the complete solver-ready source distributions required by P7/P8.

## P11.2A formal acceptance record

The accepted exact-SHA evidence is recorded in `artifacts/p11_2a/p11_2a_formal_evidence.json`.

- code SHA: `9032d5e8304ac6022ba7c4f185b170c6ba9cddd2`
- Test workflow run `34880624298`: `801 passed in 47.01 s`
- dedicated formal workflow run `34880624357`: success
- runtime artifact `10362683519`
- artifact SHA-256 `364ea31e3395e0080ad7a426f20e4fc53dc438efb4b53147ed3dcc3fcb759789`

Baseline `P11A-PUBLIC-COLD-BASE` (`L1=0.560 m`) converged in `1779` steps to residual `9.83971e-9`. The solution remained supersonic from `Mach=2.52` at the inlet to `Mach=2.71312` at the outlet, while static pressure changed from `76.026 kPa` to `56.388 kPa` and temperature from `726.847 K` to `667.421 K`. The cell-centred mass-flow relative span is `1.01872e-3` and is retained as a numerical diagnostic rather than hidden by a new ad-hoc gate.

The source-backed isolator-length variation `L1=0.560 -> 0.280 m` also converged. Once the `0.280 m` coordinate shift is removed, the overlapping solutions agree to approximately `1e-10` relative. This is a **model-scope result**: an inviscid, source-free constant-area isolator has no mechanism for the experimental reactive isolator-length sensitivity. P11.2A therefore does not claim agreement with the paper's combustion trend.

## P11.2 input status

| Required input | P11.2A status | P11.2B status |
| --- | --- | --- |
| Physical axial scale / main-passage geometry | FROZEN surrogate mapping | available as starting geometry |
| Inlet total conditions and Mach | SOURCE + DERIVED primitive state | available |
| Outlet treatment | VERIFIED supersonic-outflow for P11.2A | must be rechecked for heated cases |
| Wall friction / heat transfer | DISABLED | optional; needs sourced/approved closure if enabled |
| Total fuel flow | SOURCE AVAILABLE | available operating target only |
| Axial fuel mass-source distribution | NOT USED | NOT FROZEN |
| Fuel axial velocity / total enthalpy | NOT USED | NOT FROZEN |
| Prescribed burned-fuel / heat-release distribution | NOT USED | **PRIMARY BLOCKER / closure required** |
| Fuel LHV | not required | source can be added once fuel/closure is selected |
| Isolator-length factor | FORMALLY EXECUTED; dynamically inert in current cold-flow model | potentially meaningful with added physics |
| Injection-distance factor | DEFERRED | requires injection representation |
| Cavity-depth factor | DEFERRED | requires reduced-order cavity closure |
| Throat-size factor | DEFERRED pending unambiguous local area mapping | candidate future factor |
| LBW/YBW criterion | NOT FROZEN | P11.3 responsibility |

## P11.2B decision rule

The next stage must not turn total fuel flow into an arbitrary uniform source. A reactive or heat-addition case can enter the formal study only when its axial energy-addition representation is traceable to a source or an explicitly approved reduced-order closure.

A minimal defensible P11.2B may use a **prescribed heat-release / burned-fuel distribution** without P7 mass addition if the source and mathematical transformation are documented. A stronger case including fuel mass and momentum additionally needs axial fuel distribution, fuel velocity, and fuel total enthalpy.

Any such closure must preserve the existing solver semantics and be labelled according to its evidence level. It must not be presented as detailed chemistry, finite-rate combustion, or an exact experiment reproduction.

## Mode-classification policy

No P11.2 result may automatically be labelled LBW or YBW. The experimental paper's verbal mode observations are comparison context only. P11.3 must separately freeze definitions, observables, thresholds/logic, and source locators before a regime map is produced.

## Metric metadata contract

Each formal study must report symbol, units, definition, interpretation, scope, source status, and whether the metric is a scientific gate or a diagnostic. Physical inputs must additionally record source ID/locator, raw value, SI conversion, and derivation status (`source`, `derived`, `model-assumption`, `numerical-control`, or `deferred`).

## Current limitations

- quasi-one-dimensional calorically perfect gas;
- experimental vitiated-air composition is not species-resolved;
- no explicit cavity recirculation, transverse jets, boundary-layer/shock-train model, finite-rate chemistry, ignition, mixing, or species transport;
- the P11.2A isolator-length experiment demonstrates a limitation of the cold-flow model rather than experimental sensitivity;
- no authoritative LBW/YBW discrimination criterion has yet been frozen.
