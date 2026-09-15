# Development Rules

## 1. Architecture Authority

The project architecture governs physical models, mathematical equations, numerical methods, and module boundaries. Developers must not alter physical equations for implementation convenience.

The **teacher-provided one-dimensional CFD / second-scheme material is the primary authority for the target project model**. Public papers and benchmark cases may supplement verification, provenance, or missing context, but they must not silently redefine the teacher's requested model.

## 2. Project Naming Is Not Physics

`LBW` and `YBW` are people/project identifiers. They are **not combustion-mode labels**.

Never create an `LBW/YBW classifier`, `LBW/YBW regime map`, or any physical interpretation from the repository name unless the user explicitly changes the project meaning in the future.

## 3. No Silent Physics Changes

Changes to governing equations, source terms, the equation of state, boundary conditions, numerical fluxes, time integration, convergence criteria, mixing/combustion closures, or thermochemical data are physics/numerics changes. They require an explicit rationale in both code and the relevant documentation.

## 4. Conservation First

CFD core modules must preserve mass, momentum, and energy. Do not silently clip state variables or alter conservative quantities to hide errors, avoid NaNs, smooth curves, or pass tests. Any future positivity protection must be explicit, explained, tested, and traceable.

## 5. Chemical-Energy Accounting

The teacher reference distinguishes external wall/additional heat from chemical reaction energy.

The direct prescribed `Qdot'(x)` path is a valid reduced-order surrogate/V&V interface. When a future variable-composition thermochemical formulation represents reaction chemical energy through species/composition-dependent enthalpy, the same chemical energy must **not** also be added through `Qdot'(x)`.

No silent double counting of chemical energy is permitted.

## 6. No Magic Numbers

Physical and numerical parameters (including `gamma`, `R`, CFL, convergence tolerances, empirical closure constants, thermochemical polynomial coefficients, and any Steger-Warming smoothing parameter) must have a single traceable configuration/source. Do not scatter them through algorithms.

In particular, do not invent the near-sonic Steger-Warming smoothing `epsilon`; source or project policy must freeze it first.

## 7. Units

Use SI units throughout: m, s, kg, Pa, K, m/s, J/kg, W/m, and W/m^2 as applicable. Physical inputs and outputs in docstrings must state their units.

## 8. Test Before Expansion

For each new physical model or empirical closure: transcribe/source it, unit-test it independently, validate its dimensions/limits, integrate it, then perform solver-level verification. Do not add multiple complex source terms before their individual behavior is understood.

## 9. Reproducibility

Formal cases must read fixed inputs from `cases/`, run without source edits, and produce reproducible results. Teacher-reference equations/coefficients must be linked to an explicit source locator or evidence ledger.

## 10. Separation of Concerns

Keep gas/thermochemistry, state variables, geometry, numerical fluxes, mixing/combustion closures, source terms, boundary conditions, time advancement, convergence diagnostics, and post-processing separate. Do not consolidate them into a monolithic script.

Generic low-level prescribed source interfaces should remain available when higher-level teacher-reference empirical closures are added.

## 11. Minimal Dependencies

Prefer Python, NumPy, Matplotlib, and pytest. Add SciPy only when justified; do not add large GUI, web, ML, or OpenFOAM-binding dependencies without approval.

## 12. Scientific Naming

Use conventional names such as `rho`, `u`, `p`, `T`, `gamma`, `R`, `E`, `a`, `Mach`, `A`, `phi`, and `eta` where appropriate; avoid meaningless names.

## 13. Supporting V&V Is Not the Deliverable

NASA Burrows-Kurkov, Jin-Liu, and other public cases are useful verification and evidence assets. They must not displace implementation and reproduction of the teacher-provided model. When priorities conflict, close the teacher-reference model gap first unless the user explicitly instructs otherwise.
