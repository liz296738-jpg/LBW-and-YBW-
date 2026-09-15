# P11.2B Jin Fig. 14 Applicability Boundary

## Purpose

This note records the assumptions and additional inputs that are required to reproduce the simple quasi-one-dimensional validation used by Jin et al. (2026). It is deliberately separate from the heat-release-shape evidence: recovering `Qdot'(x)` is necessary but is **not** sufficient to reproduce Fig. 14.

Primary source: Kaiyan Jin et al., *Experimental study on heat release distribution during supersonic combustion*, *Combustion and Flame* 287 (2026) 114876, DOI `10.1016/j.combustflame.2026.114876`, especially Sec. 3.2.3, Eqs. (9)-(11), and the Fig. 14 validation discussion.

## What the published one-dimensional equations actually require

The Jin pressure/Mach relations retain cross-sectional area, stagnation temperature, specific-heat ratio, combustor diameter, and a wall-friction coefficient `Cf`. The energy relation additionally requires the axial heat-release rate, mass flow, `cp`, and initial stagnation temperature.

Therefore a source-backed heat-release curve alone does not fully specify the published validation model. The exact Fig. 14 reproduction also needs a solver-ready inlet state and a wall-friction closure with a known coefficient convention.

## Explicit applicability assumptions in Jin

Jin states that the simple one-dimensional validation assumes the compared flow remains **supersonic** and is **free from flow separation**. Under that assumption the `M=1` singularity is avoided and shock-train / separation-induced effective-area complications are neglected.

The repository handles these statements asymmetrically:

- `min(M)>1` is numerically checkable after a run and is therefore implemented as an explicit diagnostic with no invented safety margin;
- absence of boundary-layer separation is **not** inferable from the present one-dimensional state vector;
- absence of a physical shock train is likewise not established merely because the reduced solver converges.

A future result may therefore claim compatibility with Jin's simple validation only if the Mach gate passes **and** the separation/shock-train assumptions remain defensible for the source condition.

## Newly identified evidence gaps

Two inputs were previously under-specified in the project readiness description:

1. **station-3 / combustor-inlet boundary state.** Liu defines station 3, but the accessible validation record does not directly tabulate the complete primitive or total state used to initialize Jin's external model-B calculation. Nominal freestream data are not silently substituted for the combustor-inlet state.
2. **wall-friction closure.** Jin Eqs. (9)-(10) explicitly retain `Cf`, but the accessible article text does not expose the numerical value used in Fig. 14. The repository production wall source accepts a **Darcy friction factor**, so a source-defined coefficient convention is also required before any Jin `Cf` value can be inserted.

Liu's separate one-dimensional mode-transition derivation presents a negligible-wall-friction relation. That is useful context, but it is **not evidence that Jin set `Cf=0` in Fig. 14**. The project therefore does not disable wall friction for the exact reproduction on that basis.

## Formal-case consequence

The exact Jin–Liu validation is currently blocked by six evidence items:

1. resolve the Jin model-B `phi=1.04` versus Liu model-B `phi=1.03` / model-A `phi=1.04` identity conflict;
2. recover the Fig. 14 axial heat-release shape or fitted parameters;
3. recover the matching absolute heat-addition scale;
4. resolve the `2 deg cone angle` convention needed for the radial area law;
5. recover the exact station-3 solver-ready inlet state for the validation run;
6. recover the Fig. 14 wall-friction coefficient and its convention, or a direct source statement that friction was disabled.

The source-to-solver **axial coordinate mapping is already closed** and is not part of this list.

Machine-readable evidence is stored in `cases/studies/data/p11_2b_jin_validation_applicability.json`. The formal-case gate now requires geometry, inlet state, and wall-friction evidence in addition to coordinate, heat-release-shape, and absolute-energy evidence.
