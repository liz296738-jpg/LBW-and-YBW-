# P11.2B Direct Prescribed Heat-Release Closure

## Status

`INTERFACE AND SOURCE-BACKED CLOSURE FORMS IMPLEMENTED — FORMAL HEATED PARAMETER SET STILL EVIDENCE-GATED`

P11.2A showed that the accepted inviscid, source-free cold-flow model cannot reproduce the experimentally observed sensitivity to isolator length: shortening a constant-area isolator only shifts the downstream solution in the axial coordinate. P11.2B therefore introduces the smallest additional energy-source capability needed to study heat-release effects without inventing fuel mass, fuel velocity, or detailed chemistry.

The production interface is a directly prescribed axial line heat-release rate:

`heat_release_rate_per_length = Qdot'(x) [W/m]`

It is mapped through the verified P8 source semantics as

`qdot_vol(x) = Qdot'(x) / A(x) [W/m^3]`

and enters only the conservative energy equation. It adds no mass or axial momentum.

## Why a direct energy interface is needed

The previous P8 path accepts a prescribed burned-fuel distribution [kg/(m s)] and an LHV [J/kg]. That is appropriate when both inputs are source-backed. It is scientifically inappropriate to take an experimentally measured or literature-modelled heat-release distribution and reverse-engineer a fictitious burned-fuel profile merely to satisfy the API.

The direct `Qdot'(x)` path exposes the energy-source representation that already exists in `source_terms.py`; it does not introduce a new governing equation. The solver rejects configurations in which the burned-fuel/LHV path and direct heat-release path are both active, preventing double counting.

## Evidence ledger

Machine-readable evidence is stored in:

`cases/studies/data/p11_2b_heat_release_model_source.json`

### SRC07 — Cao et al. (2020)

Ruifeng Cao, Yue Lu, Daren Yu, Juntao Chang et al., *Study on influencing factors of combustion mode transition boundary for a scramjet engine based on one-dimensional model*, Aerospace Science and Technology 96 (2020) 105590, DOI `10.1016/j.ast.2019.105590`.

This Cao-lineage source explicitly treats combustor heat-release distribution as a factor influencing the combustion-mode-transition boundary, alongside area profile, wall conditions, and inflow composition. It establishes direct scientific relevance to the teacher-designated modelling direction, but the currently accessible record does not expose a complete solver-ready heat-release parameter set.

### SRC08 — Jin et al. (2026)

Kaiyan Jin, Jianbin Li, Lin Zhang, Jianhan Liang, Xiaodong Cai, *Experimental study on heat release distribution during supersonic combustion*, Combustion and Flame 287 (2026) 114876, DOI `10.1016/j.combustflame.2026.114876`.

The paper reports a direct-connected ethylene experiment at Mach 2.52, stagnation temperature 1650 K, stagnation pressure 1.3 MPa, and air mass flow 0.600 kg/s. It develops a normalized one-dimensional heat-release model from CH* chemiluminescence and demonstrates coupling with quasi-one-dimensional equations.

The range-parameterized Eq. 7 is

`Q*(x) = Q*_m exp(-(x-x_m)^2/(x_c-x_m)^2)`.

The asymmetric Eq. 8 is text-recoverable as

`Q*(x) = Q*_m exp(-[((x-x_m)(x-x_i+k))/((x_c-x_m)(x-x_i))]^2)`

for the heat-release region downstream of initiation coordinate `x_i`. The repository defines the profile as zero at and upstream of `x_i` and requires physical ordering `x_i < x_m < x_c`.

The paper also relates axial heat release to stagnation-temperature rise through Eq. 11:

`Tt(x) = Tt0 + integral(Qdot'(x) dx)/(mdot cp)`.

For its Case 10, the text reports raw `x_c=98`, `k=5.6`, global fit `R^2=0.997`, and cumulative normalized heat release about `0.92` at `x_c`. These numerical values are retained as raw evidence only: the project does not freeze their units/coordinate convention or use them in a formal case until matching `x_i`, `x_m`, and absolute heat-addition evidence are recovered.

The same paper demonstrates a quasi-one-dimensional validation against an independent circular-combustor experiment: for the referenced model-B case near equivalence ratio 1.04, its predicted exit Mach is 2.24 versus experimental 2.27. This is useful evidence that a prescribed heat-release model can support reduced-order validation, but it does not by itself supply all parameters needed to reproduce that case in this repository.

### SRC09 — Tian et al. (2012)

Lu Tian, Lihong Chen, Qiang Chen, Fei Li, Xinyu Chang, *Modeling and Measurements of Heat Release Distributions in Dual-mode Scramjet Combustor*, AIAA 2012-5833, DOI `10.2514/6.2012-5833`.

This study used a modified one-dimensional model to infer heat-release distributions by matching wall pressure and then checked the inferred solutions against TDLAS temperature/velocity measurements. Its accessible Table 1 provides four operating cases. Case 4, for example, reports Mach 2.5, total temperature 1650 K, air mass flow 1.2 kg/s, equivalence ratio 0.75, and combustion efficiency 80% for the single-port/Jet3 configuration.

The accessible text does not explicitly state the fuel chemical identity/LHV for those Table-1 cases and does not tabulate the fitted axial heat-release curve. Consequently the repository records these values but does not convert them into absolute thermal power or digitize plotted curves as formal data.

## Implemented closure utilities

`cases/studies/p11_2b_heat_release_closure.py` provides four narrow transformations:

1. `quasi_gaussian_eq7_normalized(...)` — published Eq. 7 functional form;
2. `asymmetric_quasi_gaussian_eq8_normalized(...)` — published Eq. 8 functional form, zero upstream of `x_i` and with explicit position ordering;
3. `scale_shape_to_total_power(...)` — finite-volume scaling to `Qdot'(x) [W/m]` satisfying `sum(Qdot'_i dx)=Qdot_total` exactly;
4. `cumulative_total_temperature_from_line_heat(...)` — discrete Eq. 11 energy integral as a diagnostic.

All length arguments in the normalized shapes are unit-invariant when scaled consistently. The utilities deliberately do not infer total thermal power from equivalence ratio, total fuel flow, LHV, or combustion efficiency.

## Solver contract and regression evidence

The production solver accepts optional `heat_release_rate_per_length` in:

- `quasi_1d_rhs`;
- `quasi_1d_rhs_transmissive`;
- `solve_quasi_1d`;
- `solve_quasi_1d_steady`.

The input must be finite, nonnegative, and broadcast-compatible with the cell shape. A zero profile preserves the legacy path. A nonzero direct profile is mutually exclusive with a nonzero `fuel_burn_rate_per_length`/LHV path.

Tests require the direct path to be exactly equivalent to the legacy burned-fuel/LHV path when both represent the same line heat release. This verifies that the interface does not introduce a new energy equation.

The first closure-infrastructure regression checkpoint at commit `e36cfb124f9bd0a8ddb3be6d548f79a751fdf471` passed GitHub Actions run `34882069673` with `828 passed in 60.67 s`. The subsequent Eq. 8 and evidence-ledger additions remain subject to the same full-suite gate before their final acceptance record is frozen.

## What is still blocked

No formal P11.2B heated engine case is authorized yet. The remaining minimum evidence pair is:

- absolute total heat-release power, or a source-backed way to derive it;
- matching axial shape parameters for the same geometry and operating condition.

The project will not manufacture these by assuming 100% combustion efficiency, uniformly smearing total fuel, reading untraceable values off a plot, or combining geometry, heat-release shape, and thermal power from unrelated experiments while calling the result a reproduction.

A separate literature-validation case is acceptable if all its inputs can be frozen from one internally consistent source chain. It must remain distinct from the P11.2A Li et al. geometry unless a documented transformation justifies the connection.

## Scientific claim boundary

At this stage the project may claim:

> The solver supports a directly prescribed conservative axial heat-addition profile, and the repository implements source-backed normalized symmetric/asymmetric quasi-Gaussian heat-release closure forms plus an energy-integral diagnostic, all regression-tested without introducing fictitious fuel mass or chemistry.

It may **not** yet claim a validated reactive P11.2B engine case, detailed combustion chemistry, a Cao-thesis reproduction, or an LBW/YBW prediction.
