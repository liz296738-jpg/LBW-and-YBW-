# Teacher Chapter 11 mixing and lean-combustion closure

## Scope

This P11.3C stage transcribes the teacher-provided Chapter 11 relations on textbook pages 256--258 before they are coupled to the variable-thermochemistry CFD solver. The primary source is the photographed teacher material in `乔老师项目/IMG_2464.HEIC.JPG` through `IMG_2466.HEIC.JPG`.

The implemented source equations are:

- Eq. (11.19): empirical mixing-efficiency correlations for parallel, normal, and strut injection;
- Eq. (11.20): complete-mixing length `L_m`;
- Eqs. (11.21)--(11.24): hydrocarbon complete-combustion stoichiometry, stoichiometric fuel/air ratio, and equivalence ratio;
- Eqs. (11.27)--(11.29): lean-mixture (`phi <= 1`) H2, pseudo-kerosene C10H22, and C2H4 composition relations with combustion efficiency `eta`.

The implementation lives in `src/scramjet1d/teacher_combustion.py`. Provenance/readiness is recorded in `cases/studies/data/teacher_mixing_combustion_closure.json`.

## Source equations and constants

Eq. (11.19) is retained as the raw empirical correlation. For distance `x` from the injector and complete-mixing length `L_m`:

- parallel injection: `eta_m = x/L_m`;
- normal injection: `eta_m = [x/L_m + 1/(50 + 1000 alpha)]^alpha`, with source `alpha = 0.17--0.25`;
- strut injection: `eta_m = [1-exp(-A x/L_m)]/[1-exp(-A)]`, with source `A = 1.77--3.4`.

Eq. (11.20) is

- `L_m = 0.179 C_m exp(1.72 phi0) b`, `phi0 <= 1`;
- `L_m = 3.333 C_m exp(-1.204 phi0) b`, `phi0 > 1`;

where the source gives `C_m = 25--60` and `b` is the combustor-section height.

The textbook stoichiometric fuel/air ratio is

`f_st = (36 x + 3 y) / [103 (4 x + y)]`

for `C_x H_y`, with reference values approximately `0.0291` for H2, `0.068` for C2H4, and `0.0667` for C10H22. Equivalence ratio follows Eq. (11.23), `phi = (m_f/m_air)/f_st`.

Eqs. (11.27)--(11.29) use the dry-air molar basis

`O2 + 3.7274 N2 + 0.04592 Ar`

and express the species amounts as functions of lean equivalence ratio `phi` and combustion efficiency `eta`.

## Important modeling boundary: no silent clipping

The normal-injection Eq. (11.19) can produce a value slightly above one near `x/L_m = 1`. The source text states that combustion efficiency is approximated by mixing efficiency, but the photographed pages do not explicitly specify a saturation rule.

Therefore the code deliberately separates these concepts:

1. `mixing_efficiency_raw(...)` returns Eq. (11.19) exactly and never clips it;
2. `lean_reaction_mole_amounts(...)` requires the physical reaction efficiency `eta` to lie in `[0, 1]`;
3. solver coupling remains gated until an explicit project policy maps the raw empirical correlation to the physical combustion-efficiency interval.

This avoids hiding a physics decision inside a numerical convenience operation.

## Thermochemistry boundary

The existing source-backed GRI-Mech subset already supplies thermodynamic models for H2, O2, N2, Ar, H2O, C2H4, and CO2. Therefore H2 and C2H4 reaction-composition outputs can already be converted to mass fractions and passed to the verified variable-property thermochemistry path.

C10H22 is different: Eq. (11.28) is source-transcribed and can be checked for stoichiometric/element conservation, but its CHEMKIN/NASA thermochemical polynomial is still not frozen in the project. Partial-combustion C10H22 must not be promoted into the thermodynamic solver until that source gap is closed.

## Chemical-energy accounting

This closure stage does not add a reaction heat source. Once composition changes are coupled to absolute species enthalpy, chemical reaction energy is represented by the composition-dependent thermochemical state. The independent prescribed `Qdot'(x)` pathway remains useful for reduced-order V&V, but it must not be applied simultaneously to represent the same chemical energy.

## Acceptance criteria for this stage

The isolated stage is acceptable only when tests demonstrate:

- Eq. (11.20) branch behavior and published calibration ranges;
- Eq. (11.19) endpoint/shape behavior without clipping;
- textbook stoichiometric fuel/air ratios;
- Eq. (11.23) mass-flow equivalence ratio;
- atom conservation of Eqs. (11.27)--(11.29);
- normalized mole/mass fractions for H2 and C2H4 with the existing source-backed species database;
- explicit rejection of rich (`phi > 1`) use of the transcribed lean-only composition equations;
- explicit C10H22 thermochemistry gating when unreacted pseudo-kerosene remains.

Only after this isolated closure passes CI should variable composition be coupled to the SSP-RK3 solver.
