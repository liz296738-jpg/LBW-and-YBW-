# P11.3G — Prescribed-composition SSP-RK3 compatibility march

This stage time-advances the three quasi-one-dimensional conservative flow equations while a verified H2/C2H4 teacher composition field is held fixed throughout the run.

It is deliberately one step short of a reacting teacher case. The goal is to verify the numerical path with spatially varying `Y_i(x)` before allowing the empirical mixing/combustion closure to update composition dynamically.

## CFL control

At every accepted timestep,

\[
\Delta t = \mathrm{CFL}\,\frac{\Delta x}{\max_i(|u_i|+a_i)},
\qquad
 a_i=\sqrt{\gamma(T_i,Y_i)R(Y_i)T_i}.
\]

Each cell therefore contributes its own composition-dependent wave speed.

## Time integration

The existing project SSP-RK3 integrator is reused. At every RK stage, the same immutable composition field is passed to the P11.3F variable-composition quasi-1D Rusanov RHS.

This establishes a strict limiting test: if every cell has the same composition, CFL, one-step RK3, and the short transient must reduce to the previously accepted fixed-composition variable-thermo solver.

## What this stage does not claim

- no species conservation equations;
- no dynamic `phi`, `eta`, or `Y_i` update;
- no finite-rate chemistry;
- no fuel injection source;
- no wall friction or wall heat source;
- no independent reaction `Qdot` for the teacher chemical energy;
- no variable-composition Steger-Warming yet;
- transmissive boundaries remain verification-only.

The next stage is to define the **dynamic algebraic closure contract**. That contract must state how injected fuel and air mass flow produce `phi`, how distance from the injector and Eq. (11.19)/(11.20) produce `eta`, when the algebraic composition field is refreshed, and how conservative energy is kept consistent when composition changes. That energy remap must be explicit so the project does not silently create or remove chemical energy.
