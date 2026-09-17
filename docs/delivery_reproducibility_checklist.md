# Delivery and Reproducibility Checklist

This checklist defines when the course project may be described as **deliverable complete**. It does not weaken any scientific evidence gate.

## 1. Accepted integrated H2 baseline

Required evidence:

- clearly labelled `PROJECT_DEFINED_INTEGRATED_SMOKE_CASE`;
- reproducible run command/configuration;
- Eq. 11.46 maximum relative-density steady diagnostic;
- independent normalized residual reported as a diagnostic, not an unsourced hard threshold;
- no NaN or hidden invalid thermodynamic state;
- forward-flow guard retained.

Primary record: `cases/studies/data/p11_4_project_defined_h2_smoke_acceptance.json`.

## 2. Three-level grid evidence

Required evidence:

- 20/40/80 cells or an explicitly equivalent three-level sequence;
- identical physical boundary conditions, thermochemistry, source definitions, and convergence definition across the compared levels;
- key continuous outputs and successive changes reported;
- wording limited to **grid-convergence trend** unless an asymptotic/GCI analysis is actually performed.

Primary record: `cases/studies/data/p11_4_grid_convergence_acceptance.json` plus the frozen P12 grid-refined evidence.

## 3. Discrete conservation evidence

For each formally accepted integrated/response point report dimensionless inventory rates for:

- mass;
- momentum;
- total energy.

The normalization scale must be stated. The existing mass gate is 0.5% of the inlet mass-flow scale or stricter. Momentum and energy remain quantified diagnostics until a defensible threshold is frozen from stable baseline/grid evidence; no threshold may be invented merely to pass CI.

## 4. Project-defined response sweep

Required outputs for each attempted equivalence-ratio point:

- admissibility status;
- Eq. 11.46 convergence status/value;
- normalized residual diagnostic;
- Mach, pressure, temperature, velocity and density response;
- composition response;
- normalized mass/momentum/energy inventory diagnostics.

A forward-flow guard trigger is recorded as `solver/model-domain inadmissible`. It is not evidence of unstart or a combustion-mode transition.

Primary record: `cases/studies/data/p12_project_defined_response_sweep_acceptance.json`.

### Delivery gate audit note

The P12 response-sweep acceptance record has now been rerun and re-frozen under the authoritative Eq. 11.46 maximum relative-density-change gate of `2e-5`. The accepted `phi=0.1` and `phi=0.2` points satisfy that gate and retain the existing 0.5% normalized mass-inventory requirement. Normalized residual remains an independent diagnostic only, with no unsourced hard threshold. The attempted `phi=0.3` point remains `solver/model-domain inadmissible` because the forward-flow guard is triggered; this is not interpreted as unstart or as a combustion-mode transition. The superseded `1e-4` record remains historical provenance only and is not the current delivery evidence.

## 5. Source-backed reproduction lane

Cao Case 2 must remain separate from project-defined response work. Source identity and Table 2-2 inlet data are frozen. Formal reproduction remains blocked until the exact source provides or unambiguously determines:

- `A(x)`;
- prescribed `Yi(x)` spatial profiles/rule;
- fuel/injection/source spatial convention.

No geometry digitization, guessed species profile, or project-defined closure may silently fill these fields.

## 6. Known model blockers

Keep explicit until source-resolved:

- variable-thermochemistry Steger-Warming energy compatibility and Eq. 11.44 epsilon policy;
- dimensional Eq. 11.26 wall-heat mapping;
- source-compatible isolator/shock-train information needed for broader categorical mode-transition claims;
- compatible `C10H22` thermochemistry if required.

The verified Rusanov integrated path remains the production route while these blockers are open.

## 7. Final package contents

Before marking the project deliverable complete, the repository must expose, from `main`:

- accepted H2 integrated-case configuration and run command;
- convergence history/summary and key flow/composition distributions;
- 20/40/80 grid evidence;
- discrete mass/momentum/energy conservation diagnostics and scale definitions;
- project-defined parameter-response results satisfying the authoritative Eq. 11.46 steady gate;
- source/derived/project-defined/unresolved provenance labels for scientific inputs;
- current blocker list;
- passing ordinary `pytest`/CI for the exact delivery commit.

A source reproduction is **not** required for the project-defined delivery package, but the package must explicitly state that Cao Case 2 reproduction remains blocked if its evidence gate is still incomplete.
