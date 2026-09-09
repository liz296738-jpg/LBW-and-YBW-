# P5 Steger-Warming Validation and Comparison

## Purpose

P5 validates the existing first-order quasi-1D solver with raw Steger-Warming flux-vector splitting against the Rusanov baseline. It changes no governing equation, geometry source, boundary condition, CFL calculation, or SSP-RK3 integrator.

## Controlled Conditions

For every Rusanov/Steger-Warming pair, the gas model, geometry, grid, initial state, transmissive boundary treatment, CFL (`0.5`), SSP-RK3, final time, and quasi-1D source discretization are identical. Only `flux_scheme` changes.

## Case A — Isentropic Residual Convergence

The P4.4 `isentropic_nozzle_reference` is evaluated on separate non-sonic branches (`M_in=0.5` and `M_in=2.0`) using 80/160/320 cells. The interior momentum RMS residual decreases monotonically for both schemes. Final observed orders are 0.999/1.000 for Rusanov (sub/supersonic) and 1.000/1.000 for Steger-Warming, confirming first-order spatial behavior.

## Case B — Smooth Entropy-Wave Transient

The fully right-going supersonic Gaussian entropy wave has `rho0=1 kg m^-3`, `p0=100000 Pa`, `u0=800 m s^-1`, amplitude `0.1`, center `0.25 m`, and width `0.05 m`. It translates by `0.10 m` without reaching a boundary. Density-L1 errors at 80/160/320 cells are respectively `0.003764/0.002327/0.001328` for Rusanov and `0.002935/0.001731/0.000956` for Steger-Warming. Final observed orders are `0.810` and `0.857`; both are consistent with spatial first-order dominance.

## Case C — Supersonic Contact Dissipation

At 200 cells, the contact has `rho_L=1`, `rho_R=0.6 kg m^-3`, `u=800 m s^-1`, and `p=100000 Pa`; both sides satisfy `u-a>0`. At the common final time, density L1 error is `0.011149` for Rusanov and `0.009004` for Steger-Warming. Transition widths are 18 and 14 cells. Thus, for this controlled fully supersonic advected-contact benchmark only, Steger-Warming is less diffusive. This is not a claim of universal superiority.

## Case D — Shock and Near-Sonic Robustness

Both schemes reach `t=0.0004 s` in the 200-cell Sod-type case and retain finite, positive density, pressure, and temperature. Maximum absolute Mach is `0.897` (Rusanov) and `0.919` (Steger-Warming). Raw Steger-Warming also reaches the near-sonic smoke-case final time at Mach 0.95, 1.00, and 1.05 with positive finite states; minimum density is approximately `0.99996 kg m^-3` and minimum pressure is `100000 Pa`.

## Reproducibility and Results

Run `python cases/baseline/p5_flux_scheme_comparison.py`. The script creates `results/p5_4/metrics.json`, two convergence CSV files, and comparison plots. The JSON values are the source for the values reported above.

## Limitations

Raw Steger-Warming remains unsmoothed at sonic eigenvalues. Spatial reconstruction is first-order piecewise constant. Transmissive boundaries are validation boundaries, not final physical scramjet inlet/outlet conditions. No entropy fix, limiter, higher-order reconstruction, friction, heat transfer, fuel injection, or combustion is added by P5.

## Conclusion

All P5.4 acceptance cases pass under the controlled conditions above. P5 is complete; P6 will address wall friction and heat transfer as a separate model stage.
