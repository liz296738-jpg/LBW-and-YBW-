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

The primary source says `2 deg cone angle` but the recovered wording does not explicitly define half-angle versus full included angle. Same-program primary evidence plus a peer-reviewed terminology cross-check support treating the parameter as **wall divergent angle**. The study layer therefore uses `2 deg` as the wall angle measured from the centerline, classified as `SOURCE_CORROBORATED_INTERPRETATION`.

The resulting radius / area law is `DERIVED`. For the source-backed `35 mm` diameter and `357 mm` length, this gives `A_exit/A_inlet ≈ 2.9323`. A higher-authority primary figure or author dataset must override this interpretation if contradictory.

## Friction-coefficient convention

Jin Eqs. (9)–(10) use the differential friction term `4 Cf dx / D` and cite A.H. Shapiro. Matching Shapiro's wall-shear definition to the repository wall source gives the derived convention mapping

`f_D = 4 Cf`.

This resolves the **coefficient convention** only. The actual numerical `Cf` used in Jin Fig. 14 remains unknown.

A fresh primary-source check also confirms that Liu's own quasi-one-dimensional pressure and Mach analyses explicitly neglect or treat wall friction as negligible around Eqs. (3) and (5). That is useful context, but it does **not** establish that Jin set `Cf=0` in the separate Fig. 14 calculation. The project therefore continues to block an exact Fig. 14 reproduction on Jin's numerical `Cf` unless direct evidence shows that it was neglected.

## Bounded public-source recovery

`cases/studies/data/p11_2b_liu_primary_recovery.json` now separates exact source algebra from exploratory modelling bridges. `cases/studies/p11_2b_public_evidence_recovery.py` reproduces the calculations and deliberately leaves `formal_case_ready=false`.

### Exact same-row constraint

For Liu model B at `phi=1.03`, Table 2 gives both `pt4=17383.8 Pa` and `pt4/pt3=0.39`. Therefore the station-3 total pressure for **that Liu row** is algebraically constrained by

`pt3 = pt4 / (pt4/pt3) = 44573.846... Pa`.

This is classified `DERIVED_FROM_SAME_ROW_SOURCE_VALUES`. It is useful evidence, but it does not prove that Jin's labelled `phi=1.04` Fig. 14 case is identical to the Liu `phi=1.03` row.

### Exploratory energy/mass-flow bridge

The same ledger records, but does not formally promote, a reproducible estimate based on three explicit assumptions:

1. station-3 stagnation temperature is bridged from the nominal `Tt=2400 K` freestream by adiabatic no-work stagnation-enthalpy conservation;
2. nominal captured air mass flow is estimated from the reported freestream `rho=0.0025 kg/m3`, `u=1966 m/s`, inlet area-contraction ratio `1.9`, and `35 mm` isolator diameter, assuming uniform full capture with no spillage correction;
3. Liu's source-reported average `cp=1255 J/(kg K)` is used with `Ht4/Ht3=1.16`.

These give approximately:

- nominal full-capture air mass flow `8.985e-3 kg/s`;
- candidate stagnation-enthalpy increment `4.8192e5 J/kg`;
- candidate total heat power `4.330 kW`.

Those numbers are **diagnostic bounds, not formal Fig. 14 inputs**. They are intentionally prevented from closing the formal gate because neither the exact Jin condition identity nor its measured mass-flow/initial-state chain has been recovered.

## Current formal-case blockers

The authoritative readiness artifact combines shape and absolute energy into one evidence-chain requirement, leaving **four** bounded blockers:

1. **condition identity** — resolve Jin model-B `phi=1.04` versus Liu model-B `phi=1.03` / model-A `phi=1.04`;
2. **station-3 boundary state** — recover the complete primitive / total state used to initialize the external Fig. 14 model-B calculation;
3. **numerical wall-friction coefficient** — recover Jin's actual Fig. 14 `Cf`, or direct evidence that it was neglected;
4. **heat-release evidence chain** — recover either an already-absolute `Qdot'(x) [W/m]` profile, or the exact Fig. 14 shape / fitted `Q_m, x_i, x_m, x_c, k` together with its matching absolute energy scale.

The following are **not** active blockers anymore:

- axial source-to-solver coordinate mapping;
- model-B study-layer radial `A(x)` law;
- Jin/Shapiro `Cf` to repository Darcy-factor convention.

## Formal applicability boundary

Even after all numerical inputs are recovered, a Jin Fig. 14 reproduction can only be claimed if the computed comparison domain remains supersonic (`min(M)>1`). The current quasi-one-dimensional state cannot independently prove the absence of boundary-layer separation, so separation-free applicability remains an external source/model assumption.

## Promotion rule

This candidate remains in `candidate_validation_chains`, not `candidate_formal_cases`.

The project will not:

- promote the exploratory `Tt3`, mass-flow, or heat-power bridge as measured data;
- silently replace `phi=1.04` with `1.03`;
- substitute model A for model B;
- invent the station-3 primitive state;
- assume Jin's missing numerical `Cf`;
- use untracked plot digitization as formal input;
- transplant this heat-release distribution into the unrelated P11.2A geometry and call it validation.

Publisher supplementary material or author-provided data remains the preferred route for the four missing evidence families above.

The latest bounded public-access attempt is recorded in
`docs/p11_2b_evidence_recovery_log.md`. It preserves the publisher access
boundary and the exact original files needed for the next recovery round; it
does not alter the machine-readable readiness result.

## Scientific claim if completed

A completed case would be a **prescribed-heat-release quasi-one-dimensional validation against an independent cavity-free experiment**. It would not be detailed finite-rate chemistry validation and would not, by itself, establish LBW/YBW classification.
