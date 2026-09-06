# Project Scope

## Objective

Develop, in validated stages, a quasi-1D compressible-flow CFD solver for scramjet and dual-mode ramjet combustors.

## Non-objectives

Until explicitly approved, this project does not include:

- 2D or 3D CFD
- LES or DNS
- Detailed chemical kinetics
- Structural analysis
- Optimization or control

## Future Inputs

- Axial geometry `x` and area distribution `A(x)`
- Inlet pressure, temperature, and Mach number
- Wall condition
- Fuel-injection position and fuel flow rate
- Equivalence ratio

## Future Outputs

- `rho(x)`, `u(x)`, `p(x)`, `T(x)`, and `Mach(x)`
- Mass-flow consistency
- Residual history
- Convergence information

