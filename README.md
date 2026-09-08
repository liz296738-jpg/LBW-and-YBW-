# Scramjet 1D CFD

## Project Goal

Develop a quasi-one-dimensional, compressible-flow CFD solver for scramjet and dual-mode ramjet combustors.

## Current Status

Current stage: **P5.2 - Steger-Warming interface numerical flux**.

P3 is complete: ideal-gas thermodynamics, primitive/conservative conversion, Euler physical flux, Rusanov numerical flux, finite-volume spatial residual, SSP-RK3, transmissive boundaries, CFL time stepping, a transient solver loop, a Sod-type shock-tube smoke test, automated tests, and GitHub Actions CI form the constant-area baseline solver.

P4.1 adds immutable `AreaProfile` geometry with positive cell-centred and face-centred areas, a constant-area profile helper, and signed per-cell area changes. P4.2 adds area-weighted face-flux divergence, the normalized geometric momentum source, and their quasi-1D semi-discrete residual. P4.3 assembles transmissive baseline boundaries, Rusanov interface fluxes, the quasi-1D residual, CFL stepping, and SSP-RK3 into a variable-area transient solver. P4.4 adds an isentropic area-Mach analytical reference, branch-specific area-response validation, mass-flow and stagnation-property checks, exact-face residual convergence, and first-order Rusanov interior convergence.

P4 validates inviscid, adiabatic, constant-gamma quasi-1D area physics. P5.1 adds Euler characteristic speeds and unsmoothed Steger-Warming positive/negative single-state flux splitting. P5.2 adds the two-state, first-order flux-vector-splitting interface law `F_hat = F_plus(U_left) + F_minus(U_right)`, including equal-state consistency, supersonic upwinding, and vectorized broadcasting tests.

Steger-Warming interface flux exists but is not yet connected to the CFD spatial operator or solver: the production CFD solver remains Rusanov. The transmissive boundary is a baseline verification boundary, not a physical scramjet inlet/outlet model; friction, wall heat transfer, fuel injection, combustion, chemistry, and entropy/sonic treatment remain future work.

## Planned Physics

- Compressible flow
- Variable-area duct
- Wall friction
- Heat transfer
- Fuel injection
- Combustion

Each item will be introduced and validated in a separate stage.

## Planned Numerical Methods

- Steger-Warming flux vector splitting (FVS)
- Upwind discretization
- Third-order TVD / SSP Runge-Kutta time integration
- CFL-based time stepping

These methods are documented as plans only and are not yet implemented.

## Development Philosophy

Each physical model is introduced independently and validated before the next model is added. See `docs/` for the frozen scope, baseline model, numerical-method plan, and staged roadmap.
