# P11.2A Public Surrogate Cold-Flow Baseline

## Status

`IMPLEMENTED AND FORMALLY VERIFIED`

P11.2A is the first project study that combines literature-backed physical scale and inflow conditions with the accepted quasi-one-dimensional solver. It is deliberately **non-reactive**. It is not a Cao Ruifeng thesis reproduction, an experimental validation, or an LBW/YBW classifier.

Formal evidence is frozen at:

- code SHA: `9032d5e8304ac6022ba7c4f185b170c6ba9cddd2`
- standard Test workflow: run `34880624298`, `801 passed in 47.01 s`
- dedicated P11.2A workflow: run `34880624357`, success
- runtime artifact: `10362683519`
- artifact SHA-256: `364ea31e3395e0080ad7a426f20e4fc53dc438efb4b53147ed3dcc3fcb759789`
- tracked evidence record: `artifacts/p11_2a/p11_2a_formal_evidence.json`

## Source and evidence boundary

Primary reference:

> Fan Li, Mingjiang Liu, Mingbo Sun, Guoyan Zhao, Guangwei Ma, Chenxiang Zhao. *Sensitive factors of ethylene combustion heat release under different combustion modes in scramjet engine*. Acta Aeronautica et Astronautica Sinica, 2025, 46(4):130944. DOI: 10.7527/S1000-6893.2024.30944.

Tracked source ledger:

`cases/studies/data/p11_2_public_surrogate_source.json`

The paper provides the inlet total state and Mach number, vitiated-air composition, dimensioned geometry, total ethylene operating points, and published geometry/injection changes. P11.2A uses only the parts that can be mapped without inventing reactive closure data.

| Quantity | Value | Units | Status | Locator / use |
| --- | ---: | --- | --- | --- |
| Inflow Mach | 2.52 | 1 | SOURCE | Table 1 |
| Inflow total temperature | 1650 | K | SOURCE | Table 1 |
| Inflow total pressure | 1.34e6 | Pa | SOURCE | Table 1 |
| Baseline isolator length `L1` | 0.560 | m | SOURCE | Table 2 |
| Pre-cavity length `L2` | 0.140 | m | SOURCE | Table 2 |
| Combustor length `L3` | 0.490 | m | SOURCE | Table 2 |
| Width `W` | 0.050 | m | SOURCE | Table 2 |
| Heights `H1`, `H2` | 0.035, 0.042 | m | SOURCE | Table 2 |
| Short-isolator level | 0.280 | m | SOURCE | Table 4 |
| `gamma` | 1.4 | 1 | MODEL ASSUMPTION | existing gas model |
| `R` | 287 | J/(kg K) | MODEL ASSUMPTION | existing gas model |
| Static inlet `T,p,rho,u` | computed | SI | DERIVED | source total state + perfect-gas model |
| Core-flow `A(x)` | computed | m2 | MODEL ASSUMPTION / DERIVED | mapping below |
| Fuel/source profiles | unavailable | — | DEFERRED | P7/P8 reactive closure not activated |

## Inlet derivation

The source reports total conditions while the existing `supersonic-inflow` boundary requires a primitive state. The study therefore computes

\[
T = \frac{T_0}{1 + \frac{\gamma-1}{2}M^2},
\]

\[
p = \frac{P_0}{\left(1 + \frac{\gamma-1}{2}M^2\right)^{\gamma/(\gamma-1)}},
\]

\[
\rho = \frac{p}{RT}, \qquad
u_{x} = M\sqrt{\gamma RT}.
\]

For the frozen inputs this gives approximately `T=726.85 K`, `p=76.03 kPa`, `rho=0.36445 kg/m3`, and `u=1361.84 m/s`. These are **model-derived**, not measured static quantities from the paper.

## Reduced-order geometry mapping

The source does not provide a solver-ready quasi-1D station table or a one-dimensional representation of cavity recirculation. The explicit P11.2A mapping is therefore:

1. `H=H1` through the isolator and pre-cavity main-flow passage;
2. `H` varies linearly from `H1` to `H2` over `L3`;
3. width remains `W`;
4. `A(x)=W H(x)`;
5. cavity depth/volume is retained as source metadata and is **not** added to core-flow area.

This is a documented reduced-order assumption, not a digitization of Fig. 2.

## Physics and numerical controls

The case uses `supersonic-inflow`, `supersonic-outflow`, Steger-Warming, CFL `0.2`, residual tolerance `1e-8`, `dx≈0.005 m`, and the existing steady SSP-RK3 path. Darcy friction, wall heat transfer, fuel injection, and prescribed combustion are all disabled. No clipping, smoothing, automatic boundary switching, or hidden source term is used.

## Formal baseline result

Case `P11A-PUBLIC-COLD-BASE` (`L1=0.560 m`) formally converged:

| Metric | Result |
| --- | ---: |
| cells | 238 |
| steps | 1779 |
| final pseudo-time | 9.28605e-4 s |
| final residual | 9.83971e-9 |
| Mach in / out | 2.5200 / 2.71312 |
| pressure in / out | 76.026 / 56.388 kPa |
| temperature in / out | 726.847 / 667.421 K |
| mass flow in / out | 0.868562 / 0.867824 kg/s |
| mass-flow relative span | 1.01872e-3 |

The solution stays rightward and supersonic, so the selected outlet boundary remains applicable. Pressure and temperature decrease while Mach increases through the expanding core-flow mapping, which is qualitatively consistent with the declared inviscid supersonic-area model.

The roughly `0.10%` cell-centred mass-flow span is recorded as a discretization diagnostic, not hidden behind a new acceptance threshold. P10 already establishes the solver's conservation and grid-convergence properties; P11.2A does not redefine those gates.

## Isolator-length OFAT result and model-scope finding

Case `P11A-ISO-L280` (`L1=0.280 m`) also formally converged in 1772 steps with residual `9.65361e-9`. Its outlet state is effectively the same as the baseline.

After shifting the baseline axial coordinate by `0.280 m` and comparing the overlapping fields, maximum relative differences are approximately:

- density: `6.50e-11`
- velocity: `2.96e-11`
- pressure: `8.35e-11`
- temperature: `2.94e-11`
- Mach: `4.56e-11`
- mass flow: `5.08e-11`

This near-identity is **expected from the current model**, not a failed calculation. In an inviscid, source-free, constant-area isolator, changing only the length adds or removes uniform duct before the same downstream area variation. The present P11.2A equations therefore contain no mechanism by which isolator length alone can reproduce the experimental reactive sensitivity reported in Table 4.

This is an important negative result: the experiment's isolator-length sensitivity cannot be interpreted with the current cold-flow idealization. Friction, boundary-layer/shock-train interaction, combustion heat release, and other omitted mechanisms are precisely the physics that P11.2A does not claim to represent.

Accordingly, `L1=560 -> 280 mm` is retained as a **source-backed geometry OFAT and model-scope diagnostic**, not as a validated prediction of the paper's combustion trend.

## Deferred Table-4 factors

- injection distance is not meaningful while P7 injection is disabled;
- cavity depth has no approved one-dimensional cavity-area closure;
- throat-size values are source-backed, but the exact local core-flow mapping must be frozen before a formal second geometry OFAT is allowed.

The project deliberately does not manufacture a second sensitivity result merely to increase case count.

## Reproducibility

Run:

```bash
python cases/studies/p11_2a_public_surrogate.py --formal
```

The dedicated workflow `.github/workflows/p11_2a_public_surrogate.yml` executes focused tests, both formal cases, and uploads runtime results. Per-case artifacts include `case_summary.json`, `profile.csv`, `residual.csv`, and pressure/temperature/Mach/mass-flow plots.

## Validity scope

The highest permitted claim is:

> **Physical-scale public surrogate, non-reactive reduced-order quasi-one-dimensional calculation using source-backed dimensions and inflow total conditions.**

It is not experimental validation, a reactive-engine reproduction, a Cao-thesis reproduction, or an LBW/YBW mode prediction.

## Remaining blockers for P11.2B

A stronger reactive baseline still requires an evidence-backed or explicitly approved closure for at least the axial heat-release / burned-fuel distribution. A full mass-addition treatment additionally requires axial fuel mass-source distribution, fuel axial velocity, and fuel specific total enthalpy. These quantities must not be invented merely to obtain a reactive curve.
