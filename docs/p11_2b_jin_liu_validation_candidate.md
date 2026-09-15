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

### SRC10 / SRC11 — Liu geometry and validation experiment

SRC10 is Qili Liu, Damiano Baccarella, Brendan McGann, Tonghun Lee, *Dual-Mode Operation and Transition in Axisymmetric Scramjets*, AIAA Journal 57(11) (2019) 4764–4777, DOI `10.2514/1.J058391`.

SRC11 is the earlier same-program AIAA SciTech paper, *Influences of Cavity on Combustion Stabilization in an Axisymmetric Scramjet*, DOI `10.2514/6.2019-1681`. It independently records the `752 mm` overall model length and states that the cavity is replaced in the parallel configuration by a constant-area tube with the same length dimensions as the cavity.

The experiment provides a cavity-free model B with a simple axisymmetric geometry and direct exit measurements of pressure, Mach number, and stagnation enthalpy.

## Geometry evidence

The sources provide:

- circular inlet area contraction ratio `1.9`;
- inlet lip angle `10 deg`;
- constant-area circular isolator length `254 mm`;
- isolator inner diameter `35 mm`;
- fuel injector at `291.4 mm` downstream of the inlet lip;
- sixteen sonic injectors, each `0.75 mm` diameter and inclined `45 deg` backward;
- model-A cavity leading edge `42 mm` downstream of the injector;
- cavity floor length `35 mm`, depth `11 mm`, closeout ramp `22.5 deg`;
- downstream diverging combustor cone angle `2 deg`;
- diverging combustor length `357 mm`;
- overall model length `752 mm` in SRC11;
- model B replaces the cavity module with a constant-cross-sectional tube of the same `35 mm` diameter and same axial length dimensions.

### Axial transition location is now source-backed by geometric closure

The model-B replacement-tube extent no longer needs to be read from a low-resolution figure. The source-stated cavity geometry gives the axial projection of the closeout ramp as

`L_ramp = 11 mm / tan(22.5 deg) = 26.55635 mm`.

Therefore the cavity-module / model-B replacement-tube axial extent is

`35 + 26.55635 = 61.55635 mm`.

With the cavity leading-edge location `42 mm` downstream of the injector, the diverging section begins

`42 + 61.55635 = 103.55635 mm`

downstream of station 3 / the injector plane. Adding the source values from the inlet lip gives

`291.4 + 42 + 35 + 11/tan(22.5 deg) + 357 = 751.95635 mm`,

which closes the independently reported `752 mm` total model length to within about `0.044 mm`. That near-exact independent closure makes the axial transition position a source-backed derived quantity rather than a visual estimate.

For the quasi-one-dimensional validation geometry, the preferred solver coordinate is therefore `x=0` at station 3 / injector plane, with the start of divergence at `x=0.10355635 m` and the combustor exit at `x=0.46055635 m`.

One geometry ambiguity remains: the papers call the downstream section a `2 deg cone angle`, but the accessible text does not unambiguously define whether this is a wall half-angle or a full included cone angle. Because the two interpretations would produce substantially different area relief, the formal area profile remains gated on that convention instead of guessing it. The machine-readable derivation and evidence boundary are stored in `cases/studies/data/p11_2b_liu_model_b_geometry_source.json`.

The source also states that the x-axis follows the engine centerline and that its origin is at the center of the inlet. Station 3 is both the isolator exit / combustor inlet and the location of the most-upstream fuel injection; station 4 is the combustor exit. Re-basing all validation data to station 3 avoids needing an arbitrary absolute offset, provided every recovered heat-release coordinate is traced to the same source geometry.

## Thermodynamic / measurement evidence

The nominal freestream table reports:

- stagnation temperature `2400 K`;
- stagnation pressure `100 kPa`;
- Mach `4.5`;
- static temperature `475 K`;
- density `0.0025 kg/m^3`;
- velocity `1966 m/s`.

The accessible text extraction renders the static-pressure unit/value ambiguously, so that quantity is deliberately not frozen for a formal case.

For ethylene reacting-flow analysis, Liu et al. use average `gamma=1.31` and `cp=1255 J/(kg K)`. Exit stagnation enthalpy is evaluated using a heat-flux probe and a Sutton–Graves relation; exit Mach is obtained from wall static pressure and pitot measurements. The paper states that fuel mass flow is derived from fuel total pressure and the total choked injector-throat area with about 5% uncertainty, but the accessible text does not provide the exact fuel-total-pressure/mass-flow value needed to reconstruct the Jin validation run.

Liu also defines `Ht4/Ht3` as the combustor-exit to combustor-inlet total-flow-enthalpy ratio and uses it together with `pt4/pt3` in the one-dimensional mode-transition analysis. This ratio is a valuable **dimensionless validation constraint**, but by itself it is not an absolute `J/kg` increment and therefore is not silently converted into total thermal power. The repository contains explicit inverse diagnostics showing that a mass-flow scale and station-3 absolute total enthalpy are both required before `Ht4/Ht3` can determine heat power.

## Table-2 model-B record nearest to the Jin validation

Liu Table 2 contains a model-B ethylene row at `phi=1.03` with:

- `M4 = 2.27`;
- `pt4 = 17383.8 Pa`;
- `pt4/pt3 = 0.39`;
- `Ht4/Ht3 = 1.16`;
- raw table values `p0=98.6 kPa`, `p4=1453.7 Pa`, `ps=9891.1 Pa`.

The `M4=2.27` value exactly matches the experimental exit Mach cited by Jin et al. in the model-B validation discussion. This makes the row a very strong candidate for the underlying validation condition.

## The phi discrepancy is a cross-model conflict, not merely a decimal mismatch

The source comparison can now be stated more strongly than `1.03 versus 1.04`:

- Jin explicitly describes **model B, `phi=1.04`, experimental `M4=2.27`**;
- Liu Table 2 gives **model B, `phi=1.03`, `M4=2.27`, `Ht4/Ht3=1.16`**;
- Liu Table 2 also contains a row at **exactly `phi=1.04`**, but that row belongs to **model A**, with `M4=1.76` and `Ht4/Ht3=1.29`.

Therefore an automatic `1.03 -> 1.04` rounding assumption is not admissible: matching Jin by equivalence ratio would switch engine configurations, while matching by experimental exit Mach points to the Liu model-B `phi=1.03` row. The dedicated machine-readable record `cases/studies/data/p11_2b_jin_liu_condition_discrepancy.json` freezes this conflict and deliberately leaves its interpretation unresolved.

Plausible explanations include a typographical/rounding error in Jin or a distinct model-B run absent from the accessible Liu table, but the repository does not choose between them without traceable evidence.

## Why the case is still blocked

The current public record is not yet sufficient to execute the exact Jin–Liu validation without introducing hidden assumptions. The remaining blockers are now narrower:

1. resolve the model/condition identity conflict described above;
2. recover the axial heat-release shape used in the Jin validation, or the fitted quasi-Gaussian parameters for that exact case, with a retained source/figure extraction record;
3. recover the **absolute stagnation-enthalpy increment** used by Jin and the mass flow / station-3 absolute enthalpy needed to scale Eq. 11. The table ratio `Ht4/Ht3=1.16` is retained as a dimensionless constraint but is not converted into an absolute increment by itself;
4. resolve whether the source's `2 deg cone angle` is a wall half-angle or an included cone angle. The axial divergence-start location itself is now frozen by geometric closure.

The ACT-II facility paper shows that the arc heater was operated over several mass-flow rates (`7.3`, `13.3`, and `22.2 g/s` in facility characterization), but the repository does not assign any one of those values to the Liu 2019 validation run without direct evidence.

## Supplement / author-data recovery priority

Jin explicitly points readers to supplementary material and states that supporting data can be requested from the corresponding author. Public web indexing confirms the supplement exists, but the exact supplementary file containing the Fig. 14 validation inputs has not yet been recovered in a traceable form. The next evidence priority is therefore:

1. recover the publisher supplementary material or an author-hosted copy;
2. inspect it specifically for the Liu model-B validation condition, fitted `Q_m/x_m/x_i/x_c/k`, PLIF coordinate extraction, exit stagnation-enthalpy increment, and mass flow;
3. if the supplement still omits these values, treat an author-provided data table as the preferred source rather than digitizing an unlabeled figure.

## Promotion rule

This candidate remains in `candidate_validation_chains`, not `candidate_formal_cases`.

Promotion is allowed only when the missing chain is recovered from traceable evidence. In particular, the project will not:

- infer air mass flow from the inlet geometry and nominal density/velocity;
- infer absolute combustion heat from `Ht4/Ht3` alone;
- digitize PLIF/enthalpy plots without recording the coordinate/calibration procedure;
- silently replace Jin's model-B `phi=1.04` label with Liu's model-B `phi=1.03` row;
- accidentally use Liu's model-A `phi=1.04` row to satisfy Jin's model-B label;
- interpret the `2 deg cone angle` without source evidence for the angle convention;
- transplant the Liu/Jin heat-release distribution into the P11.2A Li geometry and call that validation.

## Scientific value if completed

A completed Jin–Liu model-B case would provide a substantially stronger P11.2B milestone than a synthetic heat-addition sweep. It would test the direct `Qdot'(x)` interface against an independent cavity-free experiment for which pressure distribution, exit Mach, total-pressure ratio, and total-enthalpy ratio are available, while remaining close to the quasi-one-dimensional assumptions of the current solver.

It would still be a prescribed-heat-release validation, not finite-rate chemistry validation and not an LBW/YBW classification result.
