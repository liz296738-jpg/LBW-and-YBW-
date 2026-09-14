# P11.2B Formal-Case Promotion Gate

## Purpose

P11.2B now has enough software capability to accept a prescribed axial heat-addition profile, but software capability is not evidence that a physical heated case is defined. `cases/studies/p11_2b_case_gate.py` therefore separates **solver readiness** from **scientific case readiness**.

The gate asks one narrow question: does a candidate contain enough traceable, internally consistent evidence to be promoted from an exploratory surrogate to a formal source-backed P11.2B case?

Passing the gate authorizes execution of a reduced-order prescribed-heat-release case. It does not constitute experimental validation, detailed chemistry validation, or LBW/YBW classification.

## Required evidence bundle

Every formal candidate must contain the following from one declared source/operating-condition chain:

1. source identity and operating-condition ID;
2. source locators for the promoted numerical inputs;
3. an explicit mapping from the source axial coordinate to the solver coordinate, expressed in metres and documenting both origins, scale, and offset;
4. one complete heat-release evidence path.

Two evidence paths are deliberately distinct:

### Path A — normalized Eq. 8 shape + separate absolute energy

The candidate provides source-backed `x_i`, `x_m`, `x_c`, and `k` in metres for the normalized asymmetric Eq. 8 shape. Because a normalized shape contains no absolute `W/m` scale, it must also provide exactly one source-backed absolute-energy quantity for the same operating condition:

- positive total heat-release power [W], or
- positive stagnation-enthalpy increment [J/kg] together with positive mass flow [kg/s].

### Path B — absolute tabulated line heat

The candidate provides a traceable tabulated `x [m]` / `Qdot'(x) [W/m]` distribution for the same declared case. This profile already contains both axial shape and absolute energy scale. A second `absolute_energy` block is rejected rather than used to rescale the data, because two independent absolute scales could conflict.

The gate rejects cross-source or cross-condition mixing even when every individual number looks physically plausible.

## Explicitly rejected shortcuts

The repository does not promote a case by:

- combining a normalized heat-release shape from one experiment with total power from an unrelated experiment and calling it a reproduction;
- adding a second independent absolute energy scale to an already absolute tabulated `Qdot'(x)` profile;
- assuming 100% combustion efficiency in order to manufacture total power;
- deriving total power from equivalence ratio while fuel identity, LHV, oxidizer convention, or stoichiometric basis is unresolved;
- reading coordinates from a figure without retaining the extraction record and coordinate convention;
- treating normalized CH* chemiluminescence intensity as an absolute `W/m` distribution without an independent energy scale.

These restrictions are scientific provenance rules, not numerical limitations of the solver.

## Machine-readable status

The source ledger contains `candidate_formal_cases`. It is intentionally empty at the current stage because SRC07-SRC09 do not yet provide either a complete absolute tabulated line-heat profile or a complete same-condition normalized-shape-plus-energy bundle in the accessible records.

`cases/studies/p11_2b_readiness.py` converts that ledger into a deterministic JSON readiness record. Running

```text
python cases/studies/p11_2b_readiness.py
```

writes `artifacts/p11_2b/p11_2b_readiness.json` and exits successfully even when the project is correctly blocked. Adding `--require-ready` turns the readiness state into a hard execution gate and returns a nonzero status until at least one candidate satisfies all evidence requirements.

This distinction is deliberate: CI should be able to verify that the project is **correctly blocked** without pretending that missing physical evidence is a software failure.

## Current result

Current machine-readable conclusion:

`BLOCKED_PENDING_SOURCE_BACKED_ABSOLUTE_PROFILE_OR_SHAPE_PLUS_ENERGY`

The remaining work is therefore evidence recovery rather than another solver rewrite. The preferred next input is either a source-backed absolute `Qdot'(x)` table or a complete same-condition normalized shape plus absolute-energy chain from the Cao-designated material, Jin supplementary/author data, or another authoritative source with equivalent traceability.
