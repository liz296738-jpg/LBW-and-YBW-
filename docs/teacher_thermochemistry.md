# Teacher-reference variable thermochemistry — P11.3B

## Scope

This stage implements the thermochemical relations explicitly shown in the teacher-provided Chapter 11 pages 258–259 (Eqs. 11.30–11.35) and corroborated by Cao Ruifeng's one-dimensional formulation (Chapter 2, Eqs. 2-28–2-34).

The variable-property closure remains isolated from the production Euler state conversion until its source-backed data and inversion behavior are verified.

## Frozen equations

For species `s` with molecular weight `W_s` and universal gas constant `R_u`:

```text
R_s = R_u / W_s
cp_s(T) = R_s * (a1 + a2*T + a3*T^2 + a4*T^3 + a5*T^4)
h_s(T)  = R_s * (a1*T + a2*T^2/2 + a3*T^3/3 + a4*T^4/4 + a5*T^5/5 + a6)
```

For mass fractions `Y_s`:

```text
1/W_mix = sum_s(Y_s / W_s)
R_mix   = R_u / W_mix = sum_s(Y_s * R_s)
cp_mix  = sum_s(Y_s * cp_s)
h_mix   = sum_s(Y_s * h_s)
cv_mix  = cp_mix - R_mix
gamma    = cp_mix / cv_mix
p        = rho * R_mix * T
e        = h_mix - R_mix * T
```

## Implemented equation layer

`src/scramjet1d/thermochemistry.py` now provides:

- validated six-coefficient species intervals;
- two-interval CHEMKIN/NASA polynomial selection with an explicit switch temperature;
- species `R`, `cp(T)`, and absolute `h(T)`;
- mixture molecular weight, `R(Y)`, `cp(T,Y)`, `cv(T,Y)`, `gamma(T,Y)`, `h(T,Y)`, and `e(T,Y)`;
- ideal-mixture pressure;
- bounded fixed-composition inversion from internal energy to temperature.

No state clipping, silent mass-fraction renormalization, or out-of-range polynomial extrapolation is allowed.

## Frozen source-backed core database

Data record:

`cases/studies/data/teacher_thermochemistry_gri30_core.json`

Loader/readiness audit:

`cases/studies/teacher_thermochemistry_database.py`

The core database freezes `H2`, `O2`, `N2`, `Ar`, `H2O`, `C2H4`, and `CO2` using the GRI-Mech 3.0 CHEMKIN/NASA polynomial record. Exact coefficient lines are tied to a reproducible public `thermo30.dat` mirror; the Berkeley GRI-Mech thermodynamic table supplies an independent rounded 298 K `cp` sanity check, and molecular weights are tied to NIST Chemistry WebBook values.

The source intervals are preserved rather than normalized to one artificial range. For example, the classic GRI records use a 1000 K interval switch, while `N2` and `Ar` begin at 250 K and several other species begin at 200 K.

Regression gates verify:

- low/high `cp` and absolute `h` continuity at the source switch;
- the source interval is selected on the correct side of 1000 K;
- the computed 298.15 K molar `cp` agrees with Berkeley's rounded GRI table within its display precision;
- the piecewise species database works directly in the teacher mixture equations.

This gives source-backed thermodynamic-property coverage for the teacher's hydrogen and ethylene branches. It does **not** yet complete reaction/composition closure.

## Explicit kerosene blocker

The photographed teacher reaction set also contains pseudo-kerosene `C10H22`. That species is not present in the frozen GRI-Mech 3.0 core record used here.

Therefore `C10H22` remains explicitly blocked. The project will not invent a polynomial or borrow an unrelated surrogate without recording its source and compatibility. The first integrated teacher case may use the H2 or C2H4 branch if the remaining closure equations are completed first.

## Why absolute enthalpy matters

The photographed Chapter 11 text states that the fitted enthalpy is an **absolute enthalpy** containing sensible enthalpy plus the zero-point / chemical-energy contribution. Cao's thesis states the same distinction.

Chemical reaction energy associated with changing composition is therefore represented when absolute species enthalpies are used consistently. Future solver integration must not add the same reaction energy a second time through the project's direct prescribed `Qdot'(x)` surrogate. External wall/additional heat remains a separate source.

## Current readiness

- equation transcription: **ready**;
- isolated thermochemistry implementation: **ready**;
- piecewise interval handling: **ready**;
- source-backed H2/C2H4 core species data: **ready**;
- independent 298 K `cp` sanity checks: **ready**;
- `C10H22` thermochemical data: **blocked**;
- production variable-thermo state recovery: **not yet promoted**;
- teacher mixing/equivalence-ratio/composition closure: **not yet implemented**;
- integrated teacher-reference reacting case: **not yet ready**.

## Next step

The next safe step is to create a variable-thermodynamic conservative/primitive state-recovery path **without replacing the constant-gas baseline**, initially limited to the frozen H2/C2H4-compatible species set. That path must round-trip `(rho, u, T, Y) -> U -> (rho, u, T, p, Y)`, use bounded `e -> T` inversion, enforce common source-valid temperature bounds, and prove conservation/state recovery before it is connected to the full quasi-one-dimensional solver.
