# Numerical Method

## Spatial Method

Implemented: first-order Steger-Warming Flux Vector Splitting with piecewise-constant upwind discretization.

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

P5.2 defines the first-order piecewise-constant interface construction `F_hat_(i+1/2) = F_plus(U_i) + F_minus(U_(i+1))`. It is vectorized and supports broadcast-compatible state arrays.

## Flux Scheme Selection

P5.3 connects explicit `rusanov` and `steger-warming` interface choices to the quasi-1D solver. Both choices use the same state representation, geometry, source discretization, transmissive boundary, CFL and SSP-RK3; only the interface numerical flux changes. Rusanov remains the default.

## Time Integration

P3.4 implements generic third-order SSP / TVD Runge-Kutta integration: `U1 = U^n + dt L(U^n)`, `U2 = 3/4 U^n + 1/4 [U1 + dt L(U1)]`, and `U^(n+1) = 1/3 U^n + 2/3 [U2 + dt L(U2)]`.

## Time Step and Accuracy

P3.5 uses the uniform-grid baseline `dt = CFL * dx / max(|u| + a)` with default `CFL = 0.5`. Both Rusanov and Steger-Warming use this identical CFL calculation.

## P6.3 Wall-Source Integration

The quasi-1D RHS retains its area-weighted flux divergence and geometric source, then adds the composed prescribed wall-friction and wall-heat sources. Active wall sources are evaluated inside `RHS(U_stage)` for each of the three SSP-RK3 stages; they are not frozen at the start of a timestep. The CFL formula remains based only on Euler wave speed. Assessment of source stiffness for stronger cases is deferred to P6.4.

## P6.4 Validation Status

The uniform wall-source benchmark shows third-order SSP-RK3 temporal behavior (observed velocity order about 2.999) and the tested mild/moderate prescribed-source range remains physical with the existing Euler-wave CFL. Fanno and Rayleigh profiles are evaluated as continuum steady residual-consistency references, not as boundary-driven solutions under transmissive boundaries. The strict requirement that every scheme/branch exhibit a first-order residual trend is not met: smooth Fanno Rusanov residuals converge near second order, while the supersonic Steger-Warming Rayleigh energy residual is at discrete roundoff level and is not monotonic. P6 therefore remains in progress pending an architectural decision on the validation criterion; no numerical method was changed to force this result.

P5.4 controlled validation confirms the interface law `F_hat_SW = F_plus(U_L) + F_minus(U_R)`, first-order spatial convergence on isentropic residual and smooth entropy-wave benchmarks, and physical finite states in the requested shock and near-sonic smoke cases. SSP-RK3 is third order in time, but the overall smooth-benchmark accuracy is spatial first-order dominant because reconstruction remains piecewise constant.

## Convergence

Future steady-state convergence will use normalized residuals and/or relative state changes.

## Important Note

**P3 solves the source-free constant-area baseline. P4.3 adds variable-area baseline transient integration, and P4.4/P5.4 provide controlled validation. Higher-order spatial reconstruction is intentionally not implemented.**
