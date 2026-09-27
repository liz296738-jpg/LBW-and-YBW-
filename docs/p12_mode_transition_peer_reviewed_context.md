# P12 Peer-Reviewed Context for Combustion-Mode Transition

## Authority boundary

The teacher-provided Cao Ruifeng doctoral dissertation remains the **primary
source** for the implemented Eq.(3-2) thermal-throat criterion and Table 3-1
definitions.

The papers below are supporting peer-reviewed context. They do not replace the
dissertation criterion or supply missing Cao Case 2 spatial inputs.

## Cao et al. — transition-boundary sensitivity

R. Cao, Y. Lu, D. Yu, and J. Chang,
“Study on influencing factors of combustion mode transition boundary for a
scramjet engine based on one-dimensional model,”
*Aerospace Science and Technology*, 96 (2020), 105590.
DOI: https://doi.org/10.1016/j.ast.2019.105590

This paper uses the authors' one-dimensional scramjet model to study how the
mode-transition boundary changes with factors including:

- combustor duct-area profile;
- heat-release distribution;
- combustor wall temperature;
- wall roughness;
- incoming-air composition.

The important project consequence is that a transition boundary is not a
universal equivalence-ratio constant independent of geometry, heat release,
wall state, and inflow definition.

## Zhang et al. — experimental mode-transition sensitivity

Y. Zhang, B. Chen, G. Liu, B.-X. Wei, and X. Xu,
“Influencing factors on the mode transition in a dual-mode scramjet,”
*Acta Astronautica*, 103 (2014), 1--15.
DOI: https://doi.org/10.1016/j.actaastro.2014.06.006

The experimental study reports that transition locations/widths depend on
factors including:

- fuel type;
- injector configuration;
- inflow total temperature;
- fuel-injection distribution.

The experiment classifies modes using wall-pressure distributions together with
one-dimensional analysis and optical diagnostics. Its specific transition
equivalence ratios belong to its own combustor and boundary conditions.

## Consequences for this repository

1. **No universal phi threshold.** A value such as `phi=0.24`, `0.26`, or
   `0.30` in the project-defined H2 geometry cannot be promoted into a
   universal ram/scram transition equivalence ratio.

2. **Guard is not a mode classifier.** A forward-flow guard trigger contains no
   experimental pressure/shock/optical information and is not a substitute for
   the source-defined criterion.

3. **Geometry matters.** The missing Cao Case 2 `A(x)` is not a cosmetic
   input: peer-reviewed Cao-lineage work explicitly identifies combustor area
   profile as a transition-boundary influence.

4. **Wall state matters.** The unresolved teacher Eq.11.26 wall-heat coupling
   cannot be assumed irrelevant to a future formal transition-boundary
   reproduction, because wall temperature/roughness can move the boundary in
   the Cao-lineage model.

5. **Project-defined sweeps remain sensitivity studies.** P12/P13 results are
   useful for testing the current reduced-order model but cannot establish a
   source/experimental transition boundary unless geometry, wall treatment,
   inflow, and classification observables are source-compatible.

## Claim policy

These papers may strengthen model-scope and uncertainty statements. They may
not be used to:

- overwrite the dissertation Eq.(3-2) or Table 3-1 formulas;
- import an experimental transition equivalence ratio into the current model;
- infer the missing Cao Case 2 geometry;
- convert a numerical solver failure into a physical combustion mode;
- claim that the current project-defined H2 sweep experimentally validates
  mode transition.
