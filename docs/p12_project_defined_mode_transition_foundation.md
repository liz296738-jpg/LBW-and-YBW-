# P12 Project-Defined Mode-Transition Foundation

Status: **ACTIVE / EVIDENCE-GATED RESPONSE STUDY**

Classification: `P12_PROJECT_DEFINED_MODE_TRANSITION_APPLICATION`

This stage begins only after the accepted P11.4 integrated H2 smoke case, three-level grid audit, and discrete conservation audit. It does **not** claim Cao Ruifeng Case 2 reproduction and does not remove the Case 2 evidence blocker.

## Purpose

P12 studies whether the accepted one-dimensional infrastructure can support a defensible combustion-mode-transition application. The first step is to freeze the distinction between (a) numerical/physical observables already produced by the solver and (b) a source-backed transition criterion.

## Inputs that may be reused

The accepted P11.4 project-defined H2 case may be reused only as a project-defined baseline. Its geometry, inlet state, equivalence ratio, injector location, mixing constant, injection state, zero explicit wall-heat-gradient scope, Rusanov flux, SSP-RK3 integration, CFL choice, and Eq.11.46 steady gate remain project choices or previously documented model choices.

No Cao-specific geometry, prescribed species profile, shock-train geometry, transition threshold, or transition location may be inferred from that baseline.

## Solver observables already available

A P12 sweep may record, without inventing a transition definition:

- local and extrema of Mach number;
- pressure and temperature;
- velocity and density;
- algebraic mixture composition;
- convergence diagnostics;
- discrete conservation diagnostics.

These are **observables**, not by themselves a source-backed mode label.

## Transition-classification evidence gate

A result must not be labelled `scramjet`, `ramjet`, `dual-mode`, `LBW`, `YBW`, `unstart`, or a Cao transition reproduction merely because a Mach-number threshold is crossed, a run stops converging, or an existing solver-domain guard is triggered.

Before a source-defined mode classifier is implemented, freeze from an authoritative source:

1. the exact physical definition/criterion used for the relevant combustion modes;
2. the spatial domain over which that criterion is evaluated;
3. any shock-train / precombustion model and required geometry;
4. the transition observable(s) and threshold(s), including units and reference frame;
5. the parameter varied to induce transition and its source-defined range;
6. the expected comparison quantity (transition location, critical parameter, pressure signature, Mach signature, etc.).

If those items are incomplete, P12 may perform only a clearly labelled **project-defined response sweep** and must report continuous observables and solver-admissibility status rather than categorical mode claims.

## First computational application

The first application is a `PROJECT_DEFINED_RESPONSE_SWEEP` around the accepted P11.4 H2 baseline. It varies only an explicitly project-defined control, keeps all other accepted controls fixed, and records continuous pressure/temperature/Mach responses together with convergence, conservation, and solver-admissibility diagnostics.

The first control is equivalence ratio because it is already an explicit input in the accepted H2 mapping. The initial values `0.10`, `0.20`, and `0.30` are project choices; they are not Cao values or transition thresholds.

Acceptance requirements:

- every **accepted response point** reaches the stated teacher Eq.11.46 density-change tolerance without weakening physical guards;
- the independent normalized semi-discrete residual is reported as a secondary diagnostic and is not assigned an unsourced acceptance threshold;
- positive/source-valid thermodynamic states are retained for accepted response points;
- mass-source bookkeeping remains exact, and normalized mass/momentum/energy inventory rates are reported for converged points;
- if an existing physical/model-domain guard is triggered, the point is recorded explicitly as outside the currently admissible solver path rather than forcing convergence by disabling the guard;
- a guarded or nonconverged point is excluded from continuous-response inference unless and until a model extension is separately justified and verified;
- outputs remain continuous observables and solver status only;
- no categorical combustion-mode transition is claimed until the transition-classification evidence gate above is satisfied.

The currently retained forward-flow restriction in the teacher Eq.11.38 friction adapter is an example of such a guard. Triggering it is a numerical/model-domain observation, not by itself evidence of inlet unstart or a combustion-mode transition.

## Current blockers retained

- Cao Case 2 formal reproduction: source identity and Table 2-2 inlet data are frozen, but exact source `A(x)`, prescribed `Yi(x)`, and the original fuel/source spatial convention remain incomplete.
- Eq.11.26 dimensional wall-heat adapter: unresolved.
- variable-thermochemistry Steger-Warming production integration: unresolved source compatibility.
- Cao/source-defined mode-transition classifier: not yet frozen.

These blockers must remain visible while project-defined P12 work proceeds.
