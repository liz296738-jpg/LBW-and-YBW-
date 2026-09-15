# P11.2B NASA Burrows–Kurkov Public Validation Candidate

## Status

`PRIMARY PUBLIC VALIDATION ROUTE — SOURCE ROUTE READY, FORMAL REDUCED-ORDER CASE NOT YET READY`

This candidate is introduced to remove the project's dependence on author-held or publisher-gated supplementary data for its first formal P11.2B heated validation. The existing Jin–Liu chain is retained as an advanced evidence-blocked candidate and is not deleted.

The new route uses the NASA Burrows–Kurkov supersonic hydrogen-combustion benchmark because both the primary experiment and NASA's validation archive are publicly accessible and carry traceable source identities.

## Authoritative public sources

### NASA-TM-X-2828 — primary experiment

Marshall C. Burrows and Anatole P. Kurkov, *Analytical and Experimental Study of Supersonic Combustion of Hydrogen in a Vitiated Airstream*, NASA-TM-X-2828, September 1973.

- NTRS record: `https://ntrs.nasa.gov/citations/19730023096`
- NTRS PDF: `https://ntrs.nasa.gov/api/citations/19730023096/downloads/19730023096.pdf`
- NTRS distribution status: `Public`
- NTRS copyright statement: work of the U.S. Government; public use permitted.

The experiment reports detailed probe measurements of total temperature, pressure, and composition at a station `35.6 cm` downstream of hydrogen injection in a Mach `2.44` vitiated stream.

### NASA Glenn Wind-US validation archive — public computational validation package

NASA Glenn's *Burrows and Kurkov Supersonic Combustion: Study #2* is available at:

`https://www.grc.nasa.gov/WWW/wind/valid/bk/study02/bk2.html`

The page exposes the following public assets:

- experimental archive: `exp.tar`
- Wind-US input: `str_run.dat`
- structured grid: `str_run.cgd`
- Wind-US reference solution: `str_run.cfl`
- Wind-US run log: `str_run.lis`

The repository stores only their source URLs and source-backed scalar values at this stage. Binary assets must be ingested through a checksum-bearing manifest before they are used as formal case inputs.

## Source-backed boundary / initial conditions

NASA Study #2 and its public `str_run.dat` expose:

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

The Wind-US input also exposes the vitiated-stream mass fractions:

- `O2 = 0.2576`
- `H2O = 0.2562`
- `N2 = 0.4862`
- `H2 = 0`

The hydrogen stream is pure `H2` in the tracked input.

These are source values or exact unit conversions only. They do not authorize silently replacing the vitiated mixture by calorically perfect air.

## Public experimental validation targets

NASA Study #2 explicitly compares the Wind-US solution to experimental exit-plane profiles of:

- total temperature;
- Mach number;
- `H2O` mole fraction;
- `H2` mole fraction.

For the `2286 R` freestream case, NASA reports an experimental ignition onset of approximately `18 cm` downstream of injection. NASA's documented Wind-US reference solution predicts ignition at about `14 cm` under the selected setup.

The present project may eventually compare Mach and thermal diagnostics after a defensible reduced-order mapping. It **cannot** claim validation of `H2` / `H2O` profiles without species transport and chemistry.

## Why this route is better for the first formal P11.2B case

The Jin–Liu chain remains scientifically useful but is blocked by source identity and missing same-condition numerical inputs. In contrast, the NASA route already provides:

1. a public primary experiment;
2. a public experimental-data archive;
3. a public structured grid;
4. a public solver input deck;
5. a public reference solution;
6. explicit inlet/wall conditions;
7. explicit experimental comparison quantities.

This makes the NASA benchmark a better first target for a reproducible public validation workflow.

## Important model mismatch

The NASA benchmark is not automatically solver-ready for this repository.

NASA Study #2 uses two-dimensional viscous flow, a vitiated multi-species stream, hydrogen injection, finite-rate chemistry, turbulence, and species transport. The repository currently uses a quasi-one-dimensional calorically perfect gas with prescribed source terms.

Therefore this project must not describe a future reduced-order calculation as a direct finite-rate-chemistry reproduction.

## Promotion path

A formal reduced-order NASA case may be created only after the following transformations are explicit, traceable, and regression-tested.

### 1. Quasi-one-dimensional geometry mapping

Derive `A(x)` deterministically from the public NASA grid / geometry asset. Do not hand-copy dimensions from an image when the structured grid is available.

The mapping must record:

- source asset checksum;
- source coordinate units;
- source-to-solver axial origin;
- reduction rule from the two-dimensional channel to quasi-one-dimensional area;
- any excluded injection-plenum region;
- uncertainty / approximation boundaries.

### 2. Effective thermodynamic reduction

The current solver does not model the source species mixture. A formal case therefore needs an explicit effective `gamma`, `R`, and heat-capacity policy or a stronger thermodynamic extension.

The project must not silently set `gamma=1.4`, `R=287` and call that the NASA gas.

### 3. Non-circular line-heat closure

The experiment does not currently supply an explicitly recovered axial `Qdot'(x)` measurement in the repository.

A candidate reduced-order heat-release profile may be derived from the **NASA Wind-US reference solution** if all of the following hold:

- the source `str_run.cfl` is checksum-tracked;
- the reduction is deterministic and reproducible;
- the derivation equations are documented;
- the resulting profile is labelled `NASA_REFERENCE_SOLUTION_DERIVED`;
- it is never relabelled as an experimentally measured heat-release profile;
- experimental Mach / thermal observables are retained as independent comparison targets rather than being used circularly to tune the heat source.

### 4. Experimental archive ingestion

`exp.tar` must be ingested through a manifest before formal comparison. Record at minimum:

- filename;
- SHA-256;
- source URL;
- access date;
- contained file names;
- units;
- coordinate convention;
- parsed output checksum.

### 5. Scope gate

Even after promotion, the highest allowed claim is a **prescribed-heat reduced-order validation against public NASA thermal/flow observables**, with separate comparison to NASA reference fields where computationally derived quantities are used.

The case is not authorized to claim:

- finite-rate chemistry validation;
- species-profile validation;
- detailed transverse mixing validation;
- experimentally measured `Qdot'(x)` unless directly recovered;
- LBW/YBW classification.

## Current machine-readable gate

The source ledger is:

`cases/studies/data/p11_2b_nasa_bk_public_source.json`

The readiness implementation is:

`cases/studies/p11_2b_nasa_bk_readiness.py`

At this stage the expected state is:

```text
public_source_route_ready = true
formal_case_ready = false
lbw_ybw_classification_authorized = false
finite_rate_chemistry_validation_authorized = false
species_validation_authorized = false
```

The remaining work is therefore engineering/scientific model reduction from already-public NASA assets, not private-data acquisition.

## Relationship to Jin–Liu

The Jin–Liu candidate remains in the repository as an advanced validation chain. Its unresolved evidence must remain accurately documented. It is no longer the sole path blocking the project's first public P11.2B formal heated case.

A future project may contain both:

- NASA Burrows–Kurkov: first fully public reduced-order heated validation;
- Jin–Liu: closer scramjet-specific advanced validation if the missing same-condition evidence is later recovered.

## Relationship to P11.3

Burrows–Kurkov does **not** define the project's `LBW` / `YBW` labels. P11.3 must still freeze an authoritative mode-discrimination criterion separately.
