# P11.3K — Source-enabled teacher SSP-RK3 compatibility solver

## Scope

This stage combines the accepted building blocks without expanding their physics claims:

1. the P11.3J air-only-upstream / single-interior-injector mapping;
2. the variable-composition quasi-one-dimensional Euler/Rusanov operator;
3. the non-geometric Chapter 11 Eq. (11.38) source vector.

The full compatibility RHS is

`R(U) = R_Euler+area(U,Y) + S_11.38_non-geometric(U,phi,eta)`.

The existing Euler operator is the **only** place that contributes the geometric `p dA/dx` term, so Eq. (11.38) wiring cannot duplicate it.

## SSP-RK3 source treatment

Eq. (11.25) friction depends on the prescribed combustion state through `phi*eta`, while the actual momentum source also depends on the current `rho` and `u`. Therefore the complete source vector is recomputed from each intermediate SSP-RK3 stage state. Fuel-source location, injected stream velocity/enthalpy, `phi`, `eta`, and composition remain frozen by the prescribed operating-point mapping.

A variable-composition CFL estimate controls the outer pseudo-time step. Every accepted step is recovered through the source-backed variable thermochemistry and must remain physically admissible.

## Heat and chemical-energy boundary

The solver accepts an explicit dimensional `d(delta q)/dx` profile because that is the quantity used by the transcribed Eq. (11.38) energy source. It still does **not** infer that profile from the empirical Eq. (11.26) coefficient; the source evidence for that dimensional conversion remains incomplete.

Reaction energy is represented once through composition-dependent absolute species enthalpy/internal energy. There is no independent teacher chemical `Qdot` input in this solver.

## What this stage does not claim

This remains a compatibility solver because the flux is Rusanov and the boundary faces are transmissive. The teacher alignment review identifies prescribed inlet static `p/T/u` and first-order outlet extrapolation as the target case semantics. Those are the next implementation gate. Variable-property Steger–Warming, including the teacher's near-sonic smoothing rule, remains separately source-gated.
