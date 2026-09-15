# Teacher variable-property Steger–Warming path

## Source scope

The teacher Chapter 11 pages photographed in `IMG_2468`–`IMG_2469` freeze the first-order flux-vector-splitting route used after the quasi-one-dimensional governing equation:

- Eq. (11.42): explicit Steger–Warming split-flux vector;
- Eq. (11.43): raw eigenvalue split;
- Eq. (11.44): near-zero eigenvalue smoothing;
- local eigenvalues `lambda_1=u`, `lambda_2=u-c`, `lambda_3=u+c`.

P11.3M transcribes those equations literally and evaluates the local `gamma`, `R`, sound speed and total enthalpy from the already verified variable-thermochemistry state.

## Area convention

The textbook writes the conservative equation for the area-weighted state and Eq. (11.42) consequently contains `rho*A/(2*gamma)`. The repository finite-volume residual already multiplies each numerical interface flux by face area before differencing.

`teacher_variable_steger_warming_split_flux(...)` therefore returns Eq. (11.42) **divided by area**. The later quasi-one-dimensional residual supplies the face-area factor exactly once. This is a representation change only, not a change to the source equation.

## Smoothing epsilon policy

Eq. (11.44) is visible in the supplied source as

`lambda_i^+/- = 0.5 * (lambda_i +/- sqrt(lambda_i^2 + epsilon^2))`.

The photographed evidence does not give a numerical value for `epsilon`. Therefore the implementation has no default; every split/flux call requires `epsilon_m_per_s` explicitly. `epsilon=0` is supported only as the exact Eq. (11.43) raw-splitting limit and as a regression reference. A formal nonzero value needs provenance or an explicit modeling classification.

## Compatibility result discovered by CI

The first full CI run found an important issue that must not be hidden with a looser tolerance.

For a calorically perfect gas, the literal Eq. (11.42) implementation reduces to the repository's existing Steger–Warming operator and recombines correctly. With the project's source-backed temperature-dependent `cp(T)` and **absolute species energy/enthalpy**, however, `F+ + F-` from the literal Eq. (11.42) still reconstructs the mass and momentum fluxes but does **not** exactly reconstruct the physical Euler energy flux. A representative real-mixture test showed an energy-flux difference of about 20.9%.

This is consistent with the fact that the classical closed-form Steger–Warming eigenvector formula assumes the calorically-perfect ideal-gas energy relation. The teacher chapter also asks for temperature/composition-dependent thermochemistry, but the photographed equations currently available do not state how that thermochemistry is reconciled with the classical Eq. (11.42) energy split.

Accordingly, P11.3M does **not** invent a correction term, change the absolute-energy reference, or relax the test. The literal source implementation remains an isolated audit path, while the already accepted Rusanov variable-thermochemistry solver remains the integrated compatibility path.

## Verification boundary

Tests now require:

- `lambda^+ + lambda^- = lambda` for Eq. (11.44);
- exact Eq. (11.43) reduction at `epsilon=0`;
- exact reduction to the existing constant-property Steger–Warming implementation;
- mass/momentum reconstruction for the variable-thermochemistry literal split;
- an explicit regression that records the variable-thermochemistry energy-flux incompatibility instead of concealing it;
- finite near-sonic smoothing behavior;
- cell-local composition use at interfaces.

## Next evidence task

Before Steger–Warming is connected to the teacher boundary/source-enabled solver, the teacher/Cao references need to be re-audited for the actual convention used when temperature-dependent heat capacity and absolute mixture enthalpy are combined with flux-vector splitting. If no source-backed reconciliation is found, the boundary-complete Rusanov path remains the defensible integrated implementation and Steger–Warming stays documented as an unresolved numerical-model compatibility item.
