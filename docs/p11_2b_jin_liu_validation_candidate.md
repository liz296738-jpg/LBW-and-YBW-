# P11.2B Jin–Liu Model-B Validation Candidate

## Status

`PROMISING INDEPENDENT VALIDATION CHAIN — NOT YET A FORMAL CASE`

This is the preferred public independent validation path for P11.2B. Jin et al. (2026) explicitly reuse Liu et al.'s cavity-free axisymmetric model B to test a quasi-Gaussian heat-release model coupled to quasi-one-dimensional flow equations. That is scientifically cleaner than transplanting Jin heat-release parameters into the unrelated P11.2A Li geometry.

## Primary evidence

### SRC08 — Jin et al. (2026)

Kaiyan Jin, Jianbin Li, Lin Zhang, Jianhan Liang, Xiaodong Cai, *Experimental study on heat release distribution during supersonic combustion*, Combustion and Flame 287 (2026) 114876, DOI `10.1016/j.combustflame.2026.114876`.

For the independent model-B validation Jin reports:

- a cavity-free Liu circular combustor selected as closer to quasi-one-dimensional assumptions;
- heat-release estimation based on the Jin quasi-Gaussian model, experimental PLIF information, and the measured exit stagnation-enthalpy increment;
- theoretical exit Mach `2.24` versus experimental `2.27`;
- the validation condition labelled **model B, `phi=1.04`**.

Jin Sec. 3.2.3 Eqs. (9)–(11) also make clear that the simple model requires `A(x)`, `Tt(x)`, `gamma`, wall-friction coefficient `Cf`, a duct diameter/scale, heat release, mass flow, `cp`, and the initial stagnation temperature. The text assumes the validation flow remains supersonic and separation-free.

### SRC10 — Liu et al. (2019)

Qili Liu, Damiano Baccarella, Brendan McGann, Tonghun Lee, *Dual-Mode Operation and Transition in Axisymmetric Scramjets*, AIAA Journal 57(11) (2019) 4764–4777, DOI `10.2514/1.J058391`.

Liu supplies the primary model-B experiment and Table-2 exit measurements. The model-B ethylene row that matches Jin's experimental exit Mach `2.27` is reported at `phi=1.03`, with:

- `M4 = 2.27`;
- `pt4 = 17383.8 Pa`;
- `pt4/pt3 = 0.39`;
- `Ht4/Ht3 = 1.16`.

Liu's exact `phi=1.04` row belongs to **model A**, not model B, and has `M4=1.76`. This is preserved as a source conflict rather than silently rounded or relabelled.

## Geometry state

The study geometry is no longer an open blocker.

Source-backed / cross-checked dimensions include:

- station 3 / most-upstream injector at `291.4 mm` downstream of the SRC10 inlet lip;
- isolator length `254 mm`, diameter `35 mm`;
- model-A cavity leading edge `42 mm` downstream of the injector;
- cavity floor `35 mm`, depth `11 mm`, closeout ramp `22.5 deg`;
- downstream diverging section length `357 mm`;
- primary-source descriptor `2 deg cone angle`;
- independently reported overall lengths near `752 mm`.

The closeout-ramp axial projection is derived as

`11 / tan(22.5 deg) = 26.55635 mm`.

Therefore the model-B replacement-tube module is

`35 + 26.55635 = 61.55635 mm`,

and the divergence starts

`42 + 61.55635 = 103.55635 mm`

downstream of station 3.

The solver coordinate is frozen as:

- `x=0` at station 3 / injector;
- divergence start `x=0.10355635 m`;
- station 4 / exit `x=0.46055635 m`;
- SRC10 inlet-referenced transform `x_solver = x_source - 0.2914 m`.

The complete reconstruction closes independent total-length records to sub-millimetre residuals. Those residuals are cross-checks, not fitted corrections.

## Area-law interpretation

The primary source says `2 deg cone angle` but the recovered wording does not explicitly define half-angle versus full included angle. This distinction is kept visible.

Same-program primary evidence plus a peer-reviewed terminology cross-check support treating the parameter as **wall divergent angle**. The study layer therefore uses `2 deg` as the wall angle measured from the centerline, classified as:

`SOURCE_CORROBORATED_INTERPRETATION`.

The resulting radius / area law is `DERIVED`. For the source-backed `35 mm` diameter and `357 mm` length, this gives `A_exit/A_inlet ≈ 2.9323`. A higher-authority primary figure or author dataset must override this interpretation if contradictory.

## Friction-coefficient convention is now closed

Jin Eqs. (9)–(10) use the differential friction term `4 Cf dx / D` and explicitly cite A.H. Shapiro's *The Dynamics and Thermodynamics of Compressible Fluid Flow* as the equation source.

Shapiro defines the duct friction coefficient as wall shear stress divided by dynamic head:

`Cf = tau_w / (0.5 rho u^2)`.

For a circular / hydraulic-diameter duct,

`S_m = -4 tau_w / D_h = -2 Cf rho u|u| / D_h`.

The repository production wall source is explicitly

`S_m = -0.5 f_D rho u|u| / D_h`,

where `f_D` is the Darcy friction factor. Equating the same wall force gives the derived mapping

`f_D = 4 Cf`.

This mapping is stored in `cases/studies/data/p11_2b_jin_friction_convention_source.json` and implemented in `cases/studies/p11_2b_friction_convention.py`. It is classified `DERIVED_CONVENTION_MAPPING`, not inferred from notation alone.

This resolves the **coefficient convention** only. The actual numerical `Cf` used in Jin Fig. 14 remains unknown and is still an active blocker.

## Current formal-case blockers

Five bounded evidence gaps remain:

1. **condition identity** — resolve Jin model-B `phi=1.04` versus Liu model-B `phi=1.03` / model-A `phi=1.04`;
2. **heat-release shape** — recover the exact Fig. 14 profile or fitted `Q_m, x_i, x_m, x_c, k` with traceable coordinates;
3. **absolute energy scale** — recover the measured exit stagnation-enthalpy increment and matching mass flow / station-3 absolute enthalpy, or an already-absolute `Qdot'(x) [W/m]` table;
4. **station-3 boundary state** — recover the complete primitive / total state used to initialize the external model-B calculation;
5. **numerical wall-friction coefficient** — recover Jin's actual Fig. 14 `Cf`, or direct evidence that it was neglected.

The following are **not** active blockers anymore:

- axial source-to-solver coordinate mapping;
- model-B study-layer radial `A(x)` law;
- Jin/Shapiro `Cf` to repository Darcy-factor convention.

## Formal applicability boundary

Even after all numerical inputs are recovered, a Jin Fig. 14 reproduction can only be claimed if the computed comparison domain remains supersonic (`min(M)>1`). The current quasi-one-dimensional state cannot independently prove the absence of boundary-layer separation, so separation-free applicability remains an external source/model assumption.

## Promotion rule

This candidate remains in `candidate_validation_chains`, not `candidate_formal_cases`.

The project will not:

- infer absolute heat from `Ht4/Ht3` alone;
- infer the validation mass flow from nominal geometry;
- silently replace `phi=1.04` with `1.03`;
- substitute model A for model B;
- invent the station-3 boundary state;
- assume Jin's missing numerical `Cf`;
- use untracked plot digitization as formal input;
- transplant this heat-release distribution into the unrelated P11.2A geometry and call it validation.

Publisher supplementary material or an author-provided data table remains the preferred route for the five missing inputs above.

## Scientific claim if completed

A completed case would be a **prescribed-heat-release quasi-one-dimensional validation against an independent cavity-free experiment**. It would not be detailed finite-rate chemistry validation and would not, by itself, establish LBW/YBW classification.
