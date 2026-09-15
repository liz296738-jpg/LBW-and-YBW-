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

The project-priority correction remains important: external validation and later mode-transition applications must not displace completion of the teacher-reference physical closures.

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
| Steady convergence Eq. 11.46 | Relative-density diagnostic implemented in `max_relative_density_change` | **Aligned as compatibility diagnostic** | Keep existing normalized residual too; do not weaken convergence |
| Temperature/composition-dependent gas properties | Isolated teacher/Cao thermochemistry layer implemented; production solver remains constant-gas | **Foundation aligned; integration gated** | Freeze coefficient database and then integrate variable thermo into state recovery |
| `cp(T)`, `h(T)` Chemkin/NASA polynomial mixture properties | Teacher/Cao six-coefficient evaluator, mixture properties, and `e -> T` inversion implemented | **Equation layer aligned** | Freeze source-backed species coefficients and temperature intervals; add piecewise interval selection if required |
| Mixing efficiency / mixing length | Not implemented as teacher closure | **Major gap** | Implement Eqs. 11.19-11.20 after transcription/source audit |
| Equivalence ratio / fuel-specific composition model | Not production implemented | **Major gap** | Implement Eqs. 11.21-11.29 in a separate tested closure layer |
| Empirical friction law versus combustion state | Not implemented | **Gap** | Add optional Eq. 11.25 closure |
| Empirical wall heat-transfer law versus combustion state | Not implemented | **Gap** | Add optional Eq. 11.26 closure |
| Chemical energy through composition/enthalpy | Direct `Qdot'(x)` remains a surrogate; absolute species enthalpy bookkeeping policy frozen | **Boundary explicitly controlled** | Do not double-count reaction energy when composition-dependent enthalpy is integrated |
| Combustion-mode transition study | Infrastructure/diagnostics exist, but no teacher-complete model yet | **Premature as primary milestone** | Defer until teacher-reference integrated model is ready |
| NASA/Jin/Liu benchmark work | Extensive and source-traced | **Useful, not wasted** | Keep as supporting V&V, not the project objective |

## Teacher-reference equations that control the implementation sequence

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

The repository already covers a large portion of the numerical skeleton. Eq. 11.46 compatibility is implemented as an additional diagnostic. The isolated Eq. 11.30-11.35 thermochemistry layer is now implemented and tested; its production integration remains intentionally blocked until the coefficient database is source-frozen.

Detailed P11.3B report: `docs/teacher_thermochemistry.md`.

## Important energy-accounting correction

The teacher reference explicitly states that the fitted absolute species enthalpy contains sensible enthalpy plus the zero-point / chemical-energy contribution. The current repository's direct prescribed `Qdot'(x)` combustion input is still useful as a validated reduced-order **surrogate** and for V&V, but it is not silently treated as identical to the final teacher-reference reacting formulation.

When variable composition and species enthalpy are introduced, chemical energy must be accounted for exactly once. A future implementation must not both:

1. change species/composition-dependent enthalpy to represent reaction chemistry, **and**
2. add the same chemical energy again through the direct `Qdot'(x)` source.

External wall/additional heat remains a separate source. This is a project-level invariant.

## Corrected development priority

The next primary development sequence is:

1. finish numerical compatibility: boundary/case adapters if needed and a sourced policy for near-sonic Steger-Warming smoothing;
2. finish P11.3B by freezing and independently validating the thermochemical coefficient database, then integrate variable thermo into state recovery;
3. mixing-efficiency, mixing-length, equivalence-ratio, and composition closures;
4. teacher empirical friction and wall heat-transfer closures;
5. integrated teacher-reference case and regression/verification;
6. only then use the completed model for mode-transition/parameter studies.

The NASA Burrows-Kurkov and Jin/Liu work remains in the repository as supporting verification and evidence infrastructure. It no longer controls the project roadmap.
