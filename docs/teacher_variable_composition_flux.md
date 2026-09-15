# P11.3F — Variable-composition Euler/Rusanov compatibility

This stage extends the verified teacher H2/C2H4 per-cell composition field to the three-equation Euler finite-volume operator without adding a species-transport PDE system.

## Scope

Each cell carries a source-backed algebraic mass-fraction vector `Y_i(x_j)`. At an interface, the left and right conservative states are recovered with **their own** compositions before the numerical flux is formed.

For each side,

\[
a=\sqrt{\gamma(T,Y)R(Y)T},
\]

and the Rusanov signal speed is

\[
\alpha=\max(|u_L|+a_L,\ |u_R|+a_R).
\]

The flux remains the standard three-component Euler/Rusanov flow flux. No species flux vector is introduced in this compatibility stage.

## Reduction requirement

If every cell uses the same composition, the new path must reduce to the already verified fixed-composition variable-thermo operators. Tests cover the pair flux, all internal interfaces, and the complete quasi-one-dimensional RHS.

## Quasi-one-dimensional geometry

The area-weighted flux operator is reused unchanged. The geometric momentum source is evaluated with the pressure recovered from each cell's local composition:

\[
S_{A,m}=p_i\,\frac{\Delta A_i}{A_i\Delta x}.
\]

## Scientific boundary

This is **not yet a reacting time-marching solver**. Composition is prescribed/algebraically supplied during the operator evaluation. In particular:

- no species-transport conservation equations are introduced;
- no finite-rate kinetics are introduced;
- no independent chemical `Qdot` is applied for the teacher reaction energy;
- no claim is made that Rusanov diffusion of the three flow variables constitutes a conservative species-mixing model;
- transmissive boundaries remain verification-only;
- variable-composition Steger-Warming remains separate.

The next stage is a prescribed-composition SSP-RK3/CFL compatibility march. Only after that limiting behavior is verified should `eta(x)`, `phi(x)`, fuel injection, wall friction, and wall heat terms be coupled into one teacher-reference case.
