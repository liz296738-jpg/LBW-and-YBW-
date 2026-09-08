# Scramjet 1D CFD

## Project Goal

Develop a quasi-one-dimensional, compressible-flow CFD solver for scramjet and dual-mode ramjet combustors.

## Current Status

Current stage: **P4.1 - variable-area geometry representation**.

P3 is complete: ideal-gas thermodynamics, primitive/conservative conversion, Euler physical flux, Rusanov numerical flux, finite-volume spatial residual, SSP-RK3, transmissive boundaries, CFL time stepping, a transient solver loop, a Sod-type shock-tube smoke test, automated tests, and GitHub Actions CI form the constant-area baseline solver.

P4.1 adds immutable `AreaProfile` geometry with positive cell-centred and face-centred areas, a constant-area profile helper, and signed per-cell area changes. Geometry inputs are validated and CI continues to cover the full baseline. Variable-area CFD equations, a quasi-1D residual, and geometric source terms are not assembled yet.

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
