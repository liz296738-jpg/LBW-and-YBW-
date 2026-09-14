# P11.2 Authoritative Source and Baseline Gap Report

## Status

`P11.2A FORMALLY VERIFIED — SOURCE-BACKED PUBLIC COLD-FLOW SURROGATE`

`P11.2B HEAT-RELEASE INTERFACE/CLOSURE IMPLEMENTED — FORMAL HEATED CASE STILL PARAMETER-GATED`

The original P11.2 blocker was an absence of enough source-grounded geometry and axial source data to construct a complete reactive baseline without inventing inputs. P11.2A solved the geometry/inflow part with a public physical-scale cold-flow surrogate. P11.2B has now solved the **software-interface and heat-release functional-form** part. The remaining blocker is narrower: one internally consistent published case must supply or support the absolute heat addition and matching axial shape parameters.

The public surrogate does **not** replace the teacher-designated Cao Ruifeng material and must not be cited as a Cao-thesis reproduction.

## Source inventory

| ID | Source | Authority / role | Current use |
| --- | --- | --- | --- |
| SRC01 | teacher instruction screenshots | project instruction | establishes the Cao Ruifeng material as teacher-designated reference |
| SRC02 | Cao Ruifeng doctoral thesis (2016) | project-designated thesis | candidate inlet records, kerosene LHV, combustion-mode context |
| SRC03 | Cao Ruifeng master's thesis (2011) | project-designated modelling reference | one-dimensional modelling context; no complete solver-ready case frozen yet |
| SRC04 | *Theory and Application of Hypersonic Aerodynamic Layout*, Ch. 11 | project technical reference | generalized one-dimensional source-term semantics |
| SRC05 | repository solver / P3–P10 verification evidence | implementation authority | accepted numerical capability |
| SRC06 | Li et al. (2025), DOI `10.7527/S1000-6893.2024.30944` | peer-reviewed experiment | P11.2A geometry, inflow, operating points, Table-4 factors |
| SRC07 | Cao et al. (2020), DOI `10.1016/j.ast.2019.105590` | Cao-lineage one-dimensional study | confirms heat-release distribution as a mode-transition influence |
| SRC08 | Jin et al. (2026), DOI `10.1016/j.combustflame.2026.114876` | experimental heat-release / 1-D closure paper | Eq. 7, Eq. 8, Eq. 11 closure forms and high-enthalpy validation context |
| SRC09 | Tian et al. (2012), DOI `10.2514/6.2012-5833` | modified quasi-1D experiment/model paper | pressure-fitted heat-release distributions checked with TDLAS |

Machine-readable ledgers:

- `cases/studies/data/p11_2_public_surrogate_source.json`
- `cases/studies/data/p11_2b_heat_release_model_source.json`

## P11.2A closure

SRC06 supplies source-backed inflow, geometry, fuel operating points, and Table-4 factor levels. P11.2A freezes an explicit reduced-order core-flow mapping, keeps cavity recirculation outside `A(x)`, and uses the existing perfect-gas assumptions `gamma=1.4`, `R=287 J/(kg K)`. Fuel, burn, wall-friction, and wall-heat sources remain disabled.

Formal acceptance:

- source/code SHA: `9032d5e8304ac6022ba7c4f185b170c6ba9cddd2`
- standard Test run `34880624298`: `801 passed in 47.01 s`
- dedicated formal run `34880624357`: success
- runtime artifact `10362683519`
- artifact SHA-256 `364ea31e3395e0080ad7a426f20e4fc53dc438efb4b53147ed3dcc3fcb759789`

The baseline and `L1=560 -> 280 mm` cases both converge. After removing the expected coordinate shift, their overlapping cold-flow fields agree to about `1e-10` relative. This demonstrates that the inviscid source-free constant-area isolator contains no mechanism for the experimental reactive isolator-length sensitivity.

## P11.2B gap that is now closed

The production solver now accepts a direct line heat-release distribution `Qdot'(x) [W/m]`, maps it conservatively to `Qdot'/A [W/m^3]`, and adds energy only. It is mutually exclusive with the existing burned-fuel/LHV energy path to prevent double counting.

Regression tests establish that:

- zero direct heat release preserves the legacy solver path;
- `Qdot'/A` affects only the conservative energy source;
- the direct path is numerically equivalent to the existing burned-fuel/LHV path when both represent the same `Qdot'(x)`;
- invalid/nonfinite/negative profiles are rejected;
- transient propagation of the direct path is covered.

Commit `e36cfb124f9bd0a8ddb3be6d548f79a751fdf471` passed GitHub Actions run `34882069673` with `828 passed in 60.67 s` after correcting an old P10.4 test so its production-freeze gate is evaluated at the accepted P10.4 revision rather than incorrectly forbidding all later P11 production changes.

The source-backed closure utilities now include:

- Jin Eq. 7 normalized quasi-Gaussian profile;
- Jin Eq. 8 asymmetric quasi-Gaussian profile downstream of heat-release initiation;
- exact finite-volume scaling from normalized shape to caller-supplied total power;
- Jin Eq. 11 cumulative total-temperature energy integral.

Therefore the project no longer lacks a mathematically defined path from a source-backed heat-release model to the P8 energy equation.

## Evidence recovered from SRC08 and SRC09

SRC08 reports a Mach-2.52, `T0=1650 K`, `P0=1.3 MPa`, ethylene-fueled direct-connected experiment and proposes a quasi-Gaussian one-dimensional heat-release model. Its Eq. 8 is text-recoverable and depends on `Q*_m`, `x_i`, `x_m`, `x_c`, and `k`. Case 10 text reports raw `x_c=98`, `k=5.6`, fit `R^2=0.997`, and cumulative heat fraction `0.92` at `x_c`, but the matching figure-derived `x_i`, `x_m`, coordinate convention, and absolute thermal power are not frozen.

SRC09 supplies four quasi-one-dimensional operating cases with Mach number, total temperature, air mass flow, equivalence ratio, and reported combustion efficiency. It also reports that inferred heat-release distributions were obtained by matching pressure and checked with TDLAS temperature/velocity measurements. However, the accessible text does not explicitly identify the fuel species/LHV for those cases and does not tabulate the fitted axial heat-release profiles. The repository therefore does not convert equivalence ratio + efficiency into an absolute `Qdot` or digitize plotted profiles as if they were tabulated source data.

## Confirmed Cao-thesis evidence retained

SRC02 still provides useful locatable records:

- Chapter 2, Table 2-1: `Ma2=2`, `rho2=0.7736 kg/m^3`, `p2=156.522 kPa`, `T2=705 K`, `u2=1038 m/s`, `k=1.33`, `phi=0.3` for an idealized case;
- Chapter 3, Table 3-2: `gamma=1.4` and kerosene `Hf=42,000 kJ/kg` for that cycle-analysis model;
- Chapter 5, Table 5-1: isolator-entry Mach, pressure, total temperature, and air mass flow for ground-test flight-Mach settings 4–7.

These are evidence records, not permission to combine unrelated values into an artificial formal case.

## Primary remaining blocker for a formal P11.2B run

The minimum missing pair is now:

1. **absolute total heat addition** (or a source-backed derivation of it), and
2. **matching axial shape parameters** for the same operating condition and geometry.

A formal heated case cannot be created by mixing the P11.2A geometry, a Jin shape from another apparatus, and a thermal power inferred from an unrelated fuel case while calling the result a reproduction. Such combinations may later be used only as explicitly labelled synthetic sensitivity studies, not as validation baselines.

If P7 fuel mass addition is also activated, further inputs remain necessary:

- axial fuel mass-source distribution;
- fuel axial velocity;
- fuel specific total enthalpy.

These are **not** required for a minimal prescribed-energy P11.2B surrogate because the direct `Qdot'(x)` path intentionally adds no mass or momentum.

## Additional deferred physics / mapping issues

- cavity depth cannot become a quasi-1D area change without a documented reduced-order cavity closure;
- injection-distance sensitivity is not meaningful without injection representation;
- shock-train / separation effects become important as heat release drives Mach toward unity and are not yet part of the P11.2A core model;
- wall friction and wall heat transfer need source-backed or explicitly approved closure values if enabled;
- P11.3 still requires authoritative definitions of the project's `LBW` / `YBW` labels and a discrimination criterion.

## Next development decision

Continue searching the Cao-lineage/public literature for a complete internally consistent heated case. Priority is a case that supplies geometry/inflow, an absolute exit enthalpy or total-temperature rise (or fuel/LHV/efficiency sufficient to derive it), and axial heat-release-shape parameters.

Until that evidence is recovered, P11.2B infrastructure may be verified and improved, but no formal reactive curve will be promoted to project evidence.
