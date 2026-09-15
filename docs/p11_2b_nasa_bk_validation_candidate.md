# P11.2B NASA Burrows–Kurkov Public Validation Candidate

## Status

`PRIMARY PUBLIC VALIDATION ROUTE — EXPERIMENT, GEOMETRY, AND EFFECTIVE-GAS POLICY READY; FORMAL LINE-ENERGY CLOSURE PENDING`

This route is now the project's primary path to a first fully public P11.2B heated-flow validation. The Jin–Liu chain remains documented as an advanced evidence-blocked candidate and is not deleted.

The claim boundary remains deliberately narrower than the original NASA computation: the repository solver is quasi-one-dimensional, calorically perfect gas, and uses prescribed source terms. NASA Study #2 is a two-dimensional viscous multi-species finite-rate reacting calculation compared with experiment.

## Public source chain

### Primary experiment

Marshall C. Burrows and Anatole P. Kurkov, *Analytical and Experimental Study of Supersonic Combustion of Hydrogen in a Vitiated Airstream*, NASA-TM-X-2828, September 1973.

- NTRS record: `https://ntrs.nasa.gov/citations/19730023096`
- NTRS distribution: `Public`
- NTRS marks the report as U.S. Government work / public use permitted.

### NASA Glenn validation archive

NASA Glenn, *Burrows and Kurkov Supersonic Combustion: Study #2*:

`https://www.grc.nasa.gov/WWW/wind/valid/bk/study02/bk2.html`

Public assets include `exp.tar`, `str_run.dat`, `str_run.cgd`, `str_run.cfl`, and `str_run.lis`.

## Reproducible asset acquisition

GitHub Actions successfully downloads the NASA assets directly from the official host and records SHA-256 values. The first accepted acquisition record is workflow run `34951670961`, artifact `10389039980`.

Tracked source hashes include:

- `exp.tar`: `8e3a60293b4a16aa821ac839bee8c890871ef415040029c4f573c743f6b9dc89`
- `str_run.dat`: `4ec41f3a4b034839fcd137f7c382528910db16c5db923cff363844fc14abcac2`
- `str_run.cgd`: `255563ffa5cf3afe3fdd791f642842f398c84e4f39936ef62bc92d9bb80b0e91`
- `str_run.cfl`: `e0d9c3c89c40b947934c6ab6a5aa0df1e9f32b22dc7919f81dd9ad391f08e602`

Manifest:

`cases/studies/data/p11_2b_nasa_bk_asset_manifest.json`

Raw multi-megabyte binaries are not committed blindly.

## Experimental data — resolved

`exp.tar` contains four public exit-plane datasets:

- `bkmach.dat`: 14 Mach points;
- `bktemp.dat`: 16 total-temperature points;
- `bkh2.dat`: 27 H2 mole-fraction points;
- `bkh2o.dat`: 28 H2O mole-fraction points.

The checksum-tracked normalized copy is:

`cases/studies/data/p11_2b_nasa_bk_exp_exit_profiles.csv`

All 85 points are retained, including repeated transverse coordinates. These are experimental measurements at the exit plane `x=0.356 m`; they are **not** an axial heat-release curve.

For the `2286 R` freestream condition NASA also reports experimental ignition onset near `0.18 m`; its Wind-US reference computation predicts about `0.14 m`.

## Source inlet / wall conditions — resolved

NASA Study #2 / `str_run.dat` provide:

| Quantity | Vitiated stream | Hydrogen |
| --- | ---: | ---: |
| Mach | 2.44 | 1.0 |
| static pressure | 14.7 psi | 14.7 psi |
| static temperature | 2286 R | 457.2 R |

Exact SI conversions used by the ledger are:

- vitiated-stream pressure: `101352.9322095696 Pa`
- vitiated-stream temperature: `1270 K`
- hydrogen pressure: `101352.9322095696 Pa`
- hydrogen temperature: `254 K`
- wall temperature: `298 K`
- downstream pressure record: `107558.2137734208 Pa`

Vitiated-stream mass fractions are:

- `O2 = 0.2576`
- `H2O = 0.2562`
- `N2 = 0.4862`

The project does not replace this gas silently with `gamma=1.4, R=287` air.

## Quasi-one-dimensional main-duct geometry — resolved

A separate public NASA technical report, NASA-TM-74094, states that the rectangular duct expands linearly from `5.10 cm × 9.38 cm` at the hydrogen-injection station to `5.10 cm × 10.48 cm` at `35.6 cm` downstream. NASA Glenn independently defines `x=0` at the injection step and the combustor length as `35.6 cm`.

The frozen reduced-order geometry is therefore:

- `L = 0.356 m`
- `W = 0.051 m`
- `H(0) = 0.0938 m`
- `H(L) = 0.1048 m`
- `A(0) = 0.0047838 m²`
- `A(L) = 0.0053448 m²`
- `A(L)/A(0) = 1.1172707889125801`

with

`H(x) = H0 + (H1-H0) x/L`

and

`A(x) = W H(x)`.

Source record:

`cases/studies/data/p11_2b_nasa_bk_geometry_source.json`

Implementation:

`cases/studies/p11_2b_nasa_bk_geometry.py`

The hydrogen plenum/slot is not silently added to axial core area, and no boundary-layer displacement correction is hidden in this geometry.

## Effective calorically-perfect gas policy — resolved as a model reduction

The present solver requires constant `R` and `gamma`, while the NASA benchmark is variable-property and reacting. The project therefore freezes a transparent reference-state reduction rather than pretending the gas is ordinary air.

The policy uses:

- the NASA source inlet mass fractions above;
- public Cantera / GRI-Mech 3.0 NASA7 species heat-capacity polynomials;
- the NASA inlet reference temperature `1270 K`.

Derived reference values are:

- `R_eff = 329.4821420180208 J/(kg K)`
- `cp_eff = 1514.961402157982 J/(kg K)`
- `gamma_eff = 1.2779315953440815`

The same fixed inlet composition gives lower effective gamma as temperature rises:

- `gamma(2000 K) ≈ 1.246731798`
- `gamma(2500 K) ≈ 1.235485697`
- `gamma(3000 K) ≈ 1.228362524`

Therefore a future formal result must include at least one lower-gamma heated-range sensitivity case. The `1270 K` reference-gamma run alone is not sufficient for a robustness claim.

Evidence record:

`cases/studies/data/p11_2b_nasa_bk_thermo_reduction.json`

Implementation:

`cases/studies/p11_2b_nasa_bk_thermo.py`

This is explicitly `MODEL_REDUCTION_WITH_SOURCE_BACKED_REFERENCE_PROPERTIES`; it is not a finite-rate thermodynamic reproduction.

## Only active formal blocker: effective axial line-energy closure

The experiment gives transverse exit measurements, not a measured axial `Qdot'(x)` curve. It would be circular to tune heat addition against those same exit Mach / total-temperature data and then call the result validation.

The intended route is instead to derive an **effective one-dimensional energy-source profile** from the checksum-tracked public NASA Wind-US reference solution `str_run.cfl`, while retaining the experimental Mach and total-temperature data as independent comparison targets.

Any such profile must be labelled:

`NASA_REFERENCE_SOLUTION_DERIVED`

or, more specifically, an effective net line-energy source if it includes combined reaction / wall / multidimensional effects. It must never be relabelled as experimentally measured chemical heat release.

A dedicated CGNS probe workflow now attempts to convert the public ADF CGNS reference files to HDF5 and inventory their datasets so the reduction can be deterministic rather than figure-digitized.

## Scope exclusions — not blockers for the thermal/flow claim

The public H2 and H2O profiles remain valuable benchmark context, but the present solver has no species transport or finite-rate chemistry. Therefore species agreement is explicitly outside the formal P11.2B thermal/flow acceptance claim.

Likewise Burrows–Kurkov does not define `LBW` or `YBW`. P11.3 must freeze those definitions separately from authoritative project-specific evidence.

## Highest permitted future claim

If the remaining line-energy closure is completed and the solver result passes the predeclared numerical / applicability checks, the strongest permitted claim is:

**prescribed-energy quasi-one-dimensional validation against public NASA thermal/flow observables, using an explicitly identified NASA-reference-solution-derived closure where necessary.**

It is not authorized to claim:

- finite-rate chemistry validation;
- species-profile validation;
- detailed transverse mixing validation;
- experimentally measured `Qdot'(x)` unless directly recovered;
- LBW/YBW classification.

## Machine-readable state

Primary files:

- `cases/studies/data/p11_2b_nasa_bk_public_source.json`
- `cases/studies/data/p11_2b_nasa_bk_asset_manifest.json`
- `cases/studies/data/p11_2b_nasa_bk_exp_exit_profiles.csv`
- `cases/studies/data/p11_2b_nasa_bk_geometry_source.json`
- `cases/studies/data/p11_2b_nasa_bk_thermo_reduction.json`
- `cases/studies/p11_2b_nasa_bk_readiness.py`

Expected readiness:

```text
public_source_route_ready = true
experimental_archive_ingested = true
source_backed_geometry_ready = true
thermodynamic_reduction_ready = true
formal_case_ready = false
open blocker = non_circular_line_heat_release_closure
species validation = explicitly excluded from the thermal/flow claim
LBW/YBW classification = not authorized by this case
```

## Relationship to Jin–Liu

Jin–Liu remains preserved as an advanced scramjet-specific candidate. Its missing same-condition evidence has not been fabricated. NASA Burrows–Kurkov is now the reproducible public route for the first P11.2B heated thermal/flow validation.
