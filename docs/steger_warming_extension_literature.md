# External Literature Audit: Generalized Steger--Warming for Real/Reactive Gases

## Purpose

The teacher/Cao audit established that the supplied project sources do not state how the classical Chapter 11 Steger--Warming energy split should be reconciled with the repository's variable-`cp(T,Y)`, composition-dependent absolute species-energy formulation.

A separate literature search was therefore performed to answer a different question:

> Does peer-reviewed numerical-method literature contain Steger--Warming-type extensions for thermally perfect, real-gas, multicomponent, or nonequilibrium flows?

The answer is **yes**. This changes the wording of the blocker, but it does **not** authorize silently replacing the teacher formulation.

## Relevant peer-reviewed literature

### Liu & Vinokur (1989)

Y. Liu and M. Vinokur, “Nonequilibrium Flow Computations. I. An Analysis of Numerical Formulations of Conservation Laws,” *Journal of Computational Physics*, 83(2), 373--397, 1989. DOI: https://doi.org/10.1016/0021-9991(89)90125-3

The paper generalizes several flux-Jacobian-based numerical methods, including Steger--Warming, to general thermal and chemical nonequilibrium flows.

**Relevance:** demonstrates that rigorous generalized FVS formulations exist for thermochemically complex gases.

**Non-substitution boundary:** the paper uses a broader nonequilibrium state system than the current three-equation algebraic-composition teacher path. Its formulas cannot be inserted into the present solver without a dedicated state-vector/Jacobian derivation.

### Grossman & Walters (1989)

B. Grossman and R. W. Walters, “Analysis of Flux-Split Algorithms for Euler's Equations with Real Gases,” *AIAA Journal*, 27(5), 524--531, 1989. DOI: https://doi.org/10.2514/3.10142

This work derives real-gas flux-splitting procedures and discusses an equivalent-`gamma` representation for Steger--Warming, van Leer, and Roe-type schemes.

**Relevance:** shows that a real-gas Steger--Warming extension can be derived from thermodynamic structure rather than by an ad hoc energy offset.

**Non-substitution boundary:** an equivalent-`gamma` or real-gas formulation must be proven consistent with the exact EOS/energy variable used here before adoption.

### Liou, van Leer & Shuen (1990)

M.-S. Liou, B. van Leer, and J.-S. Shuen, “Splitting of Inviscid Fluxes for Real Gases,” *Journal of Computational Physics*, 87(1), 1--24, 1990. DOI: https://doi.org/10.1016/0021-9991(90)90222-M

Flux-vector and flux-difference splittings are derived for a general equilibrium real-gas equation of state, with one-dimensional shock-tube/nozzle applications.

**Relevance:** provides a rigorous general-EOS flux-splitting route and is especially useful as a reference for what thermodynamic derivatives must be handled consistently.

**Non-substitution boundary:** equilibrium real-gas treatment is not automatically identical to a prescribed algebraic-composition field carrying absolute species enthalpy.

### Bertolazzi & Manzini (2001)

E. Bertolazzi and G. Manzini, “A Triangle-Based Unstructured Finite-Volume Method for Chemically Reactive Hypersonic Flows,” *Journal of Computational Physics*, 166(1), 84--115, 2001. DOI: https://doi.org/10.1006/jcph.2001.6644

The method explicitly uses a Steger--Warming flux-vector-splitting approach generalized to mixtures of thermally perfect gases.

**Relevance:** this is the closest direct literature evidence that Steger--Warming can be generalized to multicomponent thermally perfect mixtures.

**Non-substitution boundary:** the method evolves a chemically reactive multicomponent system with species equations. The current teacher production path instead uses three conservative gas-dynamic equations plus a frozen algebraic composition field. A dedicated reduction/projection proof would be required before claiming equivalence.

## Updated blocker interpretation

The scientifically correct statement is now:

- **Teacher/Cao source gap:** the supplied teacher/Cao material does not provide the variable-thermochemistry Steger--Warming reconciliation required by this repository.
- **External-method literature exists:** rigorous generalized Steger--Warming/real-gas FVS methods exist in peer-reviewed literature.
- **Production integration remains gated:** none of the reviewed papers has yet been shown to be algebraically identical to the repository's current state vector, absolute species-energy convention, frozen composition closure, and teacher Eq. 11.42--11.44 interface.
- **Rusanov remains the accepted production flux** until a dedicated derivation and verification program is completed.

## Minimum gate before any production replacement

A future generalized Steger--Warming implementation must satisfy all of the following before replacing Rusanov:

1. **State-vector compatibility:** derive the flux Jacobian/eigensystem for the exact conservative variables used by the production solver.
2. **Energy-reference invariance:** demonstrate that changing arbitrary species reference enthalpy does not change the physical numerical flux.
3. **Constant-property reduction:** recover the teacher/classical calorically-perfect Steger--Warming result to roundoff.
4. **Physical-flux recombination:** verify `F+ + F- = F(U)` for the variable-thermochemistry state over a representative test set.
5. **Contact/material-interface behavior:** check pressure/velocity consistency when composition changes across an interface.
6. **Positivity/admissibility:** preserve positive density/internal energy/temperature over controlled shock-tube and nozzle tests.
7. **Convergence verification:** demonstrate expected order on smooth manufactured/analytical cases before shock cases.
8. **Teacher-path regression:** reproduce all accepted H2 baseline/grid/conservation evidence without weakening existing guards.
9. **Near-sonic policy:** Eq. 11.44 smoothing epsilon must remain source-frozen or be explicitly labelled and justified as a project numerical policy; it cannot be guessed silently.
10. **No claim inflation:** even a successful generalized FVS implementation would not solve the separate Eq. 11.26 or Cao Case 2 source gaps.

## Decision

The literature turns this issue from “no known theoretical route” into **“known external theoretical routes exist, but compatibility with the teacher production state has not yet been derived and verified.”**

That is a meaningful reduction in uncertainty, but it is not yet enough evidence to modify the accepted production solver.
