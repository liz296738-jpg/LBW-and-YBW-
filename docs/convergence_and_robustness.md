# P9.4 Steady convergence and diagnostics

`solve_quasi_1d_steady` is a pseudo-time wrapper around the existing complete
quasi-1D RHS: geometry, physical boundaries, wall transfer, fuel injection,
combustion, selected flux, CFL rule, and SSP-RK3 are unchanged.

It fixes reference scales from `U0` once: `L_ref=N dx`,
`V_ref=max(|u|+a)`, `t_ref=L_ref/V_ref`, and
`U_ref=[max(rho), max(rho)V_ref, max(abs(rho E))]`.  The reported
dimensionless semi-discrete residual is

`max_j [ t_ref / U_ref,j * max_i abs(R_i,j) ]`.

`NumericalConfig.tolerance` is the steady residual threshold.  The legacy
transient solver does not use it for early stopping.  Histories include the
initial residual at time zero and each accepted full SSP-RK3 step.

Termination is `converged`, `max-time`, or `max-steps`; the two caps are normal
diagnostic outcomes, not exceptions.  A runtime physical or numerical failure
is reported as a chained `RuntimeError` containing the step, pseudo-time, and
operation context.  A small residual diagnoses semi-discrete convergence; it
does not independently validate the physical model or its assumptions.
