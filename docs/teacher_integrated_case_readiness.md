# Teacher integrated-case readiness

## Purpose

The project has finished the main teacher-reference building blocks. This stage stops adding isolated physics and begins case-level closeout: steady convergence, reproducible integrated runs, grid checks, and source-defined reproduction where the teacher/Cao material actually provides enough input data.

## Accepted integrated path

The current defensible integrated solver uses:

- variable thermochemistry and per-cell teacher H2/C2H4 composition;
- Chapter 11 algebraic `phi -> L_m -> eta_m -> eta -> Y_i` closure;
- single-cell fuel mass/momentum/total-enthalpy addition;
- teacher Eq. (11.25) friction through the verified `f_D=4f` convention;
- static `p/T/u` supersonic inlet;
- first-order/zero-gradient outlet;
- SSP-RK3 pseudo-time marching;
- variable-property CFL timestep;
- Rusanov interface flux.

Rusanov is intentional, not accidental. Literal Chapter 11 Steger-Warming Eqs. (11.42)-(11.44) were transcribed and pass their calorically-perfect limit, but they do not reconstruct the physical Euler energy flux when combined with the project's source-backed temperature-dependent heat capacity and absolute species energy. The teacher/Cao references audited so far do not supply a correction, so no unsourced energy-reference modification is introduced.

## Chapter 11 steady closeout

`src/scramjet1d/teacher_steady_solver.py` adds the case-level steady gate.

The primary stopping criterion is teacher Eq. (11.46):

```text
max_i |(rho_i^(n+1) - rho_i^n) / rho_i^n| <= tolerance
```

Density is read directly from the first conservative component, so the diagnostic is valid for the variable-thermochemistry state without introducing a calorically-perfect gas object.

A separate fixed-scale normalized semi-discrete residual is recorded for robustness auditing. It is not substituted for the teacher stopping criterion.

For the timestep, the teacher source shows Eq. (11.45):

```text
dt = min(dt0, 0.5 * dx / max_i(c_i + |u_i|))
```

The repository `NumericalConfig(cfl=0.5)` matches the spectral factor. The photographed source does not freeze a numerical `dt0`, so the steady wrapper provides an optional explicit `dt_cap_s` and has no guessed cap default.

## Cao doctoral Case 2

The teacher-provided Cao doctoral thesis gives a valuable source-defined transonic H2 benchmark in Section 2.5.4.2, Table 2-2.

Frozen entrance values:

- `Ma2 = 2.12`
- `rho2 = 0.28 kg/m^3`
- `p2 = 46.7 kPa`
- `T2 = 521 K`
- `u2 = 977 m/s`
- reported `k = 1.33`
- `phi = 0.2`
- `YN2 = 0.64`
- `YO2 = 0.22`
- `YH2O = 0.13`
- `YAr = 0.01`
- `Tw = 900 K`
- comparison grids `dx = 0.0001 m` and `0.001 m`

The thesis explicitly says the composition variation is prescribed in advance rather than solved with a selected finite-rate chemical mechanism, while variable heat capacity and multicomponent thermodynamics are evaluated during the calculation.

Machine-readable record:

`cases/studies/data/teacher_cao_case2_source.json`

## Why Case 2 is not yet claimed as reproduced

Two essential spatial inputs are not yet frozen from the source material:

1. the exact Case 2 duct area/geometry profile `A(x)`;
2. the exact prescribed Case 2 species profiles `Yi(x)`.

In addition, Table 2-2 gives a vitiated inlet mixture, whereas the photographed Chapter 11 single-injector H2 composition formula uses its own dry-air basis. These are related model families, but they are not silently interchangeable.

Therefore the repository currently permits a clearly labeled `PROJECT_DEFINED_INTEGRATED_SMOKE_CASE` to exercise the complete Chapter 11 implementation, while `formal_case2_reproduction_ready` remains false.

## Next promotion gate

The next accepted case must:

1. use the boundary-complete Rusanov teacher path;
2. converge under Eq. (11.46) and report the independent normalized residual;
3. keep all primitive states finite, positive, and inside source thermochemistry temperature ranges;
4. audit fuel source bookkeeping and avoid duplicate chemical energy;
5. identify every geometry/mixing/injection value as either source-backed or project-defined;
6. use zero explicit wall heat unless the Eq. (11.26) dimensional mapping is recovered;
7. run a minimum three-level grid study before parameter sweeps.
