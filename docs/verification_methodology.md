# Verification and Validation Methodology

## Purpose

This project separates **code/solution verification** from **physical validation**. Numerical agreement produced by mesh refinement is not, by itself, experimental validation. Conversely, agreement with an experiment is not meaningful unless numerical error and model/input provenance are controlled.

The project therefore uses the following hierarchy:

1. unit and conservation tests for individual numerical/physical components;
2. analytical or manufactured/controlled benchmark checks where available;
3. iterative-convergence checks for each steady calculation;
4. grid-refinement / discretization-error assessment;
5. comparison with source-backed experimental or published reference data only within the reference case's documented scope.

## Grid-refinement policy

The accepted P11.4 H2 audit uses 20, 40, and 80 cells with constant one-dimensional refinement ratio `r = 2`.

For a scalar quantity of interest `f`, with `f1` the finest-grid value, `f2` the medium-grid value, and `f3` the coarse-grid value, the constant-ratio observed order is

`p = ln(|(f3-f2)/(f2-f1)|) / ln(r)`

when the differences have the same sign and are non-zero.

Generalized Richardson extrapolation is

`f_ext = f1 + (f1-f2)/(r^p-1)`.

The fine-grid Grid Convergence Index is conventionally

`GCI_fine = Fs * |(f2-f1)/f1| / (r^p-1)`.

NASA grid-verification guidance recommends three or more grids to estimate an observed order and commonly uses `Fs = 1.25` when that observed order is credible. When the observed order is not demonstrably reliable/asymptotic, a more conservative two-grid style estimate can use the **nominal method order** and `Fs = 3`. This repository's production spatial reconstruction is first order, so the conservative project audit uses `p_nominal = 1` and `Fs = 3` for the two finest grids; it does **not** silently promote an uncertain observed order into a formal grid-independence claim.

### Current frozen P11.4 evidence

Using the already accepted 20/40/80 H2 record, the observed-order diagnostics for the recorded extrema are approximately:

- maximum temperature: `p ~= 0.507`;
- maximum pressure: `p ~= 0.360`;
- minimum Mach number: `p ~= 0.274`;
- maximum Mach number: `p ~= 1.227`.

Because the observed behavior is not uniformly consistent with a stable nominal first-order asymptotic regime, the project continues to describe this evidence as a **grid-convergence trend**, not formal grid independence.

Using the two finest grids, nominal first-order `p=1`, and conservative `Fs=3`, the corresponding fine-grid GCI-style estimates are approximately:

- maximum temperature: `0.633%`;
- maximum pressure: `2.027%`;
- minimum Mach number: `1.573%`;
- maximum Mach number: `0.414%`.

These are discretization-uncertainty indicators for the stated project-defined quantities, not experimental error bars and not proof that Cao Case 2 has been reproduced.

## Experimental/reference validation boundary

The NASA Burrows--Kurkov hydrogen supersonic-combustion experiment is retained as a supporting validation reference because it includes measured pressure, temperature/composition information and a well-documented Mach-2.44 vitiated-air configuration. It is not substituted for the teacher-defined/Cao geometry or operating conditions.

The teacher Chapter 11 material and Cao references remain authoritative for the requested project model. Supporting public experiments can test trends or reduced-order behavior only where geometry, operating conditions, measured quantities, and model assumptions are compatible.

## References

- ASME V&V 20, *Standard for Verification and Validation in Computational Fluid Dynamics and Heat Transfer*. https://www.asme.org/codes-standards/find-codes-standards/standard-for-verification-and-validation-in-computational-fluid-dynamics-and-heat-transfer
- NASA/TM-2000-209946, *Examining Spatial (Grid) Convergence*. https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html
- NASA/TM-20220008781, *VULCAN-CFD User Manual*, section 25.9, Grid Convergence Index Extraction. https://ntrs.nasa.gov/citations/20220008781
- M. C. Burrows and A. P. Kurkov, *Analytical and Experimental Study of Supersonic Combustion of Hydrogen in a Vitiated Airstream*, NASA-TM-X-2828, 1973. https://ntrs.nasa.gov/citations/19730023096

## Claim discipline

- A decreasing coarse-to-fine difference is evidence of a trend, not automatically asymptotic convergence.
- GCI is a discretization-error/uncertainty measure; it is not a physical validation metric.
- Experimental comparison is reported only for measured quantities and compatible conditions.
- Missing teacher/source inputs remain explicit blockers. No parameter is inferred merely to obtain a visually smoother curve or a preferred conclusion.
