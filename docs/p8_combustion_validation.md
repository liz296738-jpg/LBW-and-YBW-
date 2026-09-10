# P8 Prescribed Combustion Heat-Release Validation

## Purpose and scope

P8.4 provides formal verification and controlled validation of the prescribed
quasi-1D combustion heat-release capability. Run
`python cases/baseline/p8_4_combustion_validation.py` to regenerate the live
CSV, JSON, and PNG artifacts in `results/p8_4/`. Automated hard gates in
`tests/test_p8_4_combustion_validation.py` evaluate live solver results rather
than accepting pre-recorded files.

This validates the implemented prescribed-source model, not real scramjet
combustion, injector-combustor interaction, or chemical kinetics.

## Frozen model and source separation

The independently prescribed burned-fuel rate maps as
`Qdot'_comb = mdot'_burn LHV`, `qdot_comb = Qdot'_comb/A`, and
`S_comb = [0, 0, qdot_comb]`. The complete energy source is
`S_E = 4q''_w/D_h + rho_dot_f h_t,f + mdot'_burn LHV/A`.

P7 fuel enthalpy is not LHV. P8 chemical heat release is an additional energy
source associated with prescribed reacted fuel. The burn distribution is a
prescribed mathematical validation profile, not a predicted flame shape; P8
does not predict where combustion occurs. The caller remains responsible for
making it consistent with available injected fuel.

## V1 — exact uniform constant-source benchmark

For 20 constant-area cells with `A=0.02 m^2`, `mdot'_burn=0.001 kg/(m s)`,
`LHV=40 MJ/kg`, and `t=1e-4 s`, `qdot_comb=2e6 W/m^3`. Both schemes produced
zero displayed density, momentum, and velocity error; maximum energy error was
`2.328e-10` in conservative units. Pressure and temperature ratios were both
`1.0008`. The domain energy increase was `4.000000000000001 J` versus the
expected `4 J` (relative error `2.220e-16`). This is an exact constant-source
integration benchmark, not a temporal-order measurement.

## V2 — distributed source-energy conservation

For variable area with nonuniform burn and LHV fields, the reference integrated
combustion power and source integral were both `14701.74677194081 W`; absolute
and relative error were zero at displayed precision. Maximum mass and momentum
combustion-source magnitudes were exactly zero.

## V3 — wall-heat equivalence

Using `q''_w=q'''_comb D_h/4`, P6 wall heating and P8 combustion give identical
volumetric energy sources within this three-equation model. For both Rusanov
and Steger-Warming, RHS and final-state maximum differences were zero. This is
an equivalent-energy-source cross-validation only: wall heating and chemical
combustion are not claimed to be physically identical processes.

## V4 — conservative heat-release scaling

Uniform 1x, 2x, and 4x burn-strength cases produced conservative energy
increments of approximately `100`, `200`, and `400`; the largest ratio error
was `1.164e-12`. This verifies linear conservative energy response only, not
linearity of primitive variables.

## V5–V7 — timestep sensitivity and distributed transient

For a smooth variable-area, prescribed `sin^2` burn profile, each scheme was
compared with its own CFL `0.025` reference. Pressure relative Linf errors for
Rusanov at CFL `0.4/0.2/0.1` were `1.450e-6`, `1.782e-7`, and `2.190e-8`; the
Steger-Warming values were `1.431e-6`, `1.757e-7`, and `2.157e-8`. This is CFL
sensitivity, not a formal RK3-order claim.

At CFL `0.2`, both distributed transients reached `2e-4 s` in 36 steps and
remained finite and positive. Rusanov minima were rho `0.897741`, p
`87543.48 Pa`, T `337.90 K`; Steger-Warming minima were rho `0.895112`, p
`87301.17 Pa`, T `337.55 K`. Scheme relative Linf differences for rho, u, p,
T, and Mach were `0.00501`, `0.00346`, `0.00557`, `0.00111`, and `0.00398`.
Both are physically admissible and qualitatively consistent; no universal
scheme-superiority claim is made.

## V8 — mixed-source robustness

With wall friction/heat, P7 injection, and P8 combustion simultaneously active,
both schemes reached `3e-4 s` in 27 steps with finite, positive states. All
input arrays and geometry arrays remained immutable. Fuel injection and burning
remain independent inputs and may be spatially different.

## Limitations and conclusion

No combustion efficiency multiplier is present because the prescribed burn rate
already represents reacted fuel. No species, inventory, ignition, mixing,
flameholding, reaction-progress, or finite-rate chemistry model exists. The
constant-gamma, constant-R, three-equation homogenized perfect-gas model and
transmissive verification boundaries are retained.

P8.4 validates the prescribed combustion heat-release capability within
controlled cases; overall model V&V, grid studies, and higher-level comparison
remain P10 work. Within these stated limits, P8 completes the prescribed
burned-fuel/LHV heat-release model, solver integration, and controlled formal
validation.
