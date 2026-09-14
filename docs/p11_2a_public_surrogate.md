# P11.2A Public Surrogate Cold-Flow Baseline

## Status

`IMPLEMENTED — FORMAL RUN / CI VERIFICATION PENDING`

P11.2A is the first project study that combines literature-backed physical scale and inflow conditions with the accepted quasi-one-dimensional solver. It is deliberately **non-reactive**. It is not a Cao Ruifeng thesis reproduction, an experimental validation, or an LBW/YBW classifier.

## Purpose

The purpose of this stage is to move from P11.1's framework-only similarity experiment to a traceable physical-scale surrogate while preserving strict evidence boundaries. The case uses dimensions and inflow conditions reported by Li et al. (2025), together with the project's reduced quasi-1D calorically-perfect-gas model.

Primary reference:

> Fan Li, Mingjiang Liu, Mingbo Sun, Guoyan Zhao, Guangwei Ma, Chenxiang Zhao. *Sensitive factors of ethylene combustion heat release under different combustion modes in scramjet engine*. Acta Aeronautica et Astronautica Sinica, 2025, 46(4):130944. DOI: 10.7527/S1000-6893.2024.30944.

Tracked machine-readable source ledger:

`cases/studies/data/p11_2_public_surrogate_source.json`

## Evidence ledger

| Quantity | Value | Units | Status | Source / locator | Transformation / solver use |
| --- | ---: | --- | --- | --- | --- |
| Inflow Mach | 2.52 | 1 | SOURCE | Li et al., Table 1 | Converted with total conditions to primitive inlet |
| Inflow total temperature | 1650 | K | SOURCE | Li et al., Table 1 | Perfect-gas total-to-static relation |
| Inflow total pressure | 1.34e6 | Pa | SOURCE | Li et al., Table 1 | Perfect-gas total-to-static relation |
| Inflow composition | O2 0.2338, H2O 0.0622, CO2 0.1016, N2 0.6024 | mass fraction | SOURCE | Li et al., Table 1 | Retained as metadata; current single-gas solver does not transport species |
| Baseline isolator length L1 | 0.560 | m | SOURCE | Li et al., Table 2 | Axial domain |
| Pre-cavity length L2 | 0.140 | m | SOURCE | Li et al., Table 2 | Axial domain |
| Combustor length L3 | 0.490 | m | SOURCE | Li et al., Table 2 | Axial domain |
| Width W | 0.050 | m | SOURCE | Li et al., Table 2 | `A = W H` |
| H1 | 0.035 | m | SOURCE | Li et al., Table 2 | Core-flow height endpoint |
| H2 | 0.042 | m | SOURCE | Li et al., Table 2 | Core-flow height endpoint |
| Cavity dimensions | Lc=0.070, Dc=0.021, Hc=0.021 | m | SOURCE | Li et al., Table 2 | Metadata only in P11.2A |
| Short-isolator level | 0.280 | m | SOURCE | Li et al., Table 4 | OFAT alternate level |
| `gamma` | 1.4 | 1 | MODEL ASSUMPTION | existing project gas model | Perfect-gas conversion and CFD |
| `R` | 287 | J/(kg K) | MODEL ASSUMPTION | existing project gas model | Perfect-gas conversion and CFD |
| Static `T,p,rho,u` | computed | SI | DERIVED | Table 1 + project gas assumption | Supersonic primitive inlet |
| Main-passage `A(x)` | computed | m2 | MODEL ASSUMPTION / DERIVED | Table 2 endpoints | See geometry mapping below |
| Grid `N, dx` | computed | count, m | NUMERICAL CONTROL | study layer | Approximately constant target `dx` |
| CFL | 0.2 | 1 | NUMERICAL CONTROL | accepted study policy | Explicit pseudo-time advancement |
| Residual tolerance | 1e-8 | 1 | NUMERICAL CONTROL | accepted study policy | Steady convergence gate |
| Fuel-source profile | unavailable | — | DEFERRED | not provided | P7 disabled |
| Fuel axial velocity | unavailable | — | DEFERRED | not provided | P7 disabled |
| Fuel total enthalpy | unavailable | — | DEFERRED | not provided | P7 disabled |
| Burn / heat-release profile | unavailable | — | DEFERRED | not provided | P8 disabled |

## Total-to-static inlet derivation

The source reports total conditions and Mach number. The existing boundary implementation for `supersonic-inflow` requires a primitive state. P11.2A therefore computes, rather than hard-codes, the inlet using the project's calorically perfect gas:

\[
T = \frac{T_0}{1 + \frac{\gamma-1}{2}M^2},
\]

\[
p = \frac{P_0}{\left(1 + \frac{\gamma-1}{2}M^2\right)^{\gamma/(\gamma-1)}},
\]

\[
\rho = \frac{p}{RT}, \qquad
u = M\sqrt{\gamma RT}.
\]

For `M=2.52`, `T0=1650 K`, `P0=1.34 MPa`, `gamma=1.4`, and `R=287 J/(kg K)`, the expected values are approximately `T=726.85 K`, `p=76.0 kPa`, `rho=0.364 kg/m3`, and `u=1362 m/s`. These are **model-derived inputs**, not measured static values from the paper.

## Reduced-order geometry mapping

The source directly provides `L1`, `L2`, `L3`, `W`, `H1`, `H2`, and cavity dimensions. It does not provide a solver-ready quasi-1D station table and it does not define how cavity recirculation volume should be mapped into a one-dimensional core-flow area.

P11.2A therefore uses one explicit and reviewable reduced-order mapping:

1. The isolator and pre-cavity main-flow passage use height `H1`.
2. Across `L3`, the main-passage height varies linearly from `H1` to `H2`.
3. The width is constant at `W`.
4. `A(x) = W H(x)`.
5. Cavity depth and cavity volume are **not added** to the quasi-1D core-flow area.

This mapping is a model assumption built from source-backed endpoints. It must not be cited as a direct digitization of Figure 2. If a future authoritative station table or dimensioned wall-line definition becomes available, this mapping should be replaced and the formal baseline rerun.

## Boundary conditions

The source inflow Mach is supersonic, so the study uses:

- inlet: `supersonic-inflow`, with primitive state derived from the total conditions;
- outlet: `supersonic-outflow`, provided the formal solution remains rightward and supersonic at the outlet.

The study does not silently switch outlet boundary type. If the formal solution violates the applicability condition, the case is a boundary-applicability failure and must be reviewed.

## Disabled physical models

P11.2A intentionally sets:

- Darcy friction factor = 0;
- wall heat flux = 0;
- fuel mass-flow source = 0;
- fuel axial velocity = 0;
- fuel total enthalpy = 0;
- burned-fuel source = 0;
- fuel LHV = `None`.

The published total ethylene flow in Table 3 is not converted into an arbitrary uniform `d(mdot_f)/dx`, and the active injector-module labels are not converted into an unreported per-module split. Those operations require a separately approved reduced-order closure.

## Formal cases

The study script defines:

- `P11A-PUBLIC-COLD-BASE`: `L1 = 0.560 m`;
- `P11A-ISO-L280`: `L1 = 0.280 m`.

The second case is a source-backed one-factor-at-a-time isolator-length variation from Table 4. The grid policy targets approximately constant axial `dx`, so `N` changes when total length changes.

Other Table 4 factors are deferred unless they have an unambiguous mapping into the current non-reactive quasi-1D equations:

- injection distance: deferred because P7 injection is inactive;
- cavity depth: deferred because a one-dimensional cavity-area closure is not defined;
- throat size: source-backed values exist, but the exact reduced-order core-flow mapping must be reviewed before it is promoted to a formal second OFAT factor.

## Reproducibility

The tracked entry point is:

```bash
python cases/studies/p11_2a_public_surrogate.py --formal
```

Formal outputs are written below:

`results/p11_2a_public_surrogate/`

Each completed case writes:

- `case_summary.json`;
- `profile.csv`;
- `residual.csv`;
- pressure, temperature, Mach, and mass-flow PNG profiles.

A non-converged formal case raises an error instead of being silently accepted.

## Validity scope

The highest permitted scientific claim for this stage is:

> **Physical-scale public surrogate, non-reactive reduced-order quasi-one-dimensional calculation using source-backed dimensions and inflow total conditions.**

It is not an experimental validation, a reactive-engine reproduction, a Cao-thesis reproduction, or an LBW/YBW mode prediction.

## Remaining blockers for P11.2B

The reactive baseline remains evidence-gated because the current solver interfaces require quantities not supplied by the public paper as solver-ready axial inputs:

- axial fuel mass-source distribution;
- fuel axial velocity;
- fuel specific total enthalpy;
- burned-fuel or heat-release axial distribution;
- an approved closure connecting total injected fuel to reacted-fuel distribution.
