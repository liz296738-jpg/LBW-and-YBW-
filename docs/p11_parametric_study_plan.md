# P11 Parametric Study and Teacher-Reference Integration Plan

## Scientific scope

P11 converts the verified quasi-one-dimensional solver into reproducible physical studies while keeping numerical controls, physical inputs, modelling assumptions, and scientific claims separate.

**Naming correction:** `LBW` and `YBW` are people/project identifiers. They are not combustion modes and have no discrimination criterion.

The teacher-provided one-dimensional CFD / “second scheme” is the primary model target. Public literature cases and NASA benchmarks are supporting verification assets.

## Stage status

- P11.1 Parametric Study Foundation + controlled similarity pilot — **implemented and verified**.
- P11.2A Public source-backed cold-flow surrogate — **implemented and formally verified**.
- P11.2B Public heated reduced-order benchmark — **accepted with scoped claims** through NASA Burrows-Kurkov; Jin-Liu exact reproduction remains evidence-blocked but preserved.
- P11.3 Teacher-reference second-scheme completion — **current primary stage**.
- P11.4 Teacher/reference integrated reproduction and parameter study — planned after P11.3.
- Later combustion-mode-transition studies — planned only after the teacher-reference physical model is complete.

## Why the plan changed

The earlier roadmap incorrectly treated `LBW`/`YBW` as physical labels and began preparing a classifier. That interpretation was invalid. The teacher material instead makes the target much clearer: first build the one-dimensional model using the supplied CFD equations and Cao Ruifeng references.

The project foundation remains useful because it already implements most of the cited numerical skeleton. The correction is therefore a **priority correction, not a rewrite from zero**.

## P11.1 accepted foundation

P11.1 established reproducible metadata, controlled parameter matrices, repeatability, and study metrics using smooth quasi-one-dimensional cases. It is framework evidence, not engine calibration.

## P11.2A accepted supporting case

P11.2A uses the Li et al. public surrogate source, physical dimensions, and source-backed total inflow conditions to exercise the verified solver in a physical-scale cold-flow configuration. Its inert isolator-length response is retained as a model-scope result, not experimental validation.

## P11.2B accepted supporting benchmark

The project now contains an accepted NASA Burrows-Kurkov reduced-order computational-reference benchmark. Its purpose is to test public-data ingestion, thermodynamic reduction, conservative moment matching, signed source reconstruction, heated steady convergence, and grid refinement.

This benchmark does **not** replace the teacher-reference combustion model. It does not establish finite-rate chemistry, species transport, or the teacher's empirical mixing/combustion closures.

The Jin-Liu chain remains documented because it is scramjet-specific and scientifically useful, but unresolved same-condition evidence is not filled with assumptions.

## P11.3 teacher-reference completion

See `docs/teacher_reference_alignment.md` and `cases/studies/data/teacher_reference_alignment.json`.

### Numerical compatibility

Already present/completed:

- conservative quasi-one-dimensional formulation;
- variable-area finite-volume solver;
- first-order spatial treatment;
- raw Steger-Warming FVS;
- SSP/TVD RK3;
- CFL stepping;
- compatible physical/transmissive boundaries;
- Chapter 11 Eq. 11.46 maximum relative-density iteration-change diagnostic, added alongside the existing normalized steady-residual gate.

Remaining closeout:

- source-frozen policy for Eq. 11.44 near-sonic eigenvalue smoothing;
- teacher-reference case adapter for inlet/output semantics where needed.

### Variable thermochemistry

Production code currently uses calorically perfect gas properties. The teacher reference instead requires temperature- and composition-dependent mixture properties. The next thermodynamic layer must support source-backed species polynomial data and derived mixture `R`, `cp`, `h`, `cv`, and `gamma`.

This must be implemented as a separate verified path so the established constant-gas baseline remains available for regression and controlled comparisons.

### Mixing, combustion, and composition

The current solver accepts prescribed fuel and heat-source distributions. The teacher-reference model requires higher-level closures for mixing efficiency/mixing length, equivalence ratio, and fuel-specific composition. These closures must be transcribed from the supplied references, unit-tested outside the solver, and only then integrated.

### Friction and wall heat

Generic prescribed Darcy friction and wall heat flux remain valid low-level interfaces. Teacher-reference empirical closures are to be added as optional source generators rather than hard-coded into the core residual.

### Chemical energy bookkeeping

The photographed chapter distinguishes external wall/additional heat from chemical reaction energy. Therefore the direct `Qdot'(x)` path is retained as a surrogate interface, not silently redefined as the teacher's final chemistry model.

When species/composition-dependent enthalpy carries chemical energy, the same reaction energy must not also be added through `Qdot'(x)`.

## P11.4 integrated teacher/reference case

After P11.3 components are individually verified:

1. select one source-defined geometry and operating condition from the teacher/Cao reference set;
2. run the integrated model without hand tuning;
3. report convergence using both project residual diagnostics and the teacher-reference density-change metric;
4. audit mass, momentum, and energy;
5. compare source-available pressure, temperature, Mach/velocity, and other observables;
6. perform grid/sensitivity checks before parameter sweeps.

## Future mode-transition work

Combustion-mode transition is a later application because it appears in the Cao research direction. It must use the Cao/teacher definitions and observables after the underlying model is ready.

Mach extrema, sonic fractions, sonic margin, and sonic-crossing count remain diagnostics unless a source explicitly promotes them into a criterion. None of them are related to the names `LBW` or `YBW`.

## Metric metadata contract

Each formal study must report symbol, units, definition, interpretation, scope, source status, and whether the metric is a scientific gate or a diagnostic. Physical inputs must additionally record source/locator, raw value, SI conversion, and derivation status (`source`, `derived`, `model-assumption`, `numerical-control`, or `deferred`).
