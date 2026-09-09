# P6 Wall Friction and Heat-Transfer Validation

## Purpose

P6.4 verifies the implemented prescribed Darcy wall-friction and prescribed wall-heat-flux sources after their SSP-RK3 quasi-1D integration. It does not introduce a friction correlation, heat-transfer correlation, new boundary condition, or new source timestep rule.

## Governing Sources

The independent source vectors are `S_f = [0, -f_D rho u |u|/(2 D_h), 0]` and `S_q = [0, 0, 4 q''_w/D_h]`. The complete P6 RHS is the existing P4/P5 residual plus these two contributions. Positive `q''_w` heats the gas. Darcy friction factor and wall heat flux are prescribed inputs.

## Exact Uniform Benchmark

For uniform constant-area flow, the reference is `rho=rho0`, `u=u0/[1+(f_D/(2D_h))u0 t]`, and `(rho E)=(rho E)_0+(4q''_w/D_h)t`. At CFL 0.4/0.2/0.1, both flux schemes have velocity errors `1.735e-6/2.171e-7/2.715e-8 m/s` and observed orders `2.999/2.999`. The prescribed energy increment is `8000 J/m³`; density remains invariant and all states remain physical.

## Fanno Residual Consistency

Fanno references use the Darcy relation `Phi_F(M)=f_D L*/D_h`, preserving mass flux and stagnation temperature while remaining on separate subsonic and supersonic branches. Steger-Warming momentum residual orders are `0.978` (subsonic) and `0.999` (supersonic). Rusanov values decrease monotonically but have observed orders `1.939` and `1.978`, rather than the strict first-order acceptance band.

## Rayleigh Residual Consistency

Rayleigh references preserve mass and momentum flux and use the prescribed heat-flux mapping to stagnation-temperature change. Rusanov and subsonic Steger-Warming energy residuals decrease near first order (final orders `0.986`, `0.989`, and `0.993`). The supersonic Steger-Warming energy residual is approximately `1e-6 W/m³`, i.e. near discrete roundoff, and grows mildly on refinement; it therefore does not furnish a meaningful first-order convergence estimate.

These are steady continuum-reference residual checks. They do not claim that transmissive boundaries generate physical Fanno/Rayleigh inlet/outlet solutions.

## CFL and Source Strength

For mild and moderate uniform prescribed-source cases, CFL 0.5 and 0.25 both reached final time with positive physical states. Reducing CFL reduced exact velocity error: mild `2.877e-7 -> 3.594e-8 m/s`, moderate `3.403e-6 -> 4.244e-7 m/s`. No clipping, fallback, or source limiter was used.

## Reproducibility

Run `python cases/baseline/p6_wall_source_validation.py`. It creates `results/p6_4/metrics.json`, four CSV files, and eight PNG plots.

## Limitations

`Darcy friction factor remains prescribed.`

`Wall heat flux remains prescribed.`

`No Reynolds-number, roughness, wall-temperature, Stanton, Nusselt, or radiation model is included.`

`Fanno and Rayleigh profiles are used as steady residual-consistency references; transmissive boundaries are not treated as physical Fanno/Rayleigh inlet/outlet conditions.`

`The current spatial discretization remains first-order piecewise constant.`

`The current timestep limit remains based on Euler wave speed only.`

`No fuel injection or combustion physics is present yet.`

## Conclusion

The temporal exact-source and controlled CFL checks pass, but the strict all-path first-order residual criterion does not. P6.4 is incomplete and P6 remains in progress. No numerical formula or validation threshold was changed to conceal this outcome.
