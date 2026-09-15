# P11.2 Authoritative Source and Baseline Gap Report

## Status

`P11.2A FORMALLY VERIFIED — SOURCE-BACKED PUBLIC COLD-FLOW SURROGATE`

`P11.2B SOFTWARE / GEOMETRY / FRICTION-CONVENTION INFRASTRUCTURE READY — FORMAL HEATED CASE STILL EVIDENCE-GATED`

P11.2 originally mixed two different problems: solver capability and physical-case evidence. The solver capability problem is closed. The project can accept a source-backed axial line heat-release law `Qdot'(x) [W/m]`, map it conservatively into the energy equation, construct the Liu model-B study geometry, apply a source-traceable wall-friction convention, and enforce formal-case provenance rules. The remaining blockers are case-specific experimental inputs and source identity, not missing numerical plumbing.

The public P11.2A surrogate does **not** replace the teacher-designated Cao Ruifeng material and must not be cited as a Cao-thesis reproduction.

## Evidence classification policy

Every quantity entering a formal case is classified as one of:

- `SOURCE`: explicitly reported by the cited source;
- `DERIVED`: calculated from source quantities by a stated equation;
- `SOURCE_CORROBORATED_INTERPRETATION`: a necessary interpretation supported by multiple traceable sources but not stated verbatim by the primary source;
- `MODEL ASSUMPTION`: a declared reduction that is not claimed as source fact;
- `NUMERICAL CONTROL`: grid, CFL, tolerance, iteration limit, and similar solver settings;
- `DEFERRED / NOT_FROZEN`: evidence is still insufficient.

No missing physical input is filled merely because a value appears plausible.

## Source inventory

| ID | Source | Role in P11.2B |
| --- | --- | --- |
| SRC01 | teacher instruction screenshots | establishes Cao Ruifeng material as project-designated reference |
| SRC02 | Cao Ruifeng doctoral thesis (2016) | inlet / thermodynamic / combustion-mode lineage evidence |
| SRC03 | Cao Ruifeng master's thesis (2011) | one-dimensional modelling lineage |
| SRC04 | *Theory and Application of Hypersonic Aerodynamic Layout*, Ch. 11 | generalized quasi-1D source-term semantics |
| SRC05 | repository P3–P10 verification | numerical implementation authority |
| SRC06 | Li et al. (2025), DOI `10.7527/S1000-6893.2024.30944` | P11.2A public cold-flow surrogate |
| SRC07 | Cao et al. (2020), DOI `10.1016/j.ast.2019.105590` | Cao-lineage mode-transition / heat-release context |
| SRC08 | Jin et al. (2026), DOI `10.1016/j.combustflame.2026.114876` | Eq. 7, Eq. 8, Eq. 11 and independent Liu model-B validation |
| SRC09 | Tian et al. (2012), DOI `10.2514/6.2012-5833` | independent pressure-fitted heat-release / TDLAS validation context |
| SRC10 | Liu et al. (2019), DOI `10.2514/1.J058391` | primary axisymmetric model-B experiment reused by Jin |
| SRC11 | Liu et al. (2019), DOI `10.2514/6.2019-1681` | same-program geometry / total-length cross-check |
| SRC12 | Liu & Yao (2021), DOI `10.2514/6.2021-3536` | same-geometry numerical dimensional cross-check only |
| SRC13 | Liu et al. (2019), DOI `10.2514/1.J058204` | primary same-program 2 deg / 5 deg divergence family |
| SRC14 | Ma et al. (2021), DOI `10.1155/2021/7525824` | peer-reviewed `wall divergent angle` terminology cross-check |
| SRC15 | A.H. Shapiro (1953), *The Dynamics and Thermodynamics of Compressible Fluid Flow*, Vol. 1 | friction-coefficient definition explicitly cited by Jin Eq. 9–10 lineage |

Machine-readable evidence records include:

- `cases/studies/data/p11_2b_heat_release_model_source.json`
- `cases/studies/data/p11_2b_jin_liu_condition_discrepancy.json`
- `cases/studies/data/p11_2b_liu_model_b_geometry_source.json`
- `cases/studies/data/p11_2b_liu_angle_convention_source.json`
- `cases/studies/data/p11_2b_jin_validation_applicability.json`
- `cases/studies/data/p11_2b_jin_friction_convention_source.json`

The generated readiness state is tracked in `artifacts/p11_2b/p11_2b_readiness.json` and is regression-tested against the evidence records.

## P11.2A closure

P11.2A uses the SRC06 public geometry/inflow as a reduced, non-reactive physical-scale surrogate. Fuel, burn, friction, and wall heat are disabled. The cavity is not silently converted into extra one-dimensional core area.

Formal acceptance evidence:

- source/code SHA: `9032d5e8304ac6022ba7c4f185b170c6ba9cddd2`;
- Test run `34880624298`: `801 passed in 47.01 s`;
- dedicated formal run `34880624357`: success;
- runtime artifact `10362683519`;
- artifact SHA-256 `364ea31e3395e0080ad7a426f20e4fc53dc438efb4b53147ed3dcc3fcb759789`.

The baseline and `L1=560 -> 280 mm` cases converge. After removal of the expected coordinate shift, their overlapping cold-flow fields agree at about `1e-10` relative. This is useful negative evidence: the source-free inviscid constant-area isolator contains no mechanism for the experimental reactive isolator-length sensitivity.

## P11.2B solver / closure capability

The production solver accepts direct `heat_release_rate_per_length [W/m]`, maps it as `Qdot'/A [W/m^3]`, and adds energy only. It is mutually exclusive with the burned-fuel/LHV path so that the same thermal power cannot be counted twice.

The P11.2B study layer implements:

- Jin Eq. 7 normalized quasi-Gaussian heat release;
- Jin Eq. 8 asymmetric quasi-Gaussian heat release;
- exact finite-volume normalization from shape to a caller-supplied total power;
- Jin Eq. 11 cumulative total-temperature diagnostic;
- total-enthalpy-ratio diagnostics that retain dimensionless evidence without inventing an absolute `J/kg` scale;
- a source-traceable Liu model-B `AreaProfile`;
- a source-backed mapping from Jin/Shapiro wall-friction coefficient `Cf` to the repository Darcy friction factor.

Formal case promotion still requires the input evidence to belong to one declared physical condition.

## Liu model-B geometry closure

The axial geometry no longer depends on low-resolution figure digitization.

SRC10 places station 3 / the most-upstream injector at `291.4 mm` downstream of the inlet lip. SRC12 independently gives an inlet length `37.43 mm`; adding the SRC10 `254 mm` isolator gives

`37.43 + 254 = 291.43 mm`,

only `0.03 mm` from the SRC10 station-3 coordinate. A second identity closes exactly:

`254 mm isolator + 42 mm injector-to-cavity-leading-edge distance = 296 mm`,

matching the SRC12 constant-diameter length to the cavity leading edge.

The cavity closeout ramp has the derived axial projection

`11 / tan(22.5 deg) = 26.55635 mm`.

Therefore the model-B constant-area replacement module has axial length

`35 + 26.55635 = 61.55635 mm`,

and the divergence begins

`42 + 61.55635 = 103.55635 mm`

downstream of station 3.

The study coordinate is consequently frozen as:

- station 3 / injector: `x=0`;
- divergence start: `x=0.10355635 m`;
- station 4 / combustor exit: `x=0.46055635 m`;
- SRC10 inlet-referenced coordinate transform: `x_solver = x_source - 0.2914 m`.

The complete reconstruction closes the independently reported approximately `752 mm` model lengths to sub-millimetre residuals. These residuals are consistency checks, not fitted parameters.

Thus **axial coordinate mapping is resolved**.

## Radial area-law interpretation

The primary Liu text reports a `2 deg cone angle` but the recovered wording does not literally define half-angle versus full included angle. That distinction materially changes `A(x)`.

For the source-backed `35 mm` diameter and `357 mm` diverging length:

- `2 deg` as wall angle gives derived `A_exit/A_inlet ≈ 2.9323`;
- `2 deg` as full included angle gives derived `A_exit/A_inlet ≈ 1.8390`.

SRC13 establishes the same-program `2 deg / 5 deg` experimental divergence family. SRC14 explicitly describes the corresponding Liu-family parameter as **wall divergent angle**. The study layer therefore interprets `2 deg` as the wall angle measured from the centerline.

This is classified `SOURCE_CORROBORATED_INTERPRETATION`, not a verbatim primary-source half-angle statement. The resulting radius and area are `DERIVED`. A higher-authority primary figure or author dataset must override this interpretation if contradictory.

Thus **the study-layer radial area law is resolved**, while its evidence class remains explicit.

## Jin–Liu validation-condition conflict

Jin describes the independent validation as **model B, `phi=1.04`, experimental `M4=2.27`**.

Liu Table 2 gives:

- model B, C2H4, `phi=1.03`: `M4=2.27`, `pt4/pt3=0.39`, `Ht4/Ht3=1.16`;
- model A, C2H4, exactly `phi=1.04`: `M4=1.76`, `pt4/pt3=0.24`, `Ht4/Ht3=1.29`.

Therefore this is not treated as a harmless decimal-rounding discrepancy. Matching Jin by equivalence ratio would switch configurations; matching by `M4=2.27` points to Liu model B at `phi=1.03`. The status remains `UNRESOLVED_CROSS_MODEL_EQUIVALENCE_RATIO_CONFLICT` until a higher-specificity source identifies the actual Fig. 14 run.

## Jin/Shapiro friction convention closure

Jin Sec. 3.2.3 Eqs. (9)–(10) retain the differential friction term `4 Cf dx / D` and explicitly cite Shapiro as the equation source. Shapiro defines the duct friction coefficient as wall shear stress divided by the dynamic head:

`Cf = tau_w / (0.5 rho u^2)`.

For a circular / hydraulic-diameter duct, wall force per volume is

`S_m = -(P/A) tau_w = -4 tau_w / D_h`,

so substitution gives

`S_m = -2 Cf rho u |u| / D_h`.

The repository production wall source is explicitly

`S_m = -0.5 f_D rho u |u| / D_h`,

where `f_D` is the Darcy friction factor. Equating the same wall-force term therefore yields the **derived convention mapping**

`f_D = 4 Cf`.

This is stored in `p11_2b_jin_friction_convention_source.json` and implemented in `p11_2b_friction_convention.py`. The mapping is classified `DERIVED_CONVENTION_MAPPING` because it follows from source definitions plus the repository's explicit source equation; it is not inferred from the symbol name alone.

This closes the old **coefficient-convention** blocker. It does **not** supply the numerical `Cf` used by Jin in Fig. 14. That numerical value remains `NOT_FROZEN`.

## Jin simple-model applicability

Jin Eqs. (9)–(11) require `A(x)`, `Tt(x)`, `gamma`, `Cf`, a duct diameter/scale, axial heat release, mass flow, `cp`, and initial stagnation temperature. Jin further states the simple validation assumes supersonic and separation-free flow so that the `M=1` singularity, shock-train effects, and separation-induced area uncertainty can be excluded from that reduced model.

Therefore a formal reproduction must:

- report `min(M)>1` over the comparison domain;
- not claim that the one-dimensional state proves absence of boundary-layer separation;
- use a source-backed station-3 boundary state;
- use the actual Fig. 14 numerical `Cf` or direct source evidence that friction was neglected;
- convert any recovered Jin/Shapiro `Cf` using the now-frozen `f_D=4Cf` convention mapping.

## Formal-case gate and current blockers

`cases/studies/p11_2b_case_gate.py` accepts one of two complete heat-release evidence paths:

1. source-backed normalized Eq. 8 shape parameters plus a matching absolute energy scale from the same condition; or
2. an already-absolute, traceable `x [m] / Qdot'(x) [W/m]` profile, with no second power scaling.

The formal-case list remains empty, so formal promotion is still blocked.

The preferred Jin–Liu model-B chain now has **five bounded physical-evidence blockers**:

1. **condition identity** — resolve Jin model-B `phi=1.04` versus Liu model-B `phi=1.03` / model-A `phi=1.04`;
2. **heat-release shape** — recover the exact Fig. 14 profile or fitted `Q_m, x_i, x_m, x_c, k` values with traceable coordinates;
3. **absolute energy scale** — recover the measured stagnation-enthalpy increment and matching mass flow / station-3 absolute enthalpy, or an already-absolute `Qdot'(x)` table;
4. **station-3 boundary state** — recover the complete inlet primitive / total state used in the external model-B calculation;
5. **numerical wall-friction coefficient** — recover the actual `Cf` used in Fig. 14, or direct evidence that it was zero / neglected.

Three previously open infrastructure/evidence requirements are now explicitly closed:

- axial source-to-solver coordinate mapping — `RESOLVED_SOURCE_BACKED`;
- study-layer radial area law — `RESOLVED_SOURCE_CORROBORATED_INTERPRETATION`;
- Jin/Shapiro `Cf` to repository Darcy factor — `RESOLVED_DERIVED_FROM_SOURCE_DEFINITION`, `f_D=4Cf`.

The readiness artifact intentionally keeps formal promotion blocked even though those three subproblems are closed.

## Confirmed Cao-thesis evidence retained

SRC02 still supplies locatable records including an idealized Chapter-2 inlet case, Chapter-3 `gamma=1.4` and kerosene `Hf=42,000 kJ/kg`, and Chapter-5 isolator-entry conditions for several ground-test flight-Mach settings. These values are retained only in their original case contexts. They do not authorize mixing unrelated thesis cases into a synthetic baseline.

## Next evidence priority

The highest-value next step is still recovery of the **exact Jin Fig. 14 supporting data**: condition identity, fitted heat-release shape, absolute energy scale, station-3 state, and numerical `Cf`. Publisher supplementary material or an author-provided table is preferred.

Until then the project will not use untracked plot digitization, infer mass flow from nominal geometry, set `Cf=0` by analogy with a different Liu derivation, manufacture a station-3 state, or cross-mix operating conditions merely to make a heated case run.

The teacher-designated Cao material remains the preferred lineage for the ultimate LBW/YBW mode-transition stage. No formal reactive curve or combustion-mode classification is promoted until one evidence chain passes the gate.
