# P12 Cao Source-Defined Mode Criteria

Status: **SOURCE CRITERIA FROZEN / PARTIAL SOLVER INTEGRATION**

Primary source: 曹瑞峰, 《超燃冲压发动机燃烧模态转换及其控制方法研究》, doctoral dissertation, 2016, teacher-provided reference.

## Frozen source locations

The mode criteria used here are taken from:

- Section 3.2 and Table 3-1, combustion-mode definition/classification;
- Section 3.3.1.2, Eq. (3-2), thermal-throat critical limit;
- Section 4.2.1, definition of the combustion-mode transition boundary.

The corresponding PDF evidence is on PDF pages 70, 72 and 102 in the teacher-provided copy.

## Two-mode thermal-throat criterion

For the later dissertation analysis, the fundamental distinction between the two broad modes is whether the combustor thermal throat has reached its critical sonic condition.

Eq. (3-2) states:

- scram side: `min(Ma(x)) > 1`;
- ram side: `min(Ma(x)) < 1`.

Section 4.2.1 defines the transition boundary at a fixed incoming/flight condition as the fuel equivalence ratio for which the thermal throat is just critical (`Ma=1`). The same section describes that value as the maximum equivalence ratio for operation on the scram side, equivalently the minimum equivalence ratio for the ram side.

The source gives an exact sonic boundary, not a floating-point tolerance. Therefore `classify_thermal_throat` requires the caller to supply a numerical `sonic_tolerance` explicitly. That tolerance is a project numerical choice and must not be presented as a source physical threshold.

## Detailed Table 3-1 criterion

Table 3-1 further distinguishes:

- no-shock scram: `Ma_s > 0.762 Ma_2`;
- oblique-shock scram: `Ma_2 > Ma_3m` and `Ma_s < 0.762 Ma_2`;
- ram: `Ma_2min < Ma_2 < Ma_3m`.

The table couples these conditions to shock-train, separation and thermal-choking states. The current accepted project-defined combustor solver does **not** yet provide all source-compatible isolator quantities (`Ma_2`, `Ma_s`, `Ma_3m`, `Ma_2min`) or the required shock-train geometry/model. Therefore the detailed criterion is implemented as a source-faithful utility but is not yet attached to the integrated production case.

## Claim boundary

This source recovery changes the previous P12 evidence status: a defensible **two-mode thermal-throat criterion now exists**. It does not make the project-defined H2 baseline a Cao Case 2 reproduction, and it does not turn solver failure or the forward-flow guard into a physical mode label.

A project-defined converged profile may be evaluated against the source-defined thermal-throat criterion, provided the report clearly distinguishes:

1. source-defined criterion;
2. project-defined geometry/operating point;
3. project-selected numerical sonic tolerance;
4. solver admissibility/convergence status.

Formal Cao Case 2 reproduction remains blocked by the separate missing `A(x)`, prescribed `Yi(x)`, and original source-spatial/fuel-addition convention.
