# Teacher-reference variable thermochemistry — P11.3B

## Scope

This stage implements the thermochemical relations explicitly shown in the teacher-provided Chapter 11 pages 258–259 (Eqs. 11.30–11.35) and corroborated by Cao Ruifeng's one-dimensional formulation (Chapter 2, Eqs. 2-28–2-34).

The implementation is intentionally isolated from the production Euler state conversion. The project first verifies the variable-property closure independently, then freezes a source-backed species coefficient database, and only after that changes solver state recovery.

## Frozen equations

For species `s` with molecular weight `W_s` and universal gas constant `R_u`, the teacher reference uses

```text
R_s = R_u / W_s
cp_s(T) = R_s * (a1 + a2*T + a3*T^2 + a4*T^3 + a5*T^4)
h_s(T)  = R_s * (a1*T + a2*T^2/2 + a3*T^3/3 + a4*T^4/4 + a5*T^5/5 + a6)
```

For mass fractions `Y_s`, the mixture relations are

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

The `e = h - RT` relation is included because future conservative-state recovery needs temperature from internal energy rather than from a constant-`gamma` closed form.

## Implemented module

`src/scramjet1d/thermochemistry.py`

The module now provides:

- validated six-coefficient species thermo polynomials;
- explicit species temperature validity ranges;
- species `R`, `cp(T)`, and absolute `h(T)`;
- mixture molecular weight;
- mixture `R(T,Y)`-independent composition gas constant, `cp(T,Y)`, `cv(T,Y)`, `gamma(T,Y)`, `h(T,Y)`, and `e(T,Y)`;
- ideal-mixture pressure from density, temperature, and composition;
- a bounded bisection inversion from mixture internal energy to temperature at fixed composition.

No state clipping, silent mass-fraction renormalization, or out-of-range polynomial extrapolation is allowed.

## Why absolute enthalpy matters

The photographed Chapter 11 text states that the fitted enthalpy is an **absolute enthalpy** containing both sensible enthalpy and the zero-point / chemical-energy contribution. Cao's thesis states the same distinction.

Therefore chemical reaction energy associated with changing composition is already represented when absolute species enthalpies are used consistently. Future solver integration must not add the same reaction energy a second time through the project's direct prescribed `Qdot'(x)` surrogate.

External wall heat transfer or separately defined external heat addition remains a distinct energy source.

## Current scientific gate

Machine-readable ledger:

`cases/studies/data/teacher_thermochemistry_equations.json`

Current readiness:

- equation transcription: **ready**;
- isolated thermochemistry implementation: **ready**;
- unit/regression tests: **ready**;
- production species coefficient database: **not yet ready**;
- piecewise temperature-interval database selection: **not yet ready**;
- production solver integration: **not yet ready**;
- integrated teacher-reference reacting case: **not yet ready**.

The coefficient database is intentionally not fabricated. Before production use, every species record must freeze the coefficient source, coefficient convention, molecular weight, temperature interval(s), interval switch temperature where applicable, and provenance.

## Next step

The immediate next substage is to freeze a production coefficient set for the species required by the teacher/Cao fuel closure, validate polynomial outputs against source values, and add piecewise interval handling if the selected source uses multiple temperature bands. Only after that gate passes should variable thermochemistry be wired into conservative-to-primitive state recovery.
