# Numerical Method Plan

## Spatial Method

Planned: Steger-Warming Flux Vector Splitting with upwind discretization.

## Baseline Numerical Flux

P3.2 implements the temporary verified baseline Rusanov / Local Lax-Friedrichs flux:

`F_hat = 0.5 * (F_L + F_R) - 0.5 * alpha * (U_R - U_L)`

where `alpha = max(|u_L| + a_L, |u_R| + a_R)`. It provides a simple, stable, but comparatively dissipative baseline for later spatial-residual and time-integration verification. The planned Steger-Warming method remains unchanged.

## Baseline Spatial Discretization

P3.3 implements a first-order finite-volume formulation with piecewise-constant cell states and Rusanov interface fluxes on a uniform grid only:

`dU_i/dt = -(F_hat_(i+1/2) - F_hat_(i-1/2)) / dx`

Boundary interface fluxes are not implemented.

## Time Integration

P3.4 implements generic third-order SSP / TVD Runge-Kutta integration: `U1 = U^n + dt L(U^n)`, `U2 = 3/4 U^n + 1/4 [U1 + dt L(U1)]`, and `U^(n+1) = 1/3 U^n + 2/3 [U2 + dt L(U2)]`. CFL-based dt, boundary treatment, and a complete CFD time loop remain unimplemented.

## Time Step

Planned: CFL-based adaptive time step.

## Convergence

Future steady-state convergence will use normalized residuals and/or relative state changes.

## Important Note

**No boundary treatment, time integration, or CFD solver is implemented in P3.3.**
