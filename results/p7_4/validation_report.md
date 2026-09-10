# P7.4 Fuel-Injection Formal Validation Results

This is formal verification and controlled validation of the prescribed quasi-1D fuel-source model. It does not validate a real injector or combustion process.

## Classifications

- V1: roundoff-limited / exact-source benchmark passed.
- V2: discrete source conservation passed.
- V3: linear prescribed-source response confirmed for conservative increments.
- V4 Rusanov: CFL-convergent; Steger-Warming: CFL-convergent.
- V5: controlled distributed-injection transient remains finite and physically admissible.

The exact uniform-source benchmark has a constant right-hand side, for which SSP-RK3 integrates the source to floating-point accuracy. Therefore it cannot be used to demonstrate third-order temporal convergence. The CFL study is reported as timestep sensitivity against a finer-step reference, not as a formal temporal-order measurement.

Fuel total enthalpy is supplied as injected-stream specific total enthalpy; its kinetic contribution is already included and no additional u_f^2/2 term is added.

## Limitations

- The axial fuel mass-flow distribution is a prescribed mathematical validation profile, not an injector geometry, jet-penetration, spray, or mixing model.
- No fuel species transport, LHV, combustion heat release, or chemical kinetics is present.
- The existing three-equation homogenized perfect-gas model and transmissive verification boundaries are retained.

## Generated Metrics

V2 relative integral errors: mass=0.000e+00, momentum=0.000e+00, energy=0.000e+00.
V6 relative Linf differences: rho=5.818e-03, pressure=6.871e-03, Mach=4.893e-03.
