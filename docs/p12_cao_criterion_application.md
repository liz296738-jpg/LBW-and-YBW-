# P12 Cao Criterion Application on Project-Defined H2 Sweep

Status: **SOURCE CRITERION APPLIED / GRID-REFINED CANDIDATE REGION ACCEPTED / TRANSITION VALUE NOT CLAIMED**

This stage applies Cao Ruifeng's source-defined thermal-throat criterion to the accepted project-defined H2 response sweep and its warm-start continuation. The flow cases remain project-defined; only the criterion is source-defined.

## Source criterion

The teacher-provided doctoral dissertation defines the broad thermal-throat distinction by Eq. (3-2):

- scram side: `min(Ma(x)) > 1`;
- ram side: `min(Ma(x)) < 1`;
- exact transition boundary: thermal throat critical at `Ma = 1`.

The source does not provide a floating-point sonic tolerance. The project uses an explicit numerical tolerance only as a numerical sensitivity choice; it is not attributed to Cao.

## Accepted response sweep

From the frozen P12 response-sweep evidence:

- `phi=0.10`: converged and on the Cao scram side;
- `phi=0.20`: converged and on the Cao scram side;
- cold-start `phi=0.30`: triggers the existing forward-flow Eq.11.38 guard and receives **no physical mode label**.

## Accepted warm-start continuation

The initial 20-cell continuation with Eq.11.46 tolerance `1e-4` reached a near-sonic `phi=0.26` state. That result was treated only as a candidate region and explicitly required grid refinement with a tighter steady tolerance before any stronger claim.

## Accepted 20/40/80 grid-refined continuation

The dedicated grid study repeats the same continuation sequence `phi=0.20 -> 0.22 -> 0.24 -> 0.26` on 20, 40 and 80 cells using the teacher Eq.11.46 maximum relative-density-change metric with a project-selected numerical tolerance of `2e-5`.

All three grids complete the dedicated CI workflow. Every accepted converged point satisfies the project-selected `2e-5` tolerance applied to the Eq.11.46 metric and the project-defined 0.5% normalized mass-inventory QA gate. Neither numeric threshold is attributed to Cao, the teacher source, an experiment, or a universal CFD standard. Momentum and energy inventory rates remain reported diagnostics without invented hard thresholds.

At `phi=0.24`, all three grids are admissible and remain on the Cao Eq. (3-2) scram side. The minimum Mach values are:

- 20 cells: `1.07661298596`;
- 40 cells: `1.04462708512`;
- 80 cells: `1.01266839154`.

The minimum Mach therefore moves toward unity as the grid is refined, but this is only a grid trend; no GCI/asymptotic-order claim is made.

At `phi=0.26`, the unchanged forward-flow guard triggers on **all three grids** before an admissible converged state is accepted. Those points are classified only as **solver/model-domain inadmissible**. They are not labelled unstart, ramjet, scramjet, dual-mode, LBW or YBW.

Machine-readable record:

`cases/studies/data/p12_thermal_throat_grid_sensitivity_acceptance.json`

## Scientific conclusion and next safe step

The grid-refined evidence does **not** bracket a transition equivalence ratio: `phi=0.24` is still on the source-defined scram side at 80 cells, while `phi=0.26` is outside the currently admissible forward-flow solver/model domain on every grid.

Therefore no transition `phi` is quoted. The next safe work is to preserve this evidence, keep Cao Case 2 reproduction independently source-blocked, and improve deliverability/reproducibility of the accepted project-defined response package. Any attempt to cross the `phi=0.24` to `0.26` gap must retain the forward-flow guard and may only classify points that are both converged and solver-admissible.
