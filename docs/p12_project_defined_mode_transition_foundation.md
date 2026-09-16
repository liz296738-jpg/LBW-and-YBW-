# P12 Project-Defined Mode-Transition Foundation

Status: **FOUNDATION / EVIDENCE GATE**

Classification: `P12_PROJECT_DEFINED_MODE_TRANSITION_APPLICATION`

This stage begins only after the accepted P11.4 integrated H2 smoke case, three-level grid audit, and discrete conservation audit. It does **not** claim Cao Ruifeng Case 2 reproduction and does not remove the Case 2 evidence blocker.

## Purpose

P12 studies whether the accepted one-dimensional infrastructure can support a defensible combustion-mode-transition application. The first step is to freeze the distinction between (a) numerical/physical observables already produced by the solver and (b) a source-backed transition criterion.

## Inputs that may be reused

The accepted P11.4 project-defined H2 case may be reused only as a project-defined baseline. Its geometry, inlet state, equivalence ratio, injector location, mixing constant, injection state, zero explicit wall-heat-gradient scope, Rusanov flux, SSP-RK3 integration, CFL choice, and Eq.11.46 steady gate remain project choices or previously documented model choices.

No Cao-specific geometry, prescribed species profile, shock-train geometry, transition threshold, or transition location may be inferred from that baseline.

## Solver observables already available

A future P12 sweep may record, without inventing a transition definition:

- local and extrema of Mach number;
- pressure and temperature;
- velocity and density;
- algebraic mixture composition;
- convergence diagnostics;
- discrete conservation diagnostics.

These are **observables**, not by themselves a source-backed mode label.

## Transition-classification evidence gate

A result must not be labelled `scramjet`, `ramjet`, `dual-mode`, `LBW`, `YBW`, or a Cao transition reproduction merely because a Mach-number threshold is crossed somewhere in the one-dimensional solution.

Before a source-defined mode classifier is implemented, freeze from an authoritative source:

1. the exact physical definition/criterion used for the relevant combustion modes;
2. the spatial domain over which that criterion is evaluated;
3. any shock-train / precombustion model and required geometry;
4. the transition observable(s) and threshold(s), including units and reference frame;
5. the parameter varied to induce transition and its source-defined range;
6. the expected comparison quantity (transition location, critical parameter, pressure signature, Mach signature, etc.).

If those items are incomplete, P12 may perform only a clearly labelled **project-defined response sweep** and must report continuous observables rather than categorical mode claims.

## First safe computational application

The next implementation step is therefore a `PROJECT_DEFINED_RESPONSE_SWEEP` around the accepted P11.4 H2 baseline. It should vary only an explicitly project-defined control, keep all other accepted controls fixed, solve every point to the same steady/conservation gates, and record continuous pressure/temperature/Mach responses.

Recommended first control: equivalence ratio, because it is already an explicit input in the accepted H2 mapping. The sweep values themselves must be declared project choices; they are not Cao values unless independently source-backed.

Acceptance requirements:

- every point reaches the stated Eq.11.46 tolerance without weakening physical guards;
- positive/source-valid thermodynamic states are retained;
- mass-source bookkeeping remains exact and discrete mass inventory remains within the accepted audit convention;
- outputs are continuous observables only;
- no categorical combustion-mode transition is claimed until the transition-classification evidence gate above is satisfied.

## Current blockers retained

- Cao Case 2 formal reproduction: blocked by missing exact source `A(x)` and prescribed `Yi(x)` information.
- Eq.11.26 dimensional wall-heat adapter: unresolved.
- variable-thermochemistry Steger-Warming production integration: unresolved source compatibility.
- Cao/source-defined mode-transition classifier: not yet frozen.

These blockers must remain visible while project-defined P12 work proceeds.
