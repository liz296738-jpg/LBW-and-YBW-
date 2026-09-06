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

For the current source-free, one-dimensional Euler baseline, `∂U/∂t + ∂F/∂x = 0`.

`U = [rho, rho*u, rho*E]`

`F = [rho*u, rho*u^2 + p, u*(rho*E + p)]`

**P3.1 implements the physical Euler flux `F(U)`.** Spatial discretization, time integration, and a solver remain unimplemented.

P3.2 implements the separate Rusanov baseline numerical interface flux `F_hat(U_L, U_R)` for conservative states on either side of an interface. This numerical flux is not part of the governing physical law.

P3.3 constructs the source-free semi-discrete finite-volume system `dU/dt = L(U)`, where `L_i(U) = -(F_hat_(i+1/2) - F_hat_(i-1/2)) / dx`. This is numerical discretization, not a new physical equation.

P3.4 applies SSP-RK3 to this semi-discrete system as numerical time discretization.

The future quasi-1D formulation will include area effects and other source terms only when their equations have been approved.

## P2 Implemented Relations

P2 implements and tests the ideal-gas relation `p = rho R T`, the energy relations `e = p / [rho (gamma - 1)]` and `E = e + u^2 / 2`, the sound speed `a = sqrt(gamma R T)`, and `Mach = u / a`.

The implemented conservative state is `U = [rho, rho*u, rho*E]`. The governing PDE and all numerical solver methods remain unimplemented.
