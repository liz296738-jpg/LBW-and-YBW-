# P11.2 Authoritative Source and Baseline Gap Report

## Status

`P11.2 BLOCKED — AUTHORITATIVE SOURCE DATA REQUIRED`

P11.2 requires an evidence-backed physical baseline before any formal numerical
case or one-factor-at-a-time sensitivity is created. The repository and the
available workspace were inventoried without network access on 2026-09-15.
The authoritative project materials listed below are now available; however,
they do not yet provide all source-grounded values required to reproduce one
complete P11.2 baseline in the accepted solver.

## Source Inventory

| source_id | title | type | file/path | project authority | usable for physical baseline | notes |
| --- | --- | --- | --- | --- | --- | --- |
| SRC01 | Teacher instruction record | screenshot | `C:\Users\ASUA\OneDrive\Desktop\乔老师项目\8c5391aaaba19e0dec5eef7b949d0995.jpg` and `lQDPKHmGZKvwFxfNCvDNBOywgb9mjMBclyMKb0Ndkxe6AA_1260_2800.jpg` | Teacher/project instruction | Yes, for source selection | The teacher confirms modelling from the group-provided Cao Ruifeng papers. It supplies no numerical physical input. |
| SRC02 | *Research on Combustion Mode Transition and Its Control Method for Scramjet Engines* | doctoral thesis, Cao Ruifeng, 2016 | `C:\Users\ASUA\OneDrive\Desktop\乔老师项目\超燃冲压发动机燃烧模态转换及其控制方法研究_曹瑞峰.pdf` | Project-designated thesis | Partial | Table 2-1 supplies an idealized case-1 isolator inlet; Table 3-2 supplies kerosene LHV; Table 5-1 supplies ground-test inlet conditions. It does not provide a complete tracked combustor geometry and axial prescribed-source profile for the selected solver model. |
| SRC03 | *Research on One-Dimensional Modeling of Scramjet Engine for Control* | master's thesis, Cao Ruifeng | `C:\Users\ASUA\OneDrive\Desktop\乔老师项目\面向控制的超燃冲压发动机一维建模研究_曹瑞峰.pdf` | Project-designated thesis | Partial | Establishes one-dimensional model context and candidate physical effects, but the readable material inspected does not provide a complete, locatable numerical baseline compatible with the accepted solver. |
| SRC04 | *Theory and Application of Hypersonic Aerodynamic Layout*, Chapter 11 | photographed textbook pages | `C:\Users\ASUA\OneDrive\Desktop\乔老师项目\IMG_2459.HEIC.JPG` through `IMG_2469.HEIC.JPG` | Project-provided technical reference | Partial | Pages 251–261 document generalized one-dimensional source terms and source semantics; they do not provide a selected engine geometry or a complete numerical operating case. |
| SRC05 | Project scope and accepted numerical records | internal documentation and code | `README.md`, `docs/`, `cases/`, `src/`, `tests/` | Project implementation record | No | Provides verified solver capability, not external physical-source data. |

Source locators with usable numerical content found in `SRC02` are:

- Chapter 2, Table 2-1 (PDF printed pp. 46–47): `Ma2 = 2`,
  `rho2 = 0.7736 kg/m^3`, `p2 = 156.522 kPa`, `T2 = 705 K`,
  `u2 = 1038 m/s`, `k = 1.33`, and `phi = 0.3` for an idealized case.
- Chapter 3, Table 3-2 (PDF printed p. 57): `gamma = 1.4` and kerosene
  `Hf = 42,000 kJ/kg` for that cycle-analysis model.
- Chapter 5, Table 5-1 (PDF printed p. 124): isolator-entry `Ma2`, `P2`,
  total temperature, and air mass flow for ground-test flight-Mach settings
  4–7.

Those values are evidence records, not an authorization to invent the missing
geometry or to infer an axial injection/burn profile that the sources do not
specify.

## Blocking Evidence Gaps

The following required P11.2 input families cannot be frozen from the available
authoritative evidence:

- Geometry: axial domain and source-supported area profile, plus hydraulic
  diameter if wall friction is active. The available figures are schematic or
  non-dimensioned for the required profile; no digitizable `x` and `A` values
  were found.
- Inlet: Table 2-1 and Table 5-1 provide candidate inlet records, but a selected
  physical baseline cannot be run until its geometry and source-profile context
  are fixed.
- Outlet: a source-supported boundary selection and value when applicable.
- Fuel injection: mass-flow distribution, axial velocity, total enthalpy, and
  an authoritative axial injection location/profile.
- Prescribed burn/heat release: burn-rate distribution or heat-release
  distribution with an explicitly sourced LHV for any conversion.
- OFAT eligibility: at least two factors with source-supported non-baseline
  levels after a complete baseline is available. The papers discuss variation
  trends, but the inspected material does not yield two complete, solver-ready
  factor level sets with fixed companion inputs.

The accepted gas constants (`gamma = 1.4`, `R = 287 J/(kg K)`) may be retained
as explicit model assumptions, but they do not close the geometry, inlet, or
fuel/heat-release evidence gaps.

## Required Input to Resume

Provide the dimensioned combustor drawing or tabulated station data associated
with the chosen paper/test case, plus the selected injector location/profile and
the prescribed burn or heat-release distribution. It must identify any required
fuel axial velocity/enthalpy and support at least two OFAT factors with
non-baseline levels. Once available, its source ID, page/table/figure/section
locator, raw value, units, conversion, and derivation can be entered into the
P11.2 baseline evidence ledger.

No P11.2 physical baseline, sensitivity range, solver run, artifact, workflow,
or production-CFD change has been created from incomplete source data.
