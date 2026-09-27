# Peer-Reviewed Cross-Validation for the Quasi-1D Scramjet Model

## Purpose

This record provides **external peer-reviewed corroboration of the model family and claim boundaries** used by this repository. It is deliberately subordinate to the teacher-provided Chapter 11 material and the Cao Ruifeng references.

These papers may support statements such as:

- quasi-one-dimensional scramjet/dual-mode combustor models are established reduced-order engineering tools;
- area change, wall friction, fuel/mass injection, mixing, heat transfer, and chemistry are commonly represented in such models;
- reduced-order scramjet models should be checked against experiment and/or higher-fidelity CFD;
- broad dual-mode classification requires isolator/shock-train physics that is not contained in a combustor-only Mach trace.

They **must not** be used to:

- replace teacher Eqs. 11.18--11.46 with a different public model;
- invent the missing dimensional adapter for teacher Eq. 11.26;
- invent a variable-thermochemistry Steger--Warming correction or Eq. 11.44 epsilon;
- infer Cao Case 2 geometry, prescribed species profiles, or injection/source placement;
- tune project parameters merely to reproduce a literature curve.

## Literature

### 1. Birzer & Doolan (2009)

Cristian Birzer and Con J. Doolan, “Quasi-One-Dimensional Model of Hydrogen-Fueled Scramjet Combustors,” *Journal of Propulsion and Power*, 25(6), 1220--1225, 2009. DOI: https://doi.org/10.2514/1.43716

The paper develops a computationally efficient quasi-one-dimensional hydrogen-fueled scramjet model. Its model family includes skin friction and wall heat transfer and assumes mixing-limited combustion in the reduced-order formulation. Validation is reported against three different experimental configurations, including HyShot II.

**Permitted use here:** external evidence that a mixing-limited quasi-1D hydrogen-scramjet model with friction/heat-transfer closures is a legitimate reduced-order approach and should be validated against experiment.

**Not permitted:** treating the paper's closures, geometry, coefficients, or validation cases as the teacher model.

### 2. Tian et al. (2014)

L. Tian, L.-H. Chen, Q. Chen, F. Li, and X. Chang, “Quasi-One-Dimensional Multimodes Analysis for Dual-Mode Scramjet,” *Journal of Propulsion and Power*, 30(6), 1559--1567, 2014. DOI: https://doi.org/10.2514/1.B35177

The model includes combustor effects from area change, friction, mass injection, and heat release, while a separate precombustion-shock-train/isolator treatment is used to analyze multiple dual-mode states. Pressure predictions are compared with experimental data.

**Permitted use here:** corroboration that broad dual-mode classification requires more than a combustor-only local Mach observation; shock-train/isolator variables and validation evidence are part of a defensible multimode model.

**Not permitted:** importing the paper's shock model, transition thresholds, or geometry into the present teacher path without a separate, explicit model-extension decision.

### 3. Zhang et al. (2016)

D. Zhang, Y. Feng, S.-L. Zhang, J. Qin, K.-L. Cheng, W. Bao, and D. Yu, “Quasi-One-Dimensional Model of Scramjet Combustor Coupled with Regenerative Cooling,” *Journal of Propulsion and Power*, 32(3), 687--697, 2016. DOI: https://doi.org/10.2514/1.B35887

This quasi-one-dimensional reacting-flow model includes wall heat transfer, sonic fuel injection, mixing efficiency, finite-rate chemistry, and a thermally coupled regenerative-cooling model.

**Permitted use here:** external evidence that wall heat transfer, fuel injection, and mixing/chemistry are recognized first-order physics for reduced-order scramjet performance models.

**Not permitted:** using this regenerative-cooling formulation to fill the missing teacher Eq. 11.26 dimensional mapping.

### 4. Torrez et al. (2011)

S. M. Torrez, J. F. Driscoll, M. Ihme, and M. A. Fotia, “Reduced-Order Modeling of Turbulent Reacting Flows with Application to Ramjets and Scramjets,” *Journal of Propulsion and Power*, 27(2), 371--382, 2011. DOI: https://doi.org/10.2514/1.50272

The work constructs a reduced-order mixing/combustion model and integrates cross-sectional reaction information into a one-dimensional conservation framework. It compares the reduced-order approach with CFD solutions and experimental data.

**Permitted use here:** corroboration that low-order scramjet models are useful for design/control studies but require comparison against higher-fidelity computation and experiment.

**Not permitted:** treating agreement of model architecture as validation of this repository's specific teacher coefficients or project-defined operating point.

## Consequences for this repository

The literature strengthens the following claims without changing any governing equation:

1. The current quasi-1D project architecture is a scientifically recognizable reduced-order modeling approach.
2. Area change, friction, mass/fuel injection, heat transfer, mixing, and chemistry are all physically relevant effects in peer-reviewed scramjet reduced-order models.
3. The repository's refusal to label a forward-flow guard or a single Mach observation as a full dual-mode/unstart event is conservative and consistent with the need for isolator/shock-train treatment in multimode studies.
4. The current project-defined H2 evidence is **verification / reduced-order application evidence**, not a substitute for experimental validation of the exact teacher/Cao case.
5. Missing teacher-specific source information remains a blocker even when an alternative closure exists in public literature.

## Evidence provenance

Paper discovery was performed with a peer-reviewed literature index (Consensus). DOI/title metadata were cross-checked against publisher/institutional records where available. This document records the literature role; it does not alter any accepted CFD output.
