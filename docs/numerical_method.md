# Numerical Method Plan

## Spatial Method

Planned: Steger-Warming Flux Vector Splitting with upwind discretization.

## Baseline Numerical Flux

P3.2 implements the temporary verified baseline Rusanov / Local Lax-Friedrichs flux:

`F_hat = 0.5 * (F_L + F_R) - 0.5 * alpha * (U_R - U_L)`

where `alpha = max(|u_L| + a_L, |u_R| + a_R)`. It provides a simple, stable, but comparatively dissipative baseline for later spatial-residual and time-integration verification. The planned Steger-Warming method remains unchanged.

## Time Integration

Planned: third-order TVD / SSP Runge-Kutta.

## Time Step

Planned: CFL-based adaptive time step.

## Convergence

Future steady-state convergence will use normalized residuals and/or relative state changes.

## Important Note

**No spatial discretization, time integration, or CFD solver is implemented in P3.2.**
