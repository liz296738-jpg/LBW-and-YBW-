# P11.2B NASA Burrows–Kurkov Public Validation Candidate

## Status

`PRIMARY PUBLIC VALIDATION ROUTE — PUBLIC EXPERIMENTAL DATA INGESTED, FORMAL REDUCED-ORDER CASE NOT YET READY`

This candidate removes the project's dependence on author-held or publisher-gated supplementary data for its first formal P11.2B heated validation. The existing Jin–Liu chain remains an advanced evidence-blocked candidate and is not deleted.

The new route uses the NASA Burrows–Kurkov supersonic hydrogen-combustion benchmark because both the primary experiment and NASA's validation archive are publicly accessible and traceable.

## Authoritative public sources

### NASA-TM-X-2828 — primary experiment

Marshall C. Burrows and Anatole P. Kurkov, *Analytical and Experimental Study of Supersonic Combustion of Hydrogen in a Vitiated Airstream*, NASA-TM-X-2828, September 1973.

- NTRS record: `https://ntrs.nasa.gov/citations/19730023096`
- NTRS PDF: `https://ntrs.nasa.gov/api/citations/19730023096/downloads/19730023096.pdf`
- NTRS distribution status: `Public`
- NTRS copyright statement: work of the U.S. Government; public use permitted.

The experiment reports detailed probe measurements of total temperature, pressure, and composition at a station `35.6 cm` downstream of hydrogen injection in a Mach `2.44` vitiated stream.

### NASA Glenn Wind-US validation archive

NASA Glenn's *Burrows and Kurkov Supersonic Combustion: Study #2* is available at:

`https://www.grc.nasa.gov/WWW/wind/valid/bk/study02/bk2.html`

The archive exposes:

- `exp.tar` — experimental exit profiles;
- `str_run.dat` — Wind-US input deck;
- `str_run.cgd` — structured grid;
- `str_run.cfl` — NASA reference solution;
- `str_run.lis` — run log.

## Reproducible public-asset acquisition

GitHub Actions workflow run `34951670961` successfully downloaded the public NASA assets directly from the official NASA Glenn host and uploaded them as workflow artifact `10389039980`.

Tracked source-file checksums include:

- `exp.tar`: `8e3a60293b4a16aa821ac839bee8c890871ef415040029c4f573c743f6b9dc89`
- `str_run.dat`: `4ec41f3a4b034839fcd137f7c382528910db16c5db923cff363844fc14abcac2`
- `str_run.cgd`: `255563ffa5cf3afe3fdd791f642842f398c84e4f39936ef62bc92d9bb80b0e91`
- `str_run.cfl`: `e0d9c3c89c40b947934c6ab6a5aa0df1e9f32b22dc7919f81dd9ad391f08e602`

The complete manifest is stored at:

`cases/studies/data/p11_2b_nasa_bk_asset_manifest.json`

Raw multi-megabyte binary assets are not committed blindly to the repository.

## Experimental data now ingested

`exp.tar` contains four public experimental files:

- `bkmach.dat` — 14 Mach measurements;
- `bktemp.dat` — 16 total-temperature measurements;
- `bkh2.dat` — 27 H2 mole-fraction measurements;
- `bkh2o.dat` — 28 H2O mole-fraction measurements.

The original member SHA-256 values and point counts are tracked in the asset manifest. A normalized SI-coordinate copy preserving every data point, including repeated experimental coordinates, is stored at:

`cases/studies/data/p11_2b_nasa_bk_exp_exit_profiles.csv`

This closes the **experimental archive ingestion** requirement. The data remain transverse exit-plane measurements at `x=0.356 m`; they are not an axial heat-release profile.

## Source-backed boundary / initial conditions

NASA Study #2 and `str_run.dat` expose:

| Quantity | Freestream | Hydrogen |
| --- | ---: | ---: |
| Mach | 2.44 | 1.0 |
| static pressure | 14.7 psi | 14.7 psi |
| static temperature | 2286 R | 457.2 R |

Exact SI conversions tracked in the source ledger are:

- freestream static pressure: `101352.9322095696 Pa`
- freestream static temperature: `1270 K`
- hydrogen static pressure: `101352.9322095696 Pa`
- hydrogen static temperature: `254 K`
- wall temperature: `298 K`
- downstream pressure record: `107558.2137734208 Pa`

The vitiated-stream mass fractions in the Wind-US source input are:

- `O2 = 0.2576`
- `H2O = 0.2562`
- `N2 = 0.4862`
- `H2 = 0`

The hydrogen stream is pure `H2`.

These values do not authorize silently replacing the vitiated mixture by calorically perfect air.

## Public experimental validation targets

The ingested experimental dataset provides exit-plane profiles of:

- total temperature;
- Mach number;
- H2O mole fraction;
- H2 mole fraction.

NASA also reports an experimental ignition onset of approximately `18 cm` downstream of injection for the `2286 R` freestream case. The documented Wind-US reference computation predicts approximately `14 cm`.

The present solver can eventually compare reduced-order Mach and thermal diagnostics after a defensible reduction. It cannot claim validation of H2/H2O profiles without species transport and chemistry.

## Why this route is the primary public path

The NASA route now has:

1. a public primary experiment;
2. a checksum-tracked public experimental archive;
3. normalized experimental exit data in the repository;
4. a public structured grid;
5. a public solver input deck;
6. a public NASA reference solution;
7. explicit inlet/wall conditions;
8. explicit experimental comparison quantities.

This is a materially stronger reproducibility position than the still evidence-blocked Jin–Liu chain for the project's first formal P11.2B validation.

## Important model mismatch

NASA Study #2 is a two-dimensional viscous, multi-species, hydrogen-injection, finite-rate reacting flow. The repository currently uses a quasi-one-dimensional calorically perfect gas with prescribed source terms.

Therefore a future reduced-order calculation must not be described as a direct finite-rate-chemistry reproduction.

## Remaining formal-promotion requirements

### 1. Quasi-one-dimensional geometry mapping

Derive `A(x)` deterministically from the public `str_run.cgd` grid/geometry. Do not hand-copy dimensions from a plot when the source grid is available.

The mapping must record the grid checksum, source units, axial origin, two-dimensional-to-one-dimensional reduction rule, treatment of the injection region, and approximation boundaries.

### 2. Effective thermodynamic reduction

The current solver does not model the vitiated source mixture. A formal case needs an explicit effective `gamma`, `R`, and heat-capacity policy or a stronger thermodynamic extension.

The project must not silently set `gamma=1.4`, `R=287` and call that the NASA gas.

### 3. Non-circular line-heat closure

The ingested experiment supplies exit profiles, not a measured axial `Qdot'(x)` distribution.

A candidate reduced-order heat-release profile may be derived from the public **NASA Wind-US reference solution** only if:

- `str_run.cfl` remains checksum-tracked;
- the field reduction is deterministic and reproducible;
- the derivation equations are documented;
- resulting quantities are labelled `NASA_REFERENCE_SOLUTION_DERIVED`;
- they are never relabelled as experimentally measured heat release;
- the experimental exit Mach/temperature profiles remain independent validation targets and are not used circularly to tune the heat source.

### 4. Species-scope gate

The public H2 and H2O data remain in the benchmark record, but species-profile validation is outside the present solver capability.

## Highest permitted future claim

Even after formal promotion, the strongest permitted claim is:

**prescribed-heat quasi-one-dimensional validation against public NASA thermal/flow observables, with separately identified NASA-reference-solution-derived closure data where required.**

The case is not authorized to claim:

- finite-rate chemistry validation;
- species-profile validation;
- detailed transverse mixing validation;
- experimentally measured `Qdot'(x)` unless directly recovered;
- LBW/YBW classification.

## Current machine-readable gate

Source ledger:

`cases/studies/data/p11_2b_nasa_bk_public_source.json`

Asset manifest:

`cases/studies/data/p11_2b_nasa_bk_asset_manifest.json`

Normalized experiment:

`cases/studies/data/p11_2b_nasa_bk_exp_exit_profiles.csv`

Readiness implementation:

`cases/studies/p11_2b_nasa_bk_readiness.py`

Expected state:

```text
public_source_route_ready = true
experimental_archive_ingested = true
formal_case_ready = false
lbw_ybw_classification_authorized = false
finite_rate_chemistry_validation_authorized = false
species_validation_authorized = false
```

The remaining blockers are now model-reduction tasks over already-public data, not private-data acquisition.

## Relationship to Jin–Liu

The Jin–Liu candidate remains documented as an advanced chain whose missing same-condition evidence has not been fabricated. It is no longer the sole path to the project's first public P11.2B formal heated case.

## Relationship to P11.3

Burrows–Kurkov does **not** define the project's `LBW` / `YBW` labels. P11.3 must still freeze an authoritative mode-discrimination criterion separately.
