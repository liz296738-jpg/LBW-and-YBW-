# P11 Parametric Study Plan

## Scientific scope

P11.1 verifies study infrastructure using a controlled numerical similarity experiment. Its scientific claim level is `framework-only`. It is not a calibrated engine study, an experimental validation, an LBW/YBW classification, or a mode-transition prediction. `LBW` and `YBW` remain literal project labels until authoritative definitions and a criterion are frozen.

Numerical controls, physical inputs, and framework controls are separate categories. P11.1 sweeps only the dimensionless framework control `stagnation_pressure_scale = 0.8, 1.0, 1.2`; these values must not be interpreted as engine operating conditions.

## Stage breakdown

- P11.1 Parametric Study Foundation + controlled similarity pilot — formal run pending.
- P11.2A Source-backed public surrogate geometry/inflow baseline + physical OFAT — source evidence available; implementation may proceed.
- P11.2B Reactive physical baseline — evidence-gated pending axial injection/burn or heat-release closure.
- P11.3 Literature/teacher-defined LBW/YBW criterion + regime/transition map — planned.
- P11.4 Integrated LBW/YBW comparison, robustness, interpretation, and study closure — planned.

P11.2A uses the public surrogate source recorded in `cases/studies/data/p11_2_public_surrogate_source.json`. It must never be described as a Cao-thesis reproduction. P11.2B remains reserved for a source-backed reactive case.

## P11.1 controlled pilot

The pilot reuses the verified smooth quasi-one-dimensional isentropic family with `L=1 m`, `N=80`, linear face area from `1.0` to `1.2 m²`, `gamma=1.4`, `R=287 J/(kg K)`, and `T0=500 K`. Stagnation pressure is `300000 Pa × stagnation_pressure_scale`. Steger-Warming, CFL `0.2`, residual tolerance `1e-8`, maximum pseudo-time `0.10 s`, and `200000` maximum steps are fixed numerical controls.

The formal matrix contains `SUB-SW-P080`, `SUB-SW-P100`, `SUB-SW-P120`, `SUB-SW-P100-REPEAT`, `SUP-SW-P080`, `SUP-SW-P100`, and `SUP-SW-P120` in that order. The repeat differs only by case ID and verifies deterministic reproducibility.

Wall friction, wall heat flux, fuel injection, and prescribed combustion inputs are inactive. Injection and prescribed burn distributions remain independent inputs; the study layer adds no inventory, efficiency, mixing, ignition, chemistry, or species model.

With geometry, total temperature, reference Mach, and gas fixed, the controlled family expects invariant velocity, temperature, and Mach; pressure, density, and mass flow scale with total pressure. Relative L1 and Linf differences after the defined scaling must each be at most `1e-6`. These are framework-verification relations, not physical sensitivity claims about an engine.

## P11.2A public surrogate policy

The surrogate source is Li et al. (2025), *Sensitive factors of ethylene combustion heat release under different combustion modes in scramjet engine*, DOI `10.7527/S1000-6893.2024.30944`.

The source provides:

- inlet Mach `2.52`, total temperature `1650 K`, total pressure `1.34 MPa`, and vitiated-air composition;
- dimensioned engine geometry in Fig. 2 / Table 2;
- total ethylene flow and injector-module operating points in Table 3;
- source-supported OFAT levels in Table 4 for isolator length, injection distance, cavity depth, and throat size.

P11.2A may freeze only inputs that are directly locatable or transparently derived from them. The initial accepted scope is a quasi-1D **core-flow surrogate** with reactive sources disabled unless an axial source distribution and the additional P7/P8 inputs are separately justified.

The current perfect-gas model may retain `gamma=1.4` and `R=287 J/(kg K)` only as explicit model assumptions. The source composition is evidence metadata, not species-transport input to the present solver.

## Mode-classification policy

`lbw_ybw_classification_defined` remains false; `mode_criterion_id` and `mode_label` remain null. Mach extrema, sonic fractions, sonic margin, and crossing count are diagnostics only and do not classify LBW or YBW.

The experimental paper's verbal combustion-mode observations may be used as comparison context, but they are not automatically adopted as the repository's formal LBW/YBW criterion. P11.3 must freeze that criterion separately.

## P11.2 input status

| Required input | P11.2A surrogate | P11.2B reactive/Cao track |
| --- | --- | --- |
| Engine/combustor axial dimensions | SOURCE AVAILABLE (SRC06) | NOT FROZEN for exact Cao reproduction |
| Area profile `A(x)` | PARTIAL — dimensions available; quasi-1D mapping must be explicit | NOT FROZEN |
| Hydraulic diameter `D_h(x)` | DERIVABLE only if rectangular-core mapping is approved | NOT FROZEN |
| Inlet condition definition | SOURCE AVAILABLE | Candidate values only |
| Inlet total/static pressure | TOTAL SOURCE AVAILABLE; static derivable under model assumptions | Candidate values only |
| Inlet total/static temperature | TOTAL SOURCE AVAILABLE; static derivable under model assumptions | Candidate values only |
| Inlet Mach or velocity | Mach SOURCE AVAILABLE; velocity derivable under model assumptions | Candidate values only |
| Outlet/back-pressure treatment | NOT SOURCE-FROZEN; supersonic-outflow may be tested only if physically applicable | NOT FROZEN |
| Wall friction factor/model input | DISABLED unless separately sourced | NOT FROZEN |
| Wall heat-flux/thermal condition | DISABLED unless separately sourced | NOT FROZEN |
| Total fuel mass flow | SOURCE AVAILABLE (Table 3) | Partial |
| Fuel-injection axial distribution | NOT FROZEN | NOT FROZEN |
| Fuel axial velocity | NOT FROZEN | NOT FROZEN |
| Fuel specific total enthalpy | NOT FROZEN | NOT FROZEN |
| Prescribed burned-fuel distribution / heat release | NOT FROZEN | NOT FROZEN |
| Fuel LHV | NOT REQUIRED while combustion disabled | Cao kerosene value available but insufficient alone |
| Physical OFAT non-baseline levels | SOURCE AVAILABLE (Table 4) | NOT FROZEN |
| Authoritative LBW/YBW criterion | NOT FROZEN | NOT FROZEN |
| Experimental comparison observables | Wall-pressure / heat-release trends available | Partial |

## P11.2A permitted OFAT factors

Source-supported factor levels may be created only where the quasi-1D mapping remains meaningful:

- isolator length `560 -> 280 mm`;
- injection distance `21 -> 42 mm` only after an injection-source representation exists;
- cavity depth `21 -> 10 mm` only after the chosen quasi-1D cavity/core-area mapping is documented;
- throat size `Hc 21 -> 16.8 mm`, corresponding `H 35 -> 39.2 mm`, after the local area mapping is frozen.

Until then, the safest first formal P11.2A study is the dimensioned inflow/geometry baseline plus the isolator-length variation, with reactive and wall sources disabled.

## Metric Metadata Contract

P11.1 writes an explicit, fixed metadata record for every reported metric: symbol, units, definition, interpretation, hard-gate status, and scope. P11.2 must preserve the same provenance discipline and add, for every physical input, source ID, locator, raw value, SI conversion, and derivation status (`source`, `derived`, or `model-assumption`).

Sonic fractions, minimum sonic margin, sonic-crossing count, and Mach-extremum positions remain diagnostic only. They do not define a hard scientific gate and are not an LBW/YBW classifier.

## Limitations

- P11.2A is a literature-backed surrogate, not a reproduction of the teacher-designated Cao case.
- The solver is quasi-one-dimensional and calorically perfect; the experimental vitiated-air composition is not species-resolved.
- Cavity recirculation, transverse jets, finite-rate chemistry, mixing, ignition, and species transport are not represented explicitly.
- Total fuel flow alone is not enough to activate the existing P7/P8 source models without axial distribution, fuel velocity/enthalpy, and prescribed burn/heat-release information.
- No LBW/YBW criterion is frozen yet.
