# P12 Project-Defined Mode-Transition Foundation

Status: **SOURCE CRITERION RECOVERED / PROJECT APPLICATION ACTIVE**

Classification: `P12_PROJECT_DEFINED_MODE_TRANSITION_APPLICATION`

This stage begins only after the accepted P11.4 integrated H2 smoke case, three-level grid audit, and discrete conservation audit. It does **not** claim Cao Ruifeng Case 2 reproduction and does not remove the Case 2 evidence blocker.

## Purpose

P12 studies whether the accepted one-dimensional infrastructure can support a defensible combustion-mode-transition application. The project now distinguishes explicitly between (a) numerical/physical observables produced by the solver, (b) source-defined combustion-mode criteria recovered from Cao Ruifeng's doctoral dissertation, and (c) project-defined geometry and operating points.

## Inputs that may be reused

The accepted P11.4 project-defined H2 case may be reused only as a project-defined baseline. Its geometry, inlet state, equivalence ratio, injector location, mixing constant, injection state, zero explicit wall-heat-gradient scope, Rusanov flux, SSP-RK3 integration, and CFL choice remain project choices or previously documented model choices. Teacher Eq.11.46 supplies the maximum relative-density-change convergence metric; each numerical tolerance applied to that metric is separately frozen as a project numerical setting unless an explicit teacher-source threshold is recovered.

No Cao-specific geometry, prescribed species profile, shock-train geometry, transition location, or Case 2 result may be inferred from that baseline.

## Solver observables already available

A P12 sweep may record:

- local and extrema of Mach number;
- pressure and temperature;
- velocity and density;
- algebraic mixture composition;
- convergence diagnostics;
- normalized discrete conservation diagnostics;
- explicit solver-admissibility status.

These observables may be evaluated with a source-defined criterion only when the corresponding solution is admissible and converged.

## Recovered source-defined criterion

The teacher-provided Cao Ruifeng doctoral dissertation has now been checked directly at the relevant source pages. The source record and implementation are:

- `cases/studies/data/p12_cao_mode_criterion_source.json`;
- `docs/p12_cao_source_mode_criteria.md`;
- `src/scramjet1d/cao_mode_criteria.py`.

For the broad two-mode thermal-throat distinction, Cao Eq. (3-2) defines:

- scram side: `min(Ma(x)) > 1`;
- ram side: `min(Ma(x)) < 1`;
- transition boundary: the thermal throat is exactly critical at `Ma = 1`.

The dissertation does not prescribe a floating-point sonic tolerance. Any numerical tolerance used around `Ma=1` is therefore an explicit project numerical choice, not a source physical threshold.

Cao Table 3-1 also supplies the more detailed no-shock scram / oblique-shock scram / ram criteria involving `Ma_s`, `Ma_2`, `Ma_3m`, and `Ma_2min`. Those equations are transcribed and tested, but the detailed classifier is not attached to the current integrated project-defined combustor because the accepted solver does not yet provide all source-compatible isolator/shock-train state variables and geometry.

A solver guard, nonconvergence, or numerical failure is never converted into a combustion-mode or unstart label.

## First accepted computational application

The first `PROJECT_DEFINED_RESPONSE_SWEEP` varies equivalence ratio at `0.10`, `0.20`, and `0.30`. Those values are project choices, not Cao transition values.

The accepted evidence record is:

`cases/studies/data/p12_project_defined_response_sweep_acceptance.json`

Results:

- `phi=0.10`: converged and fully supersonic, with `min(Ma)=1.691903...`;
- `phi=0.20`: converged and fully supersonic, with `min(Ma)=1.271409...`;
- `phi=0.30`: the existing forward-flow Eq.11.38 friction guard is triggered during the cold-start pseudo-time path and no physical mode label is assigned.

Applying Cao Eq. (3-2) to the two admissible converged points places both robustly on the source-defined scram side over the explicit numerical sonic-tolerance sensitivity set `1e-6`, `1e-4`, `1e-3`, `1e-2`. The accepted points therefore do **not** yet bracket the `Ma=1` transition boundary.

## Current numerical continuation step

The next safe experiment is a guarded warm-start continuation from the accepted `phi=0.20` state toward higher equivalence ratio. Each next initial condition must be remapped consistently to the new composition while preserving primitive `p/T/u` and recomputing density and conservative energy with the new mixture thermochemistry.

This continuation is a numerical strategy only. It does not alter the physical model, weaken the forward-flow guard, or turn a failed/guarded point into a mode label.

## Acceptance rules retained

- every accepted response point must satisfy the explicitly stated project numerical tolerance applied to the teacher Eq.11.46 density-change metric;
- normalized residual remains an independent diagnostic and is not assigned an unsourced threshold;
- positive/source-valid thermodynamic states must be retained;
- normalized mass/momentum/energy inventory diagnostics must be reported for converged points;
- the existing 0.5% normalized mass-inventory gate is retained;
- guarded or nonconverged points receive no physical mode label;
- a source criterion applied to project-defined geometry must be reported as a project application of the criterion, not a Cao Case 2 reproduction.

## Current blockers retained

- Cao Case 2 formal reproduction: source identity and Table 2-2 inlet data are frozen, but exact source `A(x)`, prescribed `Yi(x)`, and the original fuel/source spatial convention remain incomplete.
- Eq.11.26 dimensional wall-heat adapter: unresolved.
- variable-thermochemistry Steger-Warming production integration: unresolved source compatibility.
- detailed Cao Table 3-1 production classification: source criteria are frozen, but source-compatible isolator/shock-train variables and geometry are not yet available in the current integrated path.

These blockers must remain visible while project-defined P12 work proceeds.
