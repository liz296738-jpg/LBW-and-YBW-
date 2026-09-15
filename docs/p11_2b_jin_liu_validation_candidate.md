# P11.2B Jin–Liu Model-B Validation Candidate

## Status

`PROMISING INDEPENDENT VALIDATION CHAIN — NOT YET A FORMAL CASE`

The strongest public validation path recovered so far is not the P11.2A Li geometry. It is the cavity-free axisymmetric scramjet **model B** experiment of Liu et al. (2019), which Jin et al. (2026) explicitly reuse to test the quasi-Gaussian heat-release model coupled to quasi-one-dimensional flow equations.

This is scientifically cleaner than attaching a Jin heat-release shape to the unrelated P11.2A geometry, because Jin explicitly identifies the Liu model-B configuration as closer to quasi-one-dimensional assumptions.

## Sources

### SRC08 — Jin et al. (2026)

Kaiyan Jin, Jianbin Li, Lin Zhang, Jianhan Liang, Xiaodong Cai, *Experimental study on heat release distribution during supersonic combustion*, Combustion and Flame 287 (2026) 114876, DOI `10.1016/j.combustflame.2026.114876`.

In the validation discussion around Fig. 14, Jin et al. state that:

- the Liu circular combustor without a cavity more closely satisfies the quasi-one-dimensional assumption;
- its heat-release distribution can be estimated using the current quasi-Gaussian model together with the experimental PLIF image and the measured stagnation-enthalpy increment at the combustor exit;
- the theoretical pressure distribution agrees strongly with the experiment;
- the theoretical exit Mach is `2.24`, close to the experimental `2.27`;
- the text identifies the validation condition as scramjet model B with `phi=1.04`.

The article explicitly states that supplementary material exists online and that supporting data are available from the corresponding author upon reasonable request. The publicly indexed article text recovered so far does **not** expose the exact model-B validation shape parameters or the absolute stagnation-enthalpy increment used for Fig. 14. Those quantities therefore remain evidence-gated rather than reconstructed by guesswork.

### SRC10 / SRC11 / SRC12 — Liu geometry and validation lineage

SRC10 is Qili Liu, Damiano Baccarella, Brendan McGann, Tonghun Lee, *Dual-Mode Operation and Transition in Axisymmetric Scramjets*, AIAA Journal 57(11) (2019) 4764–4777, DOI `10.2514/1.J058391`.

SRC11 is the earlier same-program AIAA SciTech paper, *Influences of Cavity on Combustion Stabilization in an Axisymmetric Scramjet*, DOI `10.2514/6.2019-1681`. It independently records the approximately `752 mm` overall model length and states that the cavity is replaced in the parallel configuration by a constant-area tube with the same length dimensions as the cavity.

SRC12 is Hang Liu and Wei Yao, *LES investigation of nonequilibrium flow in a cavity-flameholding axisymmetric scramjet*, AIAA 2021-3536, DOI `10.2514/6.2021-3536`. It is **not** used to replace the primary experimental source. It is used only as an independent same-geometry dimensional cross-check because it publishes a full-scale reconstruction with inlet length `37.43 mm`, a `296 mm` constant-diameter run to the cavity leading edge, and total model length `752.43 mm`.

## Geometry evidence

The source chain provides:

- circular inlet area contraction ratio `1.9`;
- inlet internal lip angle `10 deg`;
- inlet length `37.43 mm` in SRC12;
- constant-area circular isolator length `254 mm` in SRC10;
- isolator inner diameter `35 mm`;
- fuel injector at `291.4 mm` downstream of the inlet lip in SRC10;
- sixteen sonic injectors, each `0.75 mm` diameter and inclined `45 deg` backward;
- model-A cavity leading edge `42 mm` downstream of the injector;
- cavity floor length `35 mm`, depth `11 mm`, closeout ramp `22.5 deg`;
- downstream diverging combustor `2 deg cone angle` and length `357 mm`;
- approximately `752 mm` overall length in SRC11 and `752.43 mm` in SRC12;
- model B replaces the cavity module with a constant-cross-sectional tube of the same `35 mm` diameter and corresponding axial extent.

### Station 3 is independently closed

SRC10 defines station 3 as the isolator exit / combustor inlet / most-upstream fuel-injection plane and locates the injector at `291.4 mm` downstream of the inlet lip.

Independently, SRC12 gives a `37.43 mm` inlet followed by the SRC10 `254 mm` isolator. Therefore

`37.43 + 254 = 291.43 mm`,

which agrees with SRC10's `291.4 mm` station-3/injector coordinate to `0.03 mm`.

A second independent dimensional identity also closes exactly:

`254 mm isolator + 42 mm injector-to-cavity distance = 296 mm`,

matching SRC12's stated constant-diameter length from the inlet end to the cavity leading edge. These two identities clarify that the apparently different `254 mm` and `296 mm` dimensions use different axial endpoints rather than representing conflicting geometries.

Accordingly, when source coordinates are referenced to the SRC10 inlet plane, the formal coordinate transform is now frozen as

`x_solver = x_source - 0.2914 m`,

with `x_solver=0` at station 3 / the injector plane. The `0.03 mm` SRC12 closure residual is retained as an independent rounding-level cross-check rather than used as a fitted correction.

### Axial transition location is source-backed by geometric closure

The model-B replacement-tube extent does not need to be read from a low-resolution figure. The source-stated cavity geometry gives the axial projection of the closeout ramp as

`L_ramp = 11 mm / tan(22.5 deg) = 26.55635 mm`.

Therefore the cavity-module / model-B replacement-tube axial extent is

`35 + 26.55635 = 61.55635 mm`.

With the cavity leading-edge location `42 mm` downstream of station 3, the diverging section begins

`42 + 61.55635 = 103.55635 mm`

downstream of station 3. The quasi-one-dimensional validation coordinate is therefore frozen as:

- station 3 / injector: `x=0`;
- start of divergence: `x=0.10355635 m`;
- station 4 / combustor exit: `x=0.46055635 m`.

Two independent overall-length checks support this reconstruction. Using SRC10/SRC11 dimensions gives

`291.4 + 42 + 35 + 11/tan(22.5 deg) + 357 = 751.95635 mm`,

only about `0.044 mm` from SRC11's `752 mm`. Using SRC12's inlet/constant-section dimensions gives

`37.43 + 296 + 35 + 11/tan(22.5 deg) + 357 = 751.98635 mm`,

about `0.444 mm` from SRC12's `752.43 mm`. Both residuals are sub-millimetre and are treated as source/rounding consistency checks, not tunable parameters.

The machine-readable derivation is stored in `cases/studies/data/p11_2b_liu_model_b_geometry_source.json`.

### One area-profile ambiguity remains

The primary sources repeatedly call the downstream section a `2 deg cone angle`. The text also discusses a constant-cone-angle area expansion whose rate depends on the combustor radius, but the recovered primary text does not explicitly define whether `2 deg` is the wall half-angle or the full included cone angle. The two interpretations lead to materially different `A(x)`, so neither is promoted by nomenclature alone.

A formal model-B area profile therefore remains blocked **only** on this angular convention. The station-3 coordinate, divergence-start coordinate, and combustor-exit coordinate are no longer geometry blockers.

## Thermodynamic / measurement evidence

The nominal freestream record reports stagnation temperature `2400 K`, stagnation pressure `100 kPa`, Mach `4.5`, static temperature `475 K`, density `0.0025 kg/m^3`, and velocity `1966 m/s`. The primary text extraction renders the static-pressure header/value ambiguously, while SRC12 independently lists `345 Pa`; this quantity is not needed to close the present station-3 validation chain and is not promoted solely by OCR repair.

For ethylene reacting-flow analysis, Liu et al. use average `gamma=1.31` and `cp=1255 J/(kg K)`. Exit stagnation enthalpy is evaluated using a heat-flux probe and a Sutton–Graves relation; exit Mach is obtained from wall static pressure and pitot measurements. The paper states that fuel mass flow is derived from fuel total pressure and the total choked injector-throat area with about `5%` uncertainty, but the accessible record does not provide the exact fuel-total-pressure/mass-flow value needed to reconstruct the Jin validation run.

Liu defines `Ht4/Ht3` as the combustor-exit to combustor-inlet total-flow-enthalpy ratio and uses it together with `pt4/pt3` in the one-dimensional mode-transition analysis. This ratio is a useful **dimensionless validation constraint**, but by itself it is not an absolute `J/kg` increment and therefore is not silently converted into total thermal power. The repository contains explicit diagnostics showing that station-3 absolute total enthalpy and a mass-flow scale are still needed before the ratio can determine heat power.

## Table-2 model-B record nearest to the Jin validation

Liu Table 2 contains a model-B ethylene row at `phi=1.03` with:

- `M4 = 2.27`;
- `pt4 = 17383.8 Pa`;
- `pt4/pt3 = 0.39`;
- `Ht4/Ht3 = 1.16`;
- raw table values `p0=98.6 kPa`, `p4=1453.7 Pa`, `ps=9891.1 Pa`.

The `M4=2.27` value exactly matches the experimental exit Mach cited by Jin et al. in the model-B validation discussion. This makes the row a strong candidate for the underlying validation condition, but not yet an identity proof.

## The phi discrepancy is a cross-model conflict, not merely a decimal mismatch

The source comparison is:

- Jin: **model B, `phi=1.04`, experimental `M4=2.27`**;
- Liu Table 2: **model B, `phi=1.03`, `M4=2.27`, `Ht4/Ht3=1.16`**;
- Liu Table 2: a row at **exactly `phi=1.04`**, but it belongs to **model A**, with `M4=1.76` and `Ht4/Ht3=1.29`.

SRC12 additionally studies the **cavity-present** axisymmetric configuration at `phi=1.04`. This is useful contextual corroboration that `phi=1.04` appears in the cavity-present branch of the same geometry family, but it does **not** prove that Jin's model-B label is a typo.

Therefore an automatic `1.03 -> 1.04` rounding assumption is inadmissible: matching Jin by equivalence ratio would cross engine configurations, while matching by experimental exit Mach points to Liu's model-B `phi=1.03` row. The dedicated record `cases/studies/data/p11_2b_jin_liu_condition_discrepancy.json` preserves the conflict and explicitly forbids using the secondary numerical paper to override the primary-source disagreement.

## Why the case is still blocked

The current public record is not yet sufficient to execute the exact Jin–Liu validation without hidden assumptions. The remaining blockers are:

1. resolve the model/condition identity conflict above;
2. recover the axial heat-release shape used in Jin Fig. 14, or the fitted quasi-Gaussian parameters for that exact condition, with traceable coordinate evidence;
3. recover the **absolute stagnation-enthalpy increment** used by Jin together with the matching mass flow / station-3 absolute enthalpy, or recover an already-absolute `Qdot'(x) [W/m]` profile;
4. resolve whether the source's `2 deg cone angle` is a wall half-angle or an included cone angle before constructing the radial area-growth law.

The station-3 coordinate and axial divergence-start location are now closed and must not be listed as open blockers.

## Supplement / author-data recovery priority

Jin explicitly points readers to supplementary material and states that supporting data can be requested from the corresponding author. Public indexing confirms that supplementary material exists, but the exact file exposing the Fig. 14 validation inputs has not been recovered in a traceable form. The next evidence priority is therefore:

1. recover publisher supplementary material or an author-hosted copy;
2. inspect it specifically for model-B condition identity, fitted `Q_m/x_m/x_i/x_c/k`, PLIF coordinate extraction, exit stagnation-enthalpy increment, and mass flow;
3. if the supplement omits these quantities, prefer an author-provided data table over untracked figure digitization.

## Promotion rule

This candidate remains in `candidate_validation_chains`, not `candidate_formal_cases`.

The project will not infer air mass flow from nominal geometry, infer absolute heat from `Ht4/Ht3` alone, silently change `phi=1.04` to `1.03`, substitute model A for model B, assume the `2 deg` convention, or transplant this heat-release distribution into the unrelated P11.2A geometry and call it validation.

## Scientific value if completed

A completed Jin–Liu model-B case would test the direct `Qdot'(x)` interface against an independent cavity-free experiment for which pressure distribution, exit Mach, total-pressure ratio, and total-enthalpy ratio are available, while remaining close to the quasi-one-dimensional assumptions of the current solver.

It would still be a prescribed-heat-release validation, not finite-rate chemistry validation and not an LBW/YBW classification result.
