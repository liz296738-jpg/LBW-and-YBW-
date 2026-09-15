# Teacher-reference alignment review

## Why this review exists

The teacher-provided material is the primary project direction. The uploaded package contains the teacher's group instructions, photographed pages from the chapter **“双模态冲压燃烧室一维数值模拟”**, and two Cao Ruifeng theses. The teacher's instruction is to learn the CFD equations and first build the one-dimensional ramjet/scramjet model; the teacher also describes this as a second scheme whose calculation results are expected to be more accurate.

A naming correction is frozen here:

**`LBW` and `YBW` are people/project identifiers. They are not combustion-mode labels.**

Any roadmap that treats `LBW`/`YBW` as physical modes is invalid and must not be merged.

## Overall finding

The current repository has **not gone in the opposite direction**. Its numerical foundation is strongly aligned with the teacher's second-scheme route:

- unsteady quasi-one-dimensional conservative equations;
- mass, momentum, and energy states;
- variable-area source terms;
- wall friction and wall heat-transfer source interfaces;
- fuel mass/momentum/energy source interfaces;
- first-order finite-volume/upwind discretization;
- Steger-Warming flux-vector splitting;
- third-order TVD/SSP Runge-Kutta time advancement;
- CFL-controlled stepping;
- steady-state convergence infrastructure.

The main problem is not that the foundation is wrong. The problem is that the project recently began to treat **mode classification and external validation evidence as the next main deliverable before completing the teacher-reference physical closures**. That priority is now corrected.

## Detailed alignment matrix

| Teacher/reference item | Current repository | Assessment | Required adjustment |
| --- | --- | --- | --- |
| Unsteady quasi-1D conservative CFD | Implemented | **Aligned** | Keep |
| Variable-area source | Implemented | **Aligned** | Keep |
| Fuel mass/momentum/enthalpy addition | Prescribed source interfaces implemented | **Structurally aligned** | Later connect to teacher-reference mixing/combustion closure |
| Wall friction | Generic prescribed Darcy factor | **Partially aligned** | Add optional teacher empirical closure rather than replacing generic interface |
| Wall heat transfer | Generic prescribed wall heat flux | **Partially aligned** | Add optional teacher empirical closure rather than replacing generic interface |
| Steger-Warming FVS | Implemented | **Aligned except sonic smoothing** | Add source-frozen near-sonic smoothing after epsilon policy is resolved |
| First-order upwind spatial treatment | Implemented | **Aligned** | Keep |
| Third-order TVD RK | SSP-RK3 implemented with the same stage coefficients | **Aligned** | Keep |
| CFL time step | General CFL implementation | **Aligned in principle** | Teacher-specific value can be a case/configuration choice, not a magic constant |
| Inlet static p/T/u | Supersonic primitive inflow implemented | **Functionally compatible** | Add a helper/case adapter if useful; do not rewrite BC core |
| Outlet first-order extrapolation | Transmissive/zero-gradient style path exists | **Functionally compatible** | Keep and document compatibility |
| Steady convergence Eq. 11.46 | Current gate uses normalized steady RHS residual | **Gap** | Add relative-density-change diagnostic alongside current gate |
| Temperature/composition-dependent gas properties | Production gas model uses constant `gamma`, `R` | **Major gap** | Implement isolated variable thermochemistry layer |
| `cp(T)`, `h(T)` Chemkin/NASA polynomial mixture properties | NASA-BK study utility proves polynomial evaluation concept, but not production integrated | **Major gap** | Generalize with source-backed coefficients and tests |
| Mixing efficiency / mixing length | Not implemented as teacher closure | **Major gap** | Implement Eqs. 11.19-11.20 after transcription/source audit |
| Equivalence ratio / fuel-specific composition model | Not production implemented | **Major gap** | Implement Eqs. 11.21-11.29 in a separate tested closure layer |
| Empirical friction law versus combustion state | Not implemented | **Gap** | Add optional Eq. 11.25 closure |
| Empirical wall heat-transfer law versus combustion state | Not implemented | **Gap** | Add optional Eq. 11.26 closure |
| Chemical energy through composition/enthalpy | Current direct `Qdot'(x)` path is an energy-only surrogate | **Important model-boundary difference** | Keep surrogate for V&V, but do not call it the final teacher chemistry model; avoid chemical-energy double counting |
| Combustion-mode transition study | Infrastructure/diagnostics exist, but no teacher-complete model yet | **Premature as primary milestone** | Defer until teacher-reference integrated model is ready |
| NASA/Jin/Liu benchmark work | Extensive and source-traced | **Useful, not wasted** | Reclassify as supporting V&V, not the project objective |

## Teacher-reference equations that now control the next implementation phase

The photographed chapter's equation chain is the target for compatibility work:

- continuity with mass addition;
- momentum with area change, wall friction, and injected-stream momentum;
- total-energy equation with wall/additional heat and injected-stream total enthalpy;
- mixing efficiency and mixing-length empirical closure (Eqs. 11.19-11.20);
- equivalence-ratio/stoichiometric and fuel-specific composition closure (Eqs. 11.21-11.29);
- species and mixture `cp(T)`, `h(T)`, `gamma(T,Y)`, `R(Y)` (Eqs. 11.30-11.35);
- unified conservative source form (around Eq. 11.38);
- third-order TVD RK (Eq. 11.39);
- Steger-Warming flux splitting (Eqs. 11.40-11.42);
- near-sonic eigenvalue smoothing (Eq. 11.44);
- CFL time step (Eq. 11.45);
- relative-density steady criterion (Eq. 11.46).

The repository already covers a large portion of the numerical skeleton. The missing work is concentrated in the **physical closure/thermochemistry layer** and a few teacher-specific numerical compatibility details.

## Important energy-accounting correction

The teacher reference explicitly distinguishes wall/additional heat from chemical reaction energy. The current repository's direct prescribed `Qdot'(x)` combustion input is still useful as a validated reduced-order **surrogate** and for V&V. It must not be silently treated as identical to the final teacher-reference reacting formulation.

When variable composition and species enthalpy are introduced, chemical energy must be accounted for exactly once. A future implementation must not both:

1. change species/composition-dependent enthalpy to include reaction chemistry, **and**
2. add the same chemical energy again through the direct `Qdot'(x)` source.

This is now a project-level invariant.

## Corrected development priority

The next primary development sequence is:

1. teacher numerical-compatibility closeout: relative-density convergence diagnostic, boundary/case compatibility, and a sourced policy for near-sonic Steger-Warming smoothing;
2. variable temperature/composition thermodynamics;
3. mixing-efficiency, mixing-length, equivalence-ratio, and composition closures;
4. teacher empirical friction and wall heat-transfer closures;
5. integrated teacher-reference case and regression/verification;
6. only then use the completed model for mode-transition/parameter studies.

The NASA Burrows-Kurkov and Jin/Liu work remains in the repository as supporting verification and evidence infrastructure. It no longer controls the project roadmap.
