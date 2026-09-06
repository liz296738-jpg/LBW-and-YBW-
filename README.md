# Scramjet 1D CFD

## Project Goal

Develop a quasi-one-dimensional, compressible-flow CFD solver for scramjet and dual-mode ramjet combustors.

## Current Status

Current stage: **P2 — thermodynamics and primitive/conservative state conversion**.

Implemented: ideal calorically perfect gas utilities, primitive/conservative conversions, automated unit tests, and GitHub Actions CI. A production CFD solver has **not** been implemented and this project must not yet be used for research calculations.

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
