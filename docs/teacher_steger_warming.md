# Teacher variable-property Steger–Warming path

## Source scope

The teacher Chapter 11 pages photographed in `IMG_2468`–`IMG_2469` freeze the first-order flux-vector-splitting route used after the quasi-one-dimensional governing equation:

- Eq. (11.42): explicit Steger–Warming split-flux vector;
- Eq. (11.43): raw eigenvalue split;
- Eq. (11.44): near-zero eigenvalue smoothing;
- local eigenvalues `lambda_1=u`, `lambda_2=u-c`, `lambda_3=u+c`.

The same source section uses local gas properties. The implementation therefore evaluates `gamma(T,Y)`, `R(Y)`, `c=sqrt(gamma*R*T)` and total enthalpy from the already verified source-backed variable-thermochemistry path.

## Area convention

The textbook writes the conservative equation for the area-weighted state and Eq. (11.42) consequently contains `rho*A/(2*gamma)`. The repository finite-volume residual already multiplies each numerical interface flux by the face area before differencing.

`teacher_variable_steger_warming_split_flux(...)` therefore returns Eq. (11.42) **divided by area**. The later quasi-one-dimensional residual supplies the face-area factor exactly once. This is a representation change only, not a change to the source equation.

## Smoothing epsilon policy

Eq. (11.44) is visible in the supplied source as

`lambda_i^+/- = 0.5 * (lambda_i +/- sqrt(lambda_i^2 + epsilon^2))`.

The photographed evidence does not give a numerical value for `epsilon`. For that reason:

1. the implementation has **no default epsilon**;
2. every split/flux call requires `epsilon_m_per_s` explicitly;
3. `epsilon=0` is supported as the exact Eq. (11.43) raw-splitting limit and for regression against the existing constant-property Steger–Warming implementation;
4. a formal teacher case may use a nonzero epsilon only after the value is documented with provenance or clearly labeled as an explicit modeling choice.

This is preferable to guessing a value and silently changing the teacher scheme.

## Verification boundary

P11.3M verifies the isolated internal-interface operator first. Tests require:

- `lambda^+ + lambda^- = lambda` for the smoothed split;
- exact Eq. (11.43) reduction at `epsilon=0`;
- `F^+ + F^- = F` for real source-backed variable-thermochemistry states;
- reduction to the repository's existing constant-property Steger–Warming implementation;
- finite behavior near a sonic eigenvalue;
- cell-local composition use at interfaces.

This stage does **not** replace the already accepted Rusanov-based integrated teacher solver. Boundary integration and source-enabled SSP-RK3 integration remain separate gates. The Rusanov implementation stays available as a comparator while the teacher FVS path is promoted incrementally.
