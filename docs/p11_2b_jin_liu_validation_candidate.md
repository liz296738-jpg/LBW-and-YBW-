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

### SRC10 — Liu et al. (2019)

Qili Liu, Damiano Baccarella, Brendan McGann, Tonghun Lee, *Dual-Mode Operation and Transition in Axisymmetric Scramjets*, AIAA Journal 57(11) (2019) 4764–4777, DOI `10.2514/1.J058391`.

The experiment provides a cavity-free model B with a simple axisymmetric geometry and direct exit measurements of pressure, Mach number, and stagnation enthalpy.

## Geometry evidence

The source text and Fig. 2 provide:

- circular inlet area contraction ratio `1.9`;
- inlet lip angle `10 deg`;
- constant-area circular isolator length `254 mm`;
- isolator inner diameter `35 mm`;
- fuel injector at `291.4 mm` downstream of the inlet lip;
- sixteen sonic injectors, each `0.75 mm` diameter and inclined `45 deg` backward;
- downstream diverging combustor cone angle `2 deg`;
- diverging combustor length `357 mm`;
- model B replaces the model-A cavity module with a constant-cross-sectional tube of the same `35 mm` diameter before the downstream diverging combustor.

The source also states that the x-axis follows the engine centerline and that its origin is at the center of the inlet. This makes a future source-to-solver axial mapping substantially more defensible than a geometry reconstructed from an unlabeled heat-release plot.

## Thermodynamic / measurement evidence

The nominal freestream table reports:

- stagnation temperature `2400 K`;
- stagnation pressure `100 kPa`;
- Mach `4.5`;
- static temperature `475 K`;
- density `0.0025 kg/m^3`;
- velocity `1966 m/s`.

The accessible text extraction renders the static-pressure unit/value ambiguously, so that quantity is deliberately not frozen for a formal case.

For ethylene reacting-flow analysis, Liu et al. use average `gamma=1.31` and `cp=1255 J/(kg K)`. Exit stagnation enthalpy is evaluated using a heat-flux probe and a Sutton–Graves relation; exit Mach is obtained from wall static pressure and pitot measurements.

## Table-2 model-B record nearest to the Jin validation

Liu Table 2 contains a model-B ethylene row at `phi=1.03` with:

- `M4 = 2.27`;
- `pt4 = 17383.8 Pa`;
- `pt4/pt3 = 0.39`;
- `Ht4/Ht3 = 1.16`;
- raw table values `p0=98.6 kPa`, `p4=1453.7 Pa`, `ps=9891.1 Pa`.

The `M4=2.27` value exactly matches the experimental exit Mach cited by Jin et al. in the model-B validation discussion. This makes the row a very strong candidate for the underlying validation condition.

However, Jin labels the validation condition `phi=1.04`, while Liu Table 2 labels this model-B ethylene row `phi=1.03`. The repository therefore treats the identity as **unresolved**, not as an automatic rounding equivalence.

## Why the case is still blocked

The current public record is not yet sufficient to execute the exact Jin–Liu validation without introducing hidden assumptions. Four items remain:

1. resolve whether Jin's `phi=1.04` and Liu's model-B `phi=1.03` row are the same experimental condition or a distinct run/rounding convention;
2. recover the axial heat-release shape used in the Jin validation, or the fitted quasi-Gaussian parameters for that exact case, with a retained source/figure extraction record;
3. recover the **absolute stagnation-enthalpy increment** used by Jin and the mass flow needed by Eq. 11. The table ratio `Ht4/Ht3=1.16` is not converted into an absolute increment without a source-backed station-3 enthalpy value;
4. freeze the exact source-to-solver x-coordinate mapping over the model-B combustor.

The ACT-II facility paper shows that the arc heater was operated over several mass-flow rates (`7.3`, `13.3`, and `22.2 g/s` in facility characterization), but the repository does not assign any one of those values to the Liu 2019 validation run without direct evidence.

## Promotion rule

This candidate remains in `candidate_validation_chains`, not `candidate_formal_cases`.

Promotion is allowed only when the missing chain is recovered from traceable evidence. In particular, the project will not:

- infer air mass flow from the inlet geometry and nominal density/velocity;
- infer absolute combustion heat from `Ht4/Ht3` alone;
- digitize PLIF/enthalpy plots without recording the coordinate/calibration procedure;
- silently replace `phi=1.04` with `phi=1.03`;
- transplant the Liu/Jin heat-release distribution into the P11.2A Li geometry and call that validation.

## Scientific value if completed

A completed Jin–Liu model-B case would provide a substantially stronger P11.2B milestone than a synthetic heat-addition sweep. It would test the direct `Qdot'(x)` interface against an independent cavity-free experiment for which both pressure distribution and exit Mach are available, while remaining close to the quasi-one-dimensional assumptions of the current solver.

It would still be a prescribed-heat-release validation, not finite-rate chemistry validation and not an LBW/YBW classification result.
