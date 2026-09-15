# Teacher variable-composition field compatibility

## Purpose

P11.3E connects the already verified teacher lean-combustion composition equations to the already verified variable-thermochemistry state conversion without yet changing numerical fluxes or time marching.

The teacher Chapter 11 model advances three quasi-one-dimensional conservative flow equations and closes local mixture composition algebraically from equivalence ratio and combustion efficiency. The transcribed model does not require adding a separate species-transport PDE system at this stage.

## Representation

`TeacherCompositionField` stores an immutable finite-volume table

`Y_i(x_j)`

with one normalized mass-fraction row per cell. Every row must be finite, nonnegative, and sum to one. H2 and C2H4 fields are generated directly from teacher Eqs. (11.27) and (11.29), respectively.

C10H22 remains excluded from thermochemical state conversion because its reaction equation is known but its source-backed CHEMKIN/NASA thermochemistry is not yet frozen.

## Cell-wise state conversion

The new compatibility functions reuse the existing verified fixed-composition state routines cell by cell:

- primitive -> conservative uses each cell's own `e(T,Y)` and forms `E=e+u^2/2`;
- conservative -> primitive inverts each cell's own `e(T,Y)` over the common source-valid temperature interval and reconstructs `p`, `R`, `cp`, `gamma`, `h` and Mach.

No alternate thermodynamic formulas are introduced. When every row of the composition field is identical, this stage is required to reduce to the existing fixed-composition variable-state path.

## What this stage does not do

This is not yet a reacting CFD solver. It deliberately adds none of the following:

- different-composition left/right numerical fluxes;
- composition-aware SSP-RK3 time marching;
- fuel-injection mass/momentum/enthalpy coupling;
- teacher wall-friction coupling;
- wall heat-loss coupling;
- a separate combustion `Qdot` source;
- species transport or finite-rate chemical kinetics.

The separation is intentional: state compatibility must be correct before fluxes and source terms are allowed to use spatially varying composition.

## Energy accounting

Absolute source-backed species enthalpy/internal energy remains the chemical-energy datum. A future variable-composition solver must conserve the total conservative energy while composition changes alter the thermochemical energy partition. The independent prescribed `Qdot'(x)` V&V interface must not be used to add the same chemical reaction energy again.

## Next gate

The next narrow step is an interface-flux compatibility layer in which each side of a Rusanov interface is recovered with its own composition. It must verify:

1. identical left/right composition reduces to the already accepted fixed-composition variable Rusanov flux;
2. identical state and composition returns the physical Euler flux;
3. finite-volume conservation remains exact at shared interfaces;
4. source-backed temperature/composition admissibility is enforced independently on both sides.

Only after those checks should variable-composition time marching be introduced.
