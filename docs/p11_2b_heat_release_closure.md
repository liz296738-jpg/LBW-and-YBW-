# P11.2B Direct Prescribed Heat-Release Closure

## Status

`INTERFACE IMPLEMENTED — FORMAL REACTIVE PARAMETER SET STILL EVIDENCE-GATED`

P11.2A showed that the accepted inviscid, source-free cold-flow model cannot reproduce the experimentally observed sensitivity to isolator length: shortening a constant-area isolator only shifts the downstream solution in the axial coordinate. P11.2B therefore introduces the smallest additional energy-source capability needed to study heat-release effects without inventing fuel mass, fuel velocity, or detailed chemistry.

The new interface is a directly prescribed axial line heat-release rate:

`heat_release_rate_per_length = Qdot'(x) [W/m]`

It is mapped through the already verified P8 source semantics as

`qdot_vol(x) = Qdot'(x) / A(x) [W/m^3]`

and enters only the conservative energy equation. It adds no mass or axial momentum.

## Why a direct energy interface is needed

The previous P8 solver path accepts a prescribed burned-fuel distribution [kg/(m s)] and an LHV [J/kg]. That path is valid when both inputs are source-backed. It is scientifically inappropriate, however, to take an experimentally measured or literature-modelled heat-release distribution and reverse-engineer a fictitious burned-fuel profile merely to satisfy the API.

The direct `Qdot'(x)` path therefore exposes the energy-source representation that already exists in `source_terms.py`. It does not change the governing energy equation; it removes an unnecessary semantic conversion when the source evidence is heat release itself.

To prevent double counting, the solver rejects configurations in which both the burned-fuel/LHV path and the direct `Qdot'(x)` path are nonzero.

## Evidence ledger

Machine-readable evidence is stored in:

`cases/studies/data/p11_2b_heat_release_model_source.json`

### SRC07 — Cao et al. (2020)

Ruifeng Cao, Yue Lu, Daren Yu, Juntao Chang et al., *Study on influencing factors of combustion mode transition boundary for a scramjet engine based on one-dimensional model*, Aerospace Science and Technology 96 (2020) 105590, DOI `10.1016/j.ast.2019.105590`.

This source is important because it is directly within the Cao modelling lineage designated by the project. Its one-dimensional study explicitly treats combustor heat-release distribution as a factor influencing the combustion-mode-transition boundary, alongside area profile, wall conditions, and inflow composition.

The currently accessible record establishes scientific relevance, but it does not by itself expose a complete solver-ready axial heat-release parameter set for this repository.

### SRC08 — Jin et al. (2026)

Kaiyan Jin, Jianbin Li, Lin Zhang, Jianhan Liang, Xiaodong Cai, *Experimental study on heat release distribution during supersonic combustion*, Combustion and Flame 287 (2026) 114876, DOI `10.1016/j.combustflame.2026.114876`.

The paper reports a direct-connected cavity-based supersonic-combustion experiment with approximately the same high-enthalpy inflow scale already used in P11.2A: Mach 2.52, stagnation temperature 1650 K, and stagnation pressure 1.3 MPa. It develops a one-dimensional normalized heat-release-rate model from experimental CH* chemiluminescence data.

The source gives the Gaussian relation (Eq. 6)

`Q*(x) = Q*_m exp(-(x-x_m)^2/(2 delta^2))`

and the range-parameterized form (Eq. 7)

`Q*(x) = Q*_m exp(-(x-x_m)^2/(x_c-x_m)^2)`.

It also relates axial heat release to stagnation-temperature rise through its Eq. 11, equivalent to

`Tt(x) = Tt0 + integral(Qdot'(x) dx)/(mdot cp)`.

The repository implements the unambiguous Eq. 7 functional form only as a study utility. It does **not** yet assign formal values to `Q*_m`, `x_m`, `x_c`, or absolute thermal power for the P11.2A geometry.

The paper also proposes an asymmetric Eq. 8 using `x_i` and an adjustment parameter `k`. The text record for its Case 10 reports `x_c=98`, `k=5.6`, and global `R^2=0.997`, but the exact unit/parameter convention needed for a clean repository implementation has not yet been frozen. Eq. 8 is therefore deliberately deferred rather than reconstructed from a figure or guessed.

## Implemented utilities

`cases/studies/p11_2b_heat_release_closure.py` provides three narrow, testable transformations:

1. `quasi_gaussian_eq7_normalized(...)` reproduces the published Eq. 7 functional form without assigning operating-condition parameters.
2. `scale_shape_to_total_power(...)` converts any nonnegative cell-centred shape into `Qdot'(x) [W/m]` while exactly satisfying the finite-volume identity `sum(Qdot'_i dx)=Qdot_total`.
3. `cumulative_total_temperature_from_line_heat(...)` evaluates the discrete Eq. 11 energy integral as a diagnostic.

These utilities do not infer total thermal power from equivalence ratio, total fuel flow, LHV, or combustion efficiency.

## Solver contract

The production solver now accepts optional `heat_release_rate_per_length` in:

- `quasi_1d_rhs`;
- `quasi_1d_rhs_transmissive`;
- `solve_quasi_1d`;
- `solve_quasi_1d_steady`.

The input must be finite, nonnegative, and broadcast-compatible with the cell shape. A zero profile preserves the legacy solver path exactly. A nonzero direct heat-release profile is mutually exclusive with a nonzero `fuel_burn_rate_per_length`/LHV path.

Regression tests require the direct path to be exactly equivalent to the legacy burned-fuel/LHV path when both represent the same line heat release. This verifies that the interface change does not introduce a new energy equation.

## What is still blocked

No formal P11.2B reactive case is authorized yet. At least two source-backed pieces are still required together:

- an absolute total heat-release power (or an evidence-backed way to derive it), and
- axial shape parameters for the same operating condition and geometry.

The project will not manufacture these by assuming 100% combustion efficiency, dividing total fuel uniformly over the combustor, reading approximate coordinates from a plot without traceability, or borrowing parameters from a different experiment and presenting them as the Li et al. case.

A separate literature-validation case using the Jin et al. apparatus may be possible if a complete numerical parameter set can be recovered with explicit units and locators. That would remain a separate validation/surrogate case, not a calibration of the P11.2A geometry.

## Scientific claim boundary

At this stage the project may claim:

> The solver supports a directly prescribed, conservative axial heat-addition profile and the repository contains a source-backed quasi-Gaussian closure form suitable for a future P11.2B study once its operating-condition parameters are frozen.

It may **not** yet claim a validated reactive P11.2B engine case, detailed combustion chemistry, or an LBW/YBW prediction.
