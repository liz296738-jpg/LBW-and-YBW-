# P12 Cao Criterion Application on Project-Defined H2 Sweep

Status: **SOURCE CRITERION APPLIED / TRANSITION NOT YET BRACKETED**

This stage applies Cao Ruifeng's source-defined thermal-throat criterion to the already accepted project-defined H2 response sweep. The flow cases remain project-defined; only the criterion is source-defined.

## Source criterion

The teacher-provided doctoral dissertation defines the broad thermal-throat distinction by Eq. (3-2):

- scram side: `min(Ma(x)) > 1`;
- ram side: `min(Ma(x)) < 1`;
- exact transition boundary: thermal throat critical at `Ma = 1`.

The source does not provide a floating-point sonic tolerance. The application therefore checks the frozen minimum Mach values over the explicit project numerical sensitivity set `1e-6, 1e-4, 1e-3, 1e-2`.

## Accepted sweep interpretation

From the frozen P12 response-sweep evidence:

- `phi=0.10`: converged, `min(Ma)=1.694412...`; robustly on the Cao scram side for every tested numerical tolerance;
- `phi=0.20`: converged, `min(Ma)=1.278991...`; robustly on the Cao scram side for every tested numerical tolerance;
- `phi=0.30`: the existing forward-flow Eq.11.38 guard is triggered during the cold-start pseudo-time path. It receives **no physical mode label**.

Therefore the currently accepted sweep does not bracket the `Ma=1` transition boundary. It establishes only that the two admissible converged project-defined points are on the source-defined scram side.

## Next numerical step

Do not weaken or remove the forward-flow guard. The next safe numerical experiment is a continuation/warm-start sweep from the accepted `phi=0.20` solution toward higher equivalence ratio, using small increments and a composition-consistent remap of the previous converged primitive state as the next initial guess.

That continuation is a numerical strategy, not a new physical model. If a converged admissible point reaches the source-defined sonic band, it may be used to bracket the project-defined transition application. If the guard still triggers first, record the current solver-domain limitation rather than inventing a transition.
