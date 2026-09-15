# P11.2B NASA Burrows–Kurkov public heated benchmark

## Current status

`FORMAL REDUCED-ORDER REFERENCE BENCHMARK ACCEPTED — INDEPENDENT EXPERIMENTAL BULK-STATE VALIDATION NOT CLAIMED`

NASA Burrows–Kurkov is now the project's reproducible public P11.2B heated-flow benchmark route. The Jin–Liu chain remains preserved as an advanced scramjet-specific evidence-blocked candidate.

The accepted scope is deliberately narrow: the repository solver is quasi-one-dimensional and calorically perfect-gas with prescribed reduced-order source terms, while NASA Study #2 is a two-dimensional viscous, multi-species, finite-rate reacting computation compared with experiment.

## Public source chain

Primary experiment:

Marshall C. Burrows and Anatole P. Kurkov, *Analytical and Experimental Study of Supersonic Combustion of Hydrogen in a Vitiated Airstream*, NASA-TM-X-2828, September 1973.

NASA Glenn public validation archive:

`https://www.grc.nasa.gov/WWW/wind/valid/bk/study02/bk2.html`

Tracked public assets include `exp.tar`, `str_run.dat`, `str_run.cgd`, and `str_run.cfl`. Acquisition is checksum-tracked; raw multi-megabyte binaries are not blindly committed.

## Experimental data

The public `exp.tar` archive has been ingested reproducibly and contains 85 exit-plane probe points:

- Mach: 14 points;
- total temperature: 16 points;
- H2 mole fraction: 27 points;
- H2O mole fraction: 28 points.

Normalized copy:

`cases/studies/data/p11_2b_nasa_bk_exp_exit_profiles.csv`

These are transverse exit profiles, not an axial heat-release curve. Because the present solver produces one cross-sectionally reduced state, the project does **not** manufacture an unsupported scalar experimental Mach/temperature average and call it a formal validation target.

## Geometry and thermodynamic reduction

The frozen reduced-order main duct is source-backed:

- `L = 0.356 m`
- `W = 0.051 m`
- `H(0) = 0.0938 m`
- `H(L) = 0.1048 m`
- `A(0) = 0.0047838 m²`
- `A(L) = 0.0053448 m²`

The reference calorically-perfect effective-gas model is:

- `R_eff = 329.4821420180208 J/(kg K)`
- `cp_eff = 1514.961402157982 J/(kg K)`
- `gamma_eff = 1.2779315953440815`

A lower-gamma heated-range sensitivity case is retained because the result is materially sensitive to this model reduction.

## Wind-US Common File reduction

The public NASA reference files are legacy Wind-US Common Files rather than ordinary modern CGNS semantic datasets. The repository therefore uses a checksum-preserving compatibility copy plus low-level ADF access and repository-owned extraction code.

The accepted extraction:

- parses main-duct zones 2–8;
- dimensionalizes fields from the source `VSCLST/REFARR` scaling metadata;
- produces 127 raw section records / 121 unique axial stations;
- verifies the main-duct mass-flow span is below 0.5%;
- never modifies the checksum-frozen NASA source files.

## Reduced-domain inlet

The one-dimensional domain begins at the hydrogen-injection station `x=0`. The upstream freestream condition is therefore not silently reused as the reduced-domain inlet.

Instead the inlet is a conservative moment match to the NASA reference section, matching:

- mass flow;
- axial momentum flux;
- effective specific total enthalpy.

Reference-gamma effective inlet:

- `Mach = 2.4227590058`
- `T = 1247.5108 K`
- `p = 97.1469 kPa`
- `u = 1755.909 m/s`
- `mdot = 1.985307 kg/s`

## Signed reduced-order closures

Two separate computational-reference-derived closures are frozen:

1. signed net line-energy source, derived from the NASA reference effective-total-enthalpy history;
2. signed net axial-momentum residual, derived from the NASA reference axial momentum flux after accounting for the quasi-1D pressure-area contribution.

Both are labelled `NASA_REFERENCE_SOLUTION_DERIVED`. They are **not** relabelled as measured chemical heat release, Darcy friction, wall shear, or experimental data.

The existing nonnegative production combustion heat-release interface remains unchanged.

## Conservative exit target

For internal reduced-order consistency, the correct one-dimensional target is the primitive state reconstructed from the same frozen conservative exit moments, rather than separately mixing a mass-flux-weighted Mach, area-weighted pressure, and mass-flux-weighted temperature from a strongly nonuniform 2D section.

Reference-gamma conservative exit target:

- `Mach = 2.4310586215`
- `p = 87.1975 kPa`
- `T = 1263.2298 K`

Record:

`cases/studies/data/p11_2b_nasa_bk_reference_exit_reduction.json`

## Accepted numerical result

The primary 80-cell reference-gamma candidate converges with residual below `1e-7`, stays supersonic throughout, and gives approximately:

- minimum Mach: `2.4065`
- exit Mach: `2.41720`
- exit pressure: `87.923 kPa`
- exit temperature: `1269.74 K`
- energy-integral mismatch: `1.46e-11 W`
- momentum-integral mismatch: `0 N`

A 40/80/160/320-cell grid study is also accepted. At 320 cells the conservative-target relative errors are approximately:

- Mach: `-0.567%`
- pressure: `+0.827%`
- temperature: `+0.512%`

The 160-to-320 relative changes are of order `1e-5`, so the remaining ~0.5–0.8% discrepancy is stable reduced-order/model-closure error rather than unresolved mesh error.

Acceptance record:

`cases/studies/data/p11_2b_nasa_bk_benchmark_acceptance.json`

Detailed report:

`docs/p11_2b_nasa_bk_benchmark_acceptance.md`

## Meaning of `formal_case_ready=false` in the older readiness gate

`cases/studies/p11_2b_nasa_bk_readiness.py` was originally written as a gate toward a stronger experimental-validation claim. That stronger claim remains intentionally **false** because the experimental exit data are nonuniform probe profiles and the current solver does not provide species transport or a justified experimental bulk-state reduction.

This does not conflict with the new benchmark acceptance:

- `benchmark_ready = true` means the public NASA computational-reference-derived reduced-order benchmark is accepted;
- `formal_experimental_validation_ready = false` means the project does not overstate that benchmark as independent experimental bulk-state validation.

## Explicit claim boundary

Accepted:

- public-data provenance and deterministic extraction;
- quasi-1D geometry and effective-gas reduction;
- conservative moment-matched inlet and exit targets;
- signed reference-derived energy and momentum closures;
- convergence, conservation, grid-refinement, and gamma-sensitivity evidence;
- reduced-order heated-flow solver/reduction consistency benchmark.

Not accepted:

- finite-rate chemistry validation;
- H2/H2O species-profile validation;
- experimentally measured `Qdot'(x)`;
- wall-friction identification from the effective momentum residual;
- independent experimental validation of a single 1D bulk Mach/temperature scalar;
- LBW/YBW classification.

## Transition to P11.3

P11.3 is now authorized to begin **definition-first**. Before implementing any LBW/YBW classifier or regime map, the project must freeze authoritative evidence for:

1. what LBW and YBW mean;
2. the observable(s) used to distinguish them;
3. transition threshold(s) or criterion;
4. applicability to the relevant combustor/operating regime;
5. uncertainty and limitations.

A sonic crossing or `Mach < 1` must not be silently equated with LBW/YBW unless authoritative evidence explicitly supports that mapping.
