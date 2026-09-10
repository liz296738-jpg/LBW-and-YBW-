# P7 Fuel-Injection Formal Validation

## Purpose and reproducibility

P7 provides formal verification and controlled validation of the prescribed
quasi-1D fuel-source model. It does not validate a real scramjet injector or a
combustion process. Run:

```bash
python cases/baseline/p7_4_fuel_injection_validation.py
```

to regenerate machine-readable metrics, CSV tables, plots, and a concise
human-readable report in `results/p7_4/`. The automated hard gates are in
`tests/test_p7_4_fuel_validation.py`; they calculate the metrics from live
solver evaluations rather than testing pre-recorded result files.

## Scope and frozen source model

For prescribed axial fuel mass-flow addition per length
`d(mdot_f)/dx`, the local source is

```text
rho_dot_f = (d(mdot_f)/dx) / A
S_fuel = [rho_dot_f, rho_dot_f * u_f,x, rho_dot_f * h_t,f]
```

Here `u_f,x` is a signed prescribed axial injection velocity and `h_t,f` is
the injected-stream specific total enthalpy. Its kinetic contribution is
already included in the supplied total-enthalpy definition. The solver does
not add an additional `u_f^2 / 2` term.

P7 adds mass, axial momentum, and total enthalpy only. It does not use
`rho_dot_f (u_f - u)`, `rho_dot_f (h_t,f - h_t,gas)`, LHV, heat release, an
injector pressure force, or any combustion term. Production solver physics,
SSP-RK3, CFL selection, flux schemes, and transmissive boundaries remain
unchanged during P7.4.

## V1 — Uniform exact prescribed-source benchmark

V1 uses 20 constant-area cells (`A = 0.02 m^2`) with a uniform initial state
`rho=1 kg/m^3`, `u=500 m/s`, `p=100000 Pa`,
`d(mdot_f)/dx=0.02 kg/(m s)`, and `h_t,f=1e6 J/kg`. Thus `rho_dot_f=1` in SI
units. For a uniform source and transmissive uniform state, numerical flux
divergence is zero and the analytical conservative solution is

```text
U(t) = U(0) + [rho_dot_f, rho_dot_f*u_f,x, rho_dot_f*h_t,f] * t.
```

At `t=1e-4 s`, both Rusanov and Steger-Warming passed for `u_f,x=0` and
`100 m/s`. Density Linf errors were at most `6.661e-16`, momentum Linf errors
at most `5.684e-14`, and energy Linf errors at most `1.164e-10` in their
respective conservative units. All primitive states stayed positive and
finite.

This is a **roundoff-limited exact-source benchmark**, not a formal RK3 order
test. The exact uniform-source benchmark has a constant right-hand side, for
which SSP-RK3 integrates the source to floating-point accuracy. Therefore it
cannot demonstrate third-order temporal convergence. It verifies source
mapping, conservative source integration, both solver branches, and the
absence of unintended extra source terms.

The generated figures explicitly show the analytical conservative profiles
together with both numerical branches for density, momentum, and energy. An
absolute-error figure retains the measured floating-point errors; exact zero
errors are omitted only from its logarithmic display, never replaced in the
metrics.

## V2 — Discrete integrated-source conservation

V2 uses a positive sinusoidally varying area profile with 31 cells, plus
nonuniform arrays for prescribed mass addition, axial velocity, and total
enthalpy. Direct integration of the distributed source verifies

```text
sum(A_i S_rho,i dx) = sum(mprime_i dx)
sum(A_i S_rhou,i dx) = sum(mprime_i u_f,i dx)
sum(A_i S_E,i dx) = sum(mprime_i h_t,f,i dx).
```

The references and numerical integrals were respectively `0.009` and
`0.009 kg/s` for mass, `0.24912110583700403` for axial momentum rate, and
`8215.201843061674 W` for energy rate. All three recorded absolute and
relative errors were zero at displayed floating-point precision. This is
classified as discrete source conservation passed.

## V3 — Source-strength linearity

Using the V1 controlled uniform setup, source strengths of 1x, 2x, and 4x
were run independently for both schemes. Conservative increments are linear:
the Rusanov and Steger-Warming mass ratios were `2.000000000004441` and
`4.000000000015543`; momentum and energy ratios are likewise within about
`1e-11` of 2 and 4. This confirms linear prescribed-source response for
conservative increments only. It does not claim that velocity, pressure,
temperature, or Mach are linear in fuel-source strength.

## V4 — CFL/timestep sensitivity

V4 holds grid, variable area, nonuniform initial condition, prescribed smooth
fuel profile, physics, and flux scheme fixed. It compares CFL `0.4`, `0.2`,
and `0.1` with a same-scheme CFL `0.025` reference at `t=2e-4 s`.

For Rusanov, the maximum of density/pressure/Mach relative Linf differences
was `3.897e-6`, `5.016e-7`, and `6.203e-8`. For Steger-Warming it was
`3.925e-6`, `5.009e-7`, and `6.206e-8`. Both sequences decrease under
refinement and are classified **CFL-convergent**. This is a timestep
sensitivity study against a finer-step reference, not a formal temporal-order
measurement.

## V5 — Controlled nonuniform distributed-injection transient

V5 uses a prescribed smooth `sin^2` mass-addition profile on `0.25 <= x <=
0.75 m`, with variable positive area and nonuniform prescribed velocity and
total enthalpy. This profile is a prescribed mathematical validation profile;
it is not an injector geometry, jet-penetration, spray-distribution, or mixing
model.

At CFL 0.2 both schemes reach `t=2e-4 s` in 22 steps. Rusanov minima are
`rho=0.921225`, `p=90196.232 Pa`, and `T=341.146 K`; Steger-Warming minima are
`rho=0.918203`, `p=89773.654 Pa`, and `T=340.666 K`. Conservative and
primitive states, including Mach, are finite in both runs. The controlled
distributed-injection transient therefore remains finite and physically
admissible.

Because transmissive boundaries do not retain boundary-flux history, V5 is a
physical/numerical smoke validation rather than a claim of a closed global
transient mass balance. V2 provides the strict source-integral conservation
identity.

## V6 — Rusanov / Steger-Warming comparison

On the V5 case, final relative Linf differences between the two schemes are
`5.818e-3` for density, `6.871e-3` for pressure, and `4.893e-3` for Mach.
Both states are physical and retain qualitatively consistent smooth profiles.
This is not a universal accuracy or robustness ranking of the two schemes.
The V6 `both_physical` result is derived directly from the two V5 transient
physical-state flags, rather than being a fixed status value.

## Result artifacts

`results/p7_4/` contains:

- `exact_uniform_metrics.csv`, `integral_conservation_metrics.csv`,
  `strength_scaling_metrics.csv`, `cfl_sensitivity_metrics.csv`, and
  `scheme_comparison_metrics.csv`;
- `metrics.json` and `validation_report.md`;
- `exact_uniform.png`, separate exact-vs-numerical density, momentum, and
  energy plots, plus an absolute-error plot;
- `strength_scaling.png`, `cfl_sensitivity.png`, and `scheme_comparison.png`;
- separate distributed `rho(x)`, `u(x)`, `p(x)`, `T(x)`, and `Mach(x)` plots.

## Limitations and P7 conclusion

The axial fuel mass-flow distribution remains prescribed externally; no
injector geometry, jet penetration, spray, or mixing model determines it.
Fuel remains represented only through mass, axial momentum, and total enthalpy
sources in the existing three-equation homogenized perfect-gas model. No fuel
species transport equation is present. Combustion heat release and LHV remain
outside P7. The timestep remains based only on Euler wave speed; this CFL study
assesses numerical sensitivity but introduces no fuel-specific timestep
limiter. Transmissive boundaries remain verification boundaries rather than
final physical scramjet inlet/outlet conditions.

The accepted P7.4 validation commit passed CI: the full automated regression
suite reported `519 passed in 40.71 s`. The final closure update, including
the visual-integrity hard gate, passes `520` tests locally.

Within the stated scope, P7 has now completed:

- prescribed local fuel-source definition;
- quasi-1D distributed source mapping;
- solver integration and SSP-RK3 stage-wise evaluation;
- exact conservative source verification;
- discrete integral conservation verification;
- source-strength linearity checks;
- CFL/timestep sensitivity assessment;
- controlled distributed-transient checks; and
- Rusanov / Steger-Warming consistency comparison.

Within the documented prescribed-source model limitations, P7 fuel injection
is formally complete. P7 does not include combustion; P8 combustion remains
planned.
