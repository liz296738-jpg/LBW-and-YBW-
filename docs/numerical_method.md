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

## Geometry Discretization

P4.1 represents a mesh with `N` cell areas `A_i` and `N + 1` face areas `A_(i+1/2)`. The signed area change in cell `i` is `ΔA_i = A_(i+1/2) - A_(i-1/2)`.

## Quasi-1D Spatial Discretization

P4.2 retains the numerical interface flux as `F_hat`; area weighting belongs to the spatial layer. Face fluxes are weighted by `A_face`, their difference is normalized by `A_cell * dx`, and the geometric momentum source uses the same face-area difference:

`L_i = -[A_R F_hat_R - A_L F_hat_L] / (A_i dx) + [0, p_i (A_R - A_L) / (A_i dx), 0]`.

Using the identical `A_R - A_L` in both terms preserves the static constant-pressure equilibrium. This P4.2 operator accepts complete supplied interface fluxes; it does not construct boundaries, select a numerical flux, or advance time.

## Variable-Area Solver Assembly

P4.3 assembles the baseline transient path:

`cell state -> transmissive ghost states -> Rusanov fluxes -> face-area weighting + geometric source -> quasi-1D RHS -> CFL -> SSP-RK3`.

The time step remains `dt = CFL * dx / max(|u| + a)`; area is not a CFL multiplier. The transmissive ghost states are a baseline verification boundary, not a final scramjet inlet or outlet condition.

## P4 Validation Strategy

Analytical-face consistency evaluates analytical face fluxes with the discrete geometry source. On smooth grids this controlled geometry/source check approaches second-order truncation consistency. The actual baseline numerical path uses piecewise-constant states and Rusanov fluxes, and its interior residual is expected to approach first order. This does not make the production solver second order: no MUSCL reconstruction or limiter is implemented.

## Steger-Warming Flux Vector Splitting

P5.1 implements raw, unsmoothed single-state splitting with Euler eigenvalues `lambda = [u-a, u, u+a]` and `lambda_plus/minus = 0.5 * (lambda +/- |lambda|)`. The closed-form split fluxes satisfy `F_plus + F_minus = F`. No entropy fix or sonic smoothing is applied.

P5.2 defines the first-order piecewise-constant interface construction `F_hat_(i+1/2) = F_plus(U_i) + F_minus(U_(i+1))`. It is vectorized and supports broadcast-compatible state arrays. It has not yet been connected to a spatial operator or solver; production integration remains Rusanov.

## Time Integration

P3.4 implements generic third-order SSP / TVD Runge-Kutta integration: `U1 = U^n + dt L(U^n)`, `U2 = 3/4 U^n + 1/4 [U1 + dt L(U1)]`, and `U^(n+1) = 1/3 U^n + 2/3 [U2 + dt L(U2)]`.

## Time Step

P3.5 uses the uniform-grid baseline `dt = CFL * dx / max(|u| + a)` with default `CFL = 0.5`. Rusanov remains a verified baseline; the planned Steger-Warming method remains unchanged.

## Convergence

Future steady-state convergence will use normalized residuals and/or relative state changes.

## Important Note

**P3 solves the source-free constant-area baseline. P4.3 adds variable-area baseline transient integration; controlled nozzle validation and planned higher-fidelity methods remain future work.**
