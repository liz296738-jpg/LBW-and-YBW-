# P11.3J — Teacher single-injector domain mapping

## Why this stage exists

The Chapter 11 model contains both an injected-fuel source in the conservative equations and an algebraic downstream composition closure. Those are complementary pieces of the same model, not two independent ways of adding fuel. A domain whose inlet already contains the prescribed fuel and which then adds the same fuel again through `d(mdot_s)/dx` would double count mass and injected enthalpy.

P11.3J freezes a narrower finite-volume contract before any integrated solver is promoted.

## Frozen domain contract

For one prescribed injection station:

1. the injector is an **interior** finite-volume cell, so at least one physical cell exists upstream;
2. all upstream cells use `phi=0`, `eta=0` and therefore the exact air-only composition on the same H2/C2H4 teacher species basis;
3. the injector cell and all downstream cells use the already verified Chapter 11 spatial closure
   `mdot_f/mdot_air -> phi -> L_m -> eta_m -> eta -> Y_i`;
4. `Delta(mdot_f)/Delta x` is nonzero in exactly the injector cell and integrates to the prescribed total fuel mass flow;
5. injected axial velocity and injected total enthalpy are nonzero only where the conservative fuel source is applied.

The algebraic composition field changes the local thermodynamic closure `R(Y), cp(T,Y), gamma(T,Y), e(T,Y)` but is **not** an additional conservative source.

## Grid convention

The current compatibility solver uses one scalar `dx`, so the mapping accepts only a strictly increasing uniform cell-centre grid whose spacing agrees with that `dx`. The injection station is located at the centre of the selected injector cell. No sub-cell injector geometry is invented.

## Energy accounting

Injected stream energy enters Eq. (11.38) once through

`h_ts * d(mdot_s)/dx`,

with `h_ts = h_s(T_s) + u_sx^2/2` from the same absolute species-enthalpy database used by the variable-composition flow state. Chemical reaction energy remains represented through composition-dependent absolute species energy; no duplicate chemical `Qdot` is introduced.

## Remaining gate

This mapping is not yet a formal integrated teacher case. The next stage is a source-enabled variable-composition RHS/SSP-RK3 compatibility solver. It must recompute the state-dependent Eq. (11.38) friction contribution at every Runge-Kutta stage while keeping the prescribed operating-point mapping fixed. Final inlet static `p/T/u` and outlet first-order extrapolation semantics remain a later boundary-adapter gate.
