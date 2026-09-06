# Mathematical Model

## Assumptions for Baseline Model

The future baseline model is one-dimensional, compressible, inviscid, and adiabatic. It uses an ideal, calorically perfect gas with constant `gamma` and constant `R`; it initially excludes combustion and fuel injection. These are staged assumptions, not claims about the final model.

## Primitive Variables

`rho`, `u`, `p`, `T`, `Mach`

## Conservative Variables

`rho`, `rho*u`, `rho*E`

## Equation of State

`p = rho R T`

## Energy Relation

`E = e + u^2 / 2`  
`e = p / [rho (gamma - 1)]`

## Speed of Sound and Mach Number

`a = sqrt(gamma R T)`  
`M = u / a`

## Governing Equation

`∂U/∂t + ∂F/∂x = S`

The future quasi-1D formulation will include area effects and other source terms only when their equations have been approved. No source-term formula is implemented in P2.

## P2 Implemented Relations

P2 implements and tests the ideal-gas relation `p = rho R T`, the energy relations `e = p / [rho (gamma - 1)]` and `E = e + u^2 / 2`, the sound speed `a = sqrt(gamma R T)`, and `Mach = u / a`.

The implemented conservative state is `U = [rho, rho*u, rho*E]`. The governing PDE and all numerical solver methods remain unimplemented.
