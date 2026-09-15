# P11.2 Authoritative Source and Baseline Gap Report

## Status

`P11.2A UNBLOCKED — SOURCE-BACKED PUBLIC SURROGATE AVAILABLE`

`P11.2B REACTIVE CAO-THESIS REPRODUCTION STILL BLOCKED — AXIAL SOURCE PROFILE REQUIRED`

The earlier report concluded that the project-designated Cao Ruifeng material did
not expose enough source-grounded geometry and axial source data to construct a
complete reactive baseline without inventing inputs. A targeted web search has
now identified a publicly accessible, dimensioned scramjet experiment that can
serve as an explicitly labelled **surrogate physical baseline** for P11.2A.

This does **not** replace the teacher-designated Cao papers and must not be cited
as a reproduction of their cases. It provides a defensible way to continue the
physical-baseline and one-factor study infrastructure while keeping the missing
reactive closure visible.

The machine-readable source ledger is:

`cases/studies/data/p11_2_public_surrogate_source.json`

## Source Inventory

| source_id | title | type | locator | project authority | usable now | notes |
| --- | --- | --- | --- | --- | --- | --- |
| SRC01 | Teacher instruction record | screenshot | local project screenshots | Teacher/project instruction | Yes, for source selection | Confirms modelling should ultimately be grounded in the group-provided Cao Ruifeng papers. No numerical physical input. |
| SRC02 | *Research on Combustion Mode Transition and Its Control Method for Scramjet Engines* | doctoral thesis, Cao Ruifeng, 2016 | local PDF | Project-designated thesis | Partial | Table 2-1 supplies an idealized inlet; Table 3-2 supplies kerosene LHV; Table 5-1 supplies candidate ground-test inlet conditions. |
| SRC03 | *Research on One-Dimensional Modeling of Scramjet Engine for Control* | master's thesis, Cao Ruifeng | local PDF | Project-designated thesis | Partial | Establishes one-dimensional modelling context but no complete solver-ready baseline was located. |
| SRC04 | *Theory and Application of Hypersonic Aerodynamic Layout*, Chapter 11 | photographed textbook pages | local images | Project-provided reference | Partial | Supports generalized one-dimensional source-term semantics, not a complete numerical case. |
| SRC05 | Project solver and verification records | code/docs | repository | Project implementation record | Yes | Provides accepted numerical capability, not external physical inputs. |
| SRC06 | Li et al., *Sensitive factors of ethylene combustion heat release under different combustion modes in scramjet engine*, Acta Aeronautica et Astronautica Sinica 46(4), 2025, 130944, DOI 10.7527/S1000-6893.2024.30944 | peer-reviewed experimental paper | public article page, Tables 1–4 and Fig. 2 | External surrogate source | **Yes for P11.2A** | Supplies dimensioned geometry, inflow total conditions, fuel-flow operating points, injector-module selection, and four published one-factor geometry/injection changes. |

## Confirmed Cao-thesis numerical records

The following values remain useful evidence records from `SRC02`:

- Chapter 2, Table 2-1: `Ma2 = 2`, `rho2 = 0.7736 kg/m^3`,
  `p2 = 156.522 kPa`, `T2 = 705 K`, `u2 = 1038 m/s`, `k = 1.33`, and
  `phi = 0.3` for an idealized case.
- Chapter 3, Table 3-2: `gamma = 1.4` and kerosene `Hf = 42,000 kJ/kg`
  for that cycle-analysis model.
- Chapter 5, Table 5-1: isolator-entry Mach, pressure, total temperature,
  and air mass flow for ground-test flight-Mach settings 4–7.

These remain evidence records only. They are not permission to invent the
missing geometry or axial fuel/burn distributions for a Cao-thesis reproduction.

## Public surrogate baseline evidence (SRC06)

The public experimental source provides the following directly locatable inputs.
All dimensional values below are stored in SI units in the JSON source ledger.

### Inflow — Table 1

- Mach number: `2.52`
- Total temperature: `1650 K`
- Total pressure: `1.34 MPa`
- Vitiated-air mass fractions: `O2=23.38%`, `H2O=6.22%`, `CO2=10.16%`,
  `N2=60.24%`

For the repository's current calorically-perfect single-gas model, composition
is recorded as evidence but is not yet represented by species transport. If the
existing model assumption `gamma=1.4`, `R=287 J/(kg K)` is retained, the
isentropic conversion of the Table-1 total state at Mach 2.52 gives an initial
single-gas approximation of approximately:

- `T = 726.85 K`
- `p = 76.03 kPa`
- `rho = 0.36445 kg/m^3`
- `u = 1361.84 m/s`

These four values are **derived model inputs**, not measured Table-1 quantities,
and must be tagged as such in any generated artifact.

### Geometry — Fig. 2 / Table 2

The source provides a dimensioned baseline configuration, including:

- `L1 = 560 mm`
- `L2 = 140 mm`
- `L3 = 490 mm`
- width `W = 50 mm`
- heights `H1 = 35 mm`, `H2 = 42 mm`
- cavity length `Lc = 70 mm`
- cavity depth `Dc = 21 mm`
- cavity/ramp dimension `Hc = 21 mm`
- injection distances `d1 = 42 mm`, `d2 = 21 mm`, `d3 = 14 mm`
- cavity ramp angle `45 deg`

The repository is quasi-one-dimensional and therefore cannot represent the
cavity recirculation volume directly. A future P11.2A case may map the external
core-flow channel to `A(x)=W*H(x)` only where Fig. 2 unambiguously defines the
local channel height. Any cavity-volume treatment beyond that is a modelling
choice and must be documented separately rather than presented as source data.

### Operating points — Table 3

The experiment reports total ethylene mass flow and injector module selections
for equivalence ratios `0`, `0.13`, `0.15`, `0.19`, `0.27`, `0.35`, and `0.41`.
For example, the source gives `6.1 g/s` at `phi=0.13` using `J1/J2`, and
`19.1 g/s` at `phi=0.41` using `J2/J3`.

These are valuable physical records, but they are **not yet sufficient to turn
on the repository's P7/P8 source terms** because the current solver also needs:

- an axial mass-source distribution, not only total fuel flow,
- fuel axial velocity,
- fuel specific total enthalpy,
- and an independently prescribed burned-fuel or heat-release distribution.

The source therefore supports a documented fuel-flow target and operating point,
but not an invented source-profile shape.

### Published one-factor variations — Table 4

SRC06 directly closes the earlier OFAT-level gap for several physical factors:

- isolator length: `560 -> 280 mm`, at `phi = 0.13, 0.19, 0.27`
- injection distance: `21 -> 42 mm`, at `phi = 0.13, 0.19, 0.27`
- cavity depth: `21 -> 10 mm`, at `phi = 0.13, 0.19, 0.27, 0.35, 0.41`
- throat size: `Hc 21 -> 16.8 mm`, with corresponding `H 35 -> 39.2 mm`,
  at `phi = 0.13, 0.19, 0.27, 0.35, 0.41`

Thus at least two source-supported non-baseline physical factor levels are now
available without arbitrary numerical ranges.

## What is now unblocked

P11.2 may proceed in two explicitly separated tracks:

1. **P11.2A — source-backed physical cold-flow / geometry surrogate**
   - freeze SRC06 geometry and inflow data,
   - construct a reproducible quasi-1D core-flow geometry only from dimensions
     that can be mapped unambiguously,
   - keep fuel injection, prescribed combustion, wall friction, and wall heat
     transfer disabled unless separately sourced,
   - run geometry/inflow OFAT cases using published Table-4 levels where the
     quasi-1D mapping is physically meaningful,
   - label all outputs `surrogate`, not `Cao thesis reproduction`.

2. **P11.2B — reactive source-backed case**
   - remains blocked until a defensible axial fuel-source and burned-fuel or
     heat-release profile is supplied or derived from an explicitly approved
     closure.

This separation is deliberate: it allows the project to continue with a real,
dimensioned physical configuration without silently changing the accepted
source-term equations or inventing combustion physics.

## Remaining blocking evidence for P11.2B

The following input families still require evidence or an explicitly approved
closure before a formal reactive run:

- exact quasi-1D mapping of the Fig. 2 channel-height changes where the figure
  alone is ambiguous,
- per-module or axial distribution of total fuel mass flow,
- fuel axial velocity,
- fuel specific total enthalpy,
- axial burned-fuel distribution or heat-release distribution,
- any wall-friction or wall-heat-transfer inputs if those models are enabled,
- a literature/teacher-approved LBW/YBW discrimination criterion for P11.3.

## Decision rule

Do not substitute guesses for any remaining reactive input. A new value may
enter a formal case only when its source ID, table/figure/page/section locator,
raw value, units, conversion, and any derivation are recorded.

The previous all-or-nothing `P11.2 BLOCKED` state is therefore superseded:
P11.2A can continue immediately using SRC06, while exact Cao-thesis reactive
reproduction and P11.2B remain evidence-gated.
