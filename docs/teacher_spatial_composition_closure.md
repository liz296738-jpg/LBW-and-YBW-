# P11.3H — Teacher spatial algebraic composition closure

## Source alignment

A re-read of the teacher Chapter 11 equations clarifies an important implementation detail: the source model advances the three quasi-one-dimensional flow equations, while local mixture composition is closed **algebraically in space** from the prescribed fuel/air ratio and mixing/combustion efficiency. The transcribed section does not introduce separate species-transport PDEs or a time-evolution equation for `phi`, `eta`, or `Y_i`.

Therefore P11.3H replaces the earlier planning phrase “dynamic `phi/eta/Y_i` update” with a more source-faithful contract: construct the teacher composition field from the prescribed operating condition and geometry, then hold that field fixed during pseudo-time iteration of the steady three-equation flow problem unless later teacher evidence explicitly requires time-dependent composition evolution.

## Closure chain

For one prescribed injection station, the downstream fuel/air equivalence ratio is

\[
\phi = \frac{\dot m_f/\dot m_\infty}{f_{st}},
\]

from Eq. (11.23). The current H2/C2H4 thermochemical branch requires `phi <= 1` because the transcribed composition relations are the lean relations.

At every cell, Eq. (11.20) uses the local combustor height `b(x)`:

\[
L_m(x)=0.179 C_m e^{1.72\phi} b(x),\qquad \phi\le 1.
\]

The raw Eq. (11.19) mixing correlation is then evaluated from the nonnegative distance to the injector `x/L_m(x)` using the selected parallel, normal, or strut injection branch.

The raw correlation is preserved unchanged. The separately frozen project adapter maps it to physical combustion efficiency:

\[
\eta(x)=\min(\eta_{m,raw}(x),1).
\]

Residual fuel is

\[
\dot m_{fr}(x)=\dot m_{fi}[1-\eta(x)],
\]

and P11.3H verifies that Eq. (11.18) reconstructs the same `eta`.

Finally, Eqs. (11.27) or (11.29) build the H2 or C2H4 mass-fraction vector `Y_i(x)`, which feeds the already verified variable-composition thermochemistry and SSP-RK3 compatibility solver.

## Why fuel flow is scalar in this stage

The teacher governing source vector contains a spatial fuel-addition term `d(mdot_s)/dx`, but Eq. (11.19) also defines `x` relative to an injection point. Turning an arbitrary cell-centered distributed source into a cumulative injected-fuel flow and an effective mixing distance requires a discretization convention that is not explicitly frozen in the photographed source.

P11.3H therefore does **not** invent one. It models one prescribed injector with scalar downstream fuel flow and incoming-air flow. Distributed-injection coupling remains a separate adapter task.

## Scientific boundary

- H2 and C2H4 only for the current thermochemical implementation;
- lean branch only (`phi <= 1`);
- C10H22 stoichiometry is transcribed but its thermochemistry remains blocked;
- no species-transport PDE;
- no finite-rate chemistry;
- no independent teacher reaction `Qdot`;
- no wall heat conversion is invented;
- fuel mass/momentum/enthalpy source coupling is still separate.

This stage can already generate a source-backed spatial `Y_i(x)` field and pass it directly to the accepted prescribed-composition SSP-RK3 compatibility solver. The next integration step is the teacher fuel source plus the already verified teacher friction adapter.
