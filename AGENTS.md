# Development Rules

## 1. Architecture Authority

The project architecture governs physical models, mathematical equations, numerical methods, and module boundaries. Developers must not alter physical equations for implementation convenience.

## 2. No Silent Physics Changes

Changes to governing equations, source terms, the equation of state, boundary conditions, numerical fluxes, time integration, or convergence criteria are physics/numerics changes. They require an explicit rationale in both code and the relevant documentation.

## 3. Conservation First

CFD core modules must preserve mass, momentum, and energy. Do not silently clip state variables or alter conservative quantities to hide errors, avoid NaNs, smooth curves, or pass tests. Any future positivity protection must be explicit, explained, tested, and traceable.

## 4. No Magic Numbers

Physical and numerical parameters (including `gamma`, `R`, CFL, and tolerances) must have a single configuration source; do not scatter them through algorithms.

## 5. Units

Use SI units throughout: m, s, kg, Pa, K, m/s, and J/kg. Physical inputs and outputs in docstrings must state their units.

## 6. Test Before Expansion

For each new physical model: implement it, add unit tests, perform physical validation, then proceed to the next model. Do not add multiple complex source terms before validation.

## 7. Reproducibility

Future formal cases must read fixed inputs from `cases/`, run without source edits, and produce reproducible results.

## 8. Separation of Concerns

Keep gas properties, state variables, geometry, numerical fluxes, source terms, boundary conditions, time advancement, and post-processing separate. Do not consolidate them into a monolithic script.

## 9. Minimal Dependencies

Prefer Python, NumPy, Matplotlib, and pytest. Add SciPy only when justified; do not add large GUI, web, ML, or OpenFOAM-binding dependencies without approval.

## 10. Scientific Naming

Use conventional names such as `rho`, `u`, `p`, `T`, `gamma`, `R`, `E`, `a`, `Mach`, and `A`; avoid meaningless names.

