# P6 Wall Friction and Heat-Transfer Validation

## Scope and reproducibility

P6 validates the prescribed Darcy-friction source `S_f=[0,-f_D rho u|u|/(2D_h),0]` and prescribed wall-heat source `S_q=[0,0,4q''_w/D_h]` after SSP-RK3 integration. It introduces no correlation, limiter, boundary condition, CFL rule, or solver-physics change. Run `python cases/baseline/p6_wall_source_validation.py` to create JSON, CSV, and plot artifacts in `results/p6_4/`.

## Exact temporal benchmark

For uniform constant-area flow, `rho=rho0`, `u=u0/[1+(f_D/(2D_h))u0t]`, and `(rho E)=(rho E)_0+(4q''_w/D_h)t`. Both Rusanov and Steger-Warming give velocity errors `1.735e-6`, `2.171e-7`, and `2.715e-8 m/s` at CFL 0.4, 0.2, and 0.1, with final temporal order `2.999`. Density is invariant, the prescribed energy increment is exactly `8000 J/m³`, and all states are physical.

## Fanno residual consistency

Exact-temporal acceptance is calculated from numerical solver output itself: density conservation, final energy-density error, actual mean energy increment, and its difference from the analytical increment are recorded for every scheme/CFL run; none are hard-coded status flags.

Fanno references preserve `rho*u` and stagnation temperature (variation below `1e-10`) and move Mach toward one on each separate branch. Residuals report mass, momentum, and energy RMS values. The momentum residual is normalized by RMS `|S_f,momentum|`; its finest-grid classifications are: Rusanov subsonic `superconvergent` (1.939), Rusanov supersonic `superconvergent` (1.978), Steger-Warming subsonic `convergent` (0.978), and Steger-Warming supersonic `convergent` (0.999). The Rusanov result is accepted as superconvergence, not rejected for exceeding first order.

## Rayleigh residual consistency

Rayleigh references preserve mass flux and momentum flux, and their stagnation-temperature slope satisfies `dT0/dx=4q''_w/(D_h G cp)` to approximately `2e-11 K/m`. Energy residuals are normalized by RMS `|S_q,energy|`. Rusanov sub/supersonic and Steger-Warming subsonic are convergent (final orders 0.986, 0.989, and 0.993). Supersonic Steger-Warming is `roundoff-limited`, with normalized finest energy residual about `8.1e-13`.

The latter does not claim that Steger-Warming is generally higher order. In fully rightgoing supersonic flow its split interface flux is the left physical flux. For this constant prescribed-heating Rayleigh reference, the energy flux is linear in `x`; the backward difference is then exact apart from floating-point roundoff.

## Source-strength sensitivity

At `D_h=0.1 m` and `t_final=0.002 s`, 1x (`f_D=0.02`, `q''=50 kW/m²`), 2x (`0.04`, `100 kW/m²`), and 4x (`0.08`, `200 kW/m²`) all reach final time with positive physical states at CFL 0.5, 0.25, and 0.125. Exact velocity error strictly decreases under each refinement, with final temporal order above 2.5. This validates the tested range through 4x only; it is not a claim of arbitrary source-strength stability.

## Acceptance and limitations

Hard gates execute solver/reference calculations directly: exact temporal behavior, Fanno/Rayleigh classifications and invariants, Rayleigh `T0` slope, and all 1x/2x/4x source-strength cases. P6.4 and P6 are complete.

The Darcy factor and wall heat flux remain prescribed. No Reynolds/roughness, wall-temperature, Stanton/Nusselt, radiation, fuel-injection, or combustion model is present. Fanno/Rayleigh profiles are steady residual references, not transmissive-boundary inlet/outlet solutions. Spatial reconstruction remains first-order piecewise constant and the timestep limit remains Euler-wave-speed based.
