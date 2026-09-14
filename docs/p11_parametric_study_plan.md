# P11 Parametric Study Plan

## Scientific scope

P11.1 verifies study infrastructure using a controlled numerical similarity experiment. Its scientific claim level is `framework-only`. It is not a calibrated engine study, an experimental validation, an LBW/YBW classification, or a mode-transition prediction. `LBW` and `YBW` remain literal project labels until authoritative definitions and a criterion are frozen.

Numerical controls, physical inputs, and framework controls are separate categories. P11.1 sweeps only the dimensionless framework control `stagnation_pressure_scale = 0.8, 1.0, 1.2`; these values must not be interpreted as engine operating conditions.

## Stage breakdown

- P11.1 Parametric Study Foundation + controlled similarity pilot — formal run pending.
- P11.2 Physical baseline freeze + one-factor physical sensitivities — planned.
- P11.3 Literature/teacher-defined LBW/YBW criterion + regime/transition map — planned.
- P11.4 Integrated LBW/YBW comparison, robustness, interpretation, and study closure — planned.

P11.2–P11.4 are outside the present implementation.

## P11.1 controlled pilot

The pilot reuses the verified smooth quasi-one-dimensional isentropic family with `L=1 m`, `N=80`, linear face area from `1.0` to `1.2 m²`, `gamma=1.4`, `R=287 J/(kg K)`, and `T0=500 K`. Stagnation pressure is `300000 Pa × stagnation_pressure_scale`. Steger-Warming, CFL `0.2`, residual tolerance `1e-8`, maximum pseudo-time `0.10 s`, and `200000` maximum steps are fixed numerical controls.

The formal matrix contains `SUB-SW-P080`, `SUB-SW-P100`, `SUB-SW-P120`, `SUB-SW-P100-REPEAT`, `SUP-SW-P080`, `SUP-SW-P100`, and `SUP-SW-P120` in that order. The repeat differs only by case ID and verifies deterministic reproducibility.

Wall friction, wall heat flux, fuel injection, and prescribed combustion inputs are inactive. Injection and prescribed burn distributions remain independent inputs; the study layer adds no inventory, efficiency, mixing, ignition, chemistry, or species model.

With geometry, total temperature, reference Mach, and gas fixed, the controlled family expects invariant velocity, temperature, and Mach; pressure, density, and mass flow scale with total pressure. Relative L1 and Linf differences after the defined scaling must each be at most `1e-6`. These are framework-verification relations, not physical sensitivity claims about an engine.

## Mode-classification policy

`lbw_ybw_classification_defined` is false; `mode_criterion_id` and `mode_label` are null. Mach extrema, sonic fractions, sonic margin, and crossing count are diagnostics only and do not classify LBW or YBW.

## Inputs required before P11.2

| Required input | Status |
| --- | --- |
| Engine/combustor axial coordinate | NOT FROZEN |
| Area profile `A(x)` | NOT FROZEN |
| Hydraulic diameter `D_h(x)` | NOT FROZEN |
| Inlet condition definition | NOT FROZEN |
| Inlet total/static pressure | NOT FROZEN |
| Inlet total/static temperature | NOT FROZEN |
| Inlet Mach or velocity | NOT FROZEN |
| Outlet/back-pressure treatment | NOT FROZEN |
| Wall friction factor or model | NOT FROZEN |
| Wall heat-flux/thermal condition | NOT FROZEN |
| Fuel-injection axial distribution | NOT FROZEN |
| Fuel axial velocity | NOT FROZEN |
| Fuel specific total enthalpy | NOT FROZEN |
| Prescribed burned-fuel distribution or approved closure | NOT FROZEN |
| Fuel LHV | NOT FROZEN |
| Authoritative LBW definition | NOT FROZEN |
| Authoritative YBW definition | NOT FROZEN |
| LBW/YBW discrimination criterion | NOT FROZEN |
| Criterion source: teacher, paper, or experiment | NOT FROZEN |
| Experimental or literature comparison observables | NOT FROZEN |

Candidate future physical factors include inlet total pressure, inlet total temperature, outlet static pressure, injection strength, prescribed burn/heat-release strength, wall friction, wall heat transfer, and geometry. Every range remains `NOT FROZEN`; P11.1 does not select one.

## Metric Metadata Contract

P11.1 writes an explicit, fixed metadata record for every reported metric: its symbol, units, definition, interpretation, hard-gate status, and scope. Units are dimensional where applicable (`m`, `Pa`, `K`, `kg/m^3`, `m/s`, and `kg/s`), `count` for sonic-crossing count, and `1` only for dimensionless metrics. Inlet and outlet values for static pressure, static temperature, Mach, mass flow, local total temperature, and reconstructed local total pressure refer to the first and last cell centers, respectively.

Sonic fractions, minimum sonic margin, sonic-crossing count, and Mach-extremum positions are diagnostic only. They do not define a hard scientific gate and are not an LBW/YBW classifier.

## Limitations

- Framework pilot only; not a calibrated engine case.
- No LBW/YBW criterion, real fuel sweep, real heat-release sweep, or experimental comparison.
- Quasi-one-dimensional perfect-gas model with prescribed source models.
- No finite-rate chemistry or species transport.
- P11.1 branch checks apply only to its controlled framework cases and are not global engine-validity rules.
