# Thermochemistry Provenance and Validation Policy

## Scope

This document records where the teacher-reference H2/C2H4 thermochemical data come from and what the repository's automated checks do and do not prove.

## Primary thermochemistry source

The computational coefficient convention is the GRI-Mech 3.0 CHEMKIN/NASA seven-coefficient thermodynamic format released 1999-07-30.

- Berkeley GRI-Mech coefficient file: `http://combustion.berkeley.edu/gri-mech/version30/files30/thermo30.dat`
- Berkeley thermodynamic summary: `https://combustion.berkeley.edu/gri-mech/new21/data/thermo_table.html`
- Reproducible public snapshot used to cross-check exact fixed-format records: `https://github.com/OpenFOAM/OpenFOAM-6/blob/master/tutorials/combustion/reactingFoam/RAS/SandiaD_LTS/chemkin/thermo30.dat`

The OpenFOAM copy is treated as a reproducible snapshot, not as the scientific authority. Its header identifies the file as GRI-Mech Version 3.0 thermodynamics in NASA Polynomial format for CHEMKIN-II.

## Independent checks

The Berkeley thermodynamic summary publishes rounded 298 K molar heat capacities generated from the polynomial database. The repository uses those rounded values only as an independent transcription sanity check. Molecular weights are independently traceable to NIST Chemistry WebBook SRD 69.

These checks are intended to catch wrong species, coefficient transcription, interval selection, unit conversion, and gross data drift. They are not experimental validation of the combustor model.

## Project-defined regression thresholds

The following tolerances are software/data-integrity gates chosen by this project:

- low/high polynomial switch continuity relative tolerance: `1e-5`;
- absolute difference from Berkeley's rounded 298 K Cp table: `0.03 cal/(mol K)`.

They are **not** uncertainty intervals published by GRI-Mech, Berkeley, NIST, Cao, or the teacher material. They must not be used as physical validation error bars.

## Supported and blocked scope

The frozen core database currently contains H2, O2, N2, Ar, H2O, C2H4, and CO2. This is sufficient for the implemented H2/C2H4 teacher-reference thermodynamic path.

`C10H22` remains source-gated. No pseudo-kerosene NASA polynomial is to be invented or borrowed from an unrelated surrogate without a separately justified source and model-compatibility review.

## Energy accounting

The teacher/Cao variable-thermochemistry path uses composition-dependent absolute species enthalpy. Chemical energy represented by composition change must not be silently added a second time through an independent heat-release source. External wall/additional heat remains a separate energy channel.

## Claim boundary

Source-backed thermodynamic properties are one component of the CFD model. Agreement of Cp, molecular weight, or polynomial continuity does not validate combustion, mixing, ignition, shock-train behavior, or engine mode transition. Those require their own model and validation evidence.
