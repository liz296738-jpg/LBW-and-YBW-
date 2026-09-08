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

P3.5 completes the baseline assembly with transmissive zero-gradient ghost cells.

## Time Integration

P3.4 implements generic third-order SSP / TVD Runge-Kutta integration: `U1 = U^n + dt L(U^n)`, `U2 = 3/4 U^n + 1/4 [U1 + dt L(U1)]`, and `U^(n+1) = 1/3 U^n + 2/3 [U2 + dt L(U2)]`.

## Time Step

P3.5 uses the uniform-grid baseline `dt = CFL * dx / max(|u| + a)` with default `CFL = 0.5`. Rusanov remains a verified baseline; the planned Steger-Warming method remains unchanged.

## Convergence

Future steady-state convergence will use normalized residuals and/or relative state changes.

## Important Note

**P3 solves the source-free constant-area baseline only. Variable area, source terms, and planned higher-fidelity methods remain future work.**
