# Eq.11.26 External Source Search Audit

## Question

Can the currently source-gated teacher Eq.11.26 empirical wall-heat
coefficient be converted, from traceable external evidence, into the
dimensional `d(delta q)/dx` input required by teacher Eq.11.38?

## Result

**No source-traceable unique adapter has been recovered. The gate remains
closed.**

This is a negative evidence record: it documents what was searched and why
plausible alternative wall-heat models are not silently substituted.

## What was corroborated

The teacher Eq.11.25 friction polynomial

`f = 0.0018 + 0.001958 z + 0.00927 z^2 - 0.0088525 z^3`,
with `z=phi*eta`,

also appears in later dual-mode/scramjet modeling material. This provides
external corroboration that the friction correlation belongs to an established
model lineage.

That corroboration does **not** establish the meaning or dimensional adapter of
teacher Eq.11.26.

## What was not recovered

Exact-coefficient searches for the teacher Eq.11.26 polynomial did not recover
a sufficiently authoritative source that simultaneously defines:

1. the physical meaning of the Eq.11.26 output;
2. its dimensions;
3. whether it is a local coefficient, a heat-flux-like quantity, a
   specific-heat increment, or another empirical state;
4. the exact relation between that output and the `delta q` used in Eq.11.38;
5. whether geometric factors such as wetted perimeter / hydraulic diameter,
   mass flux, wall temperature, or reference enthalpy are already embedded.

Without those definitions, dimensional consistency alone cannot identify a
unique mapping.

## Why external wall-heat models are not substituted

Peer-reviewed scramjet reduced-order models commonly include wall heat
transfer. Some use reference-enthalpy / Eckert-type methods; others use
regenerative-cooling or empirical heat-transfer closures.

Those models establish that wall heat transfer is important, but they do not
prove that the teacher Eq.11.26 coefficient is algebraically identical to any
one of those formulations.

Replacing Eq.11.26 with an external heat-transfer correlation would therefore
be a **model change**, not a recovery of the teacher equation.

## Production policy

The current policy remains:

- keep the literal Eq.11.26 polynomial available for source transcription and
  isolated checks;
- do not interpret it as W/m^2, J/kg, or J/(kg m) without source evidence;
- keep the production teacher path's explicit
  `wall_specific_heat_gain_gradient_J_per_kg_per_m` channel;
- use zero in the project-defined H2 baseline as
  `SOURCE_GATED_NEUTRALIZATION`, not as a validated adiabatic-wall claim;
- do not promote an external Eckert/reference-enthalpy model into the teacher
  path unless a future project explicitly defines and validates a new model
  branch.

## Reopening criteria

The Eq.11.26 gate may be reopened only if one of the following is recovered:

- the missing teacher pages/notes that define Eq.11.26 and its coupling;
- a primary source explicitly identified by the teacher/Cao lineage that gives
  the dimensional relation;
- original code from the same model lineage with variables and units that can
  be unambiguously mapped back to the printed equations.

A visually reasonable temperature or pressure curve is not sufficient evidence.
