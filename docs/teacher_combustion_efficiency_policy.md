# Teacher combustion-efficiency adapter policy

## Why an adapter is needed

The teacher source defines combustion efficiency in Eq. (11.18) from injected and residual fuel mass and prints it as a percentage. In fractional CFD form this is

`eta = (m_fi - m_fr) / m_fi`,

so the physical range is `0 <= eta <= 1`.

The same Chapter 11 section then approximates combustion efficiency by mixing efficiency and supplies Eq. (11.19) empirical mixing correlations. Those correlations are useful as written and therefore remain available through `mixing_efficiency_raw(...)` without clipping. However, the normal-injection correlation can be slightly above one near `x/L_m = 1`, and the parallel/strut expressions can also exceed the complete-mixing limit if evaluated beyond their intended normalized range.

## Frozen project policy

When the raw Eq. (11.19) value is used as the teacher combustion-efficiency surrogate, the project now applies the explicit adapter

`eta = min(eta_m_raw, 1.0)`.

This is **not** presented as a new textbook equation and does not alter Eq. (11.19). It is a separate project modeling policy justified by three source-consistent facts:

1. Eq. (11.18) defines a physical burned-fuel fraction and therefore cannot exceed one;
2. the teacher text approximates combustion efficiency by mixing efficiency;
3. Eq. (11.20) defines `L_m` as the length required for complete mixing, so values beyond complete mixing should not imply more than 100% reacted fuel.

The implementation is isolated in `src/scramjet1d/teacher_efficiency.py`. Higher-level code must call the adapter explicitly; raw mixing values remain inspectable for diagnostics and provenance.

## Eq. (11.18) computational convention

The source percentage form

`eta[%] = (m_fi - m_fr) / m_fi * 100%`

is represented internally as the dimensionless fraction

`eta = (m_fi - m_fr) / m_fi`.

The adapter rejects non-finite values, non-positive injected fuel flow, negative residual fuel, or residual fuel greater than injected fuel. No silent correction is applied.

## Remaining gate

Freezing this efficiency adapter removes one ambiguity but does **not** yet authorize direct solver replacement. The next stage is a per-cell H2/C2H4 composition-field compatibility layer. It must independently verify that each teacher-derived composition is nonnegative, sums to one, stays within the source-backed species set, and can round-trip through the existing variable-thermochemistry state conversion before any variable-composition numerical flux or SSP-RK3 integration is added.

Chemical reaction energy must continue to be represented through composition-dependent absolute species enthalpy in that path; the independent prescribed `Qdot'(x)` surrogate must remain off for the same reaction energy.
