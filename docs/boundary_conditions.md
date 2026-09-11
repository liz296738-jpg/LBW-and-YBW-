# P9.1 Physical Boundary Foundation

`BoundaryConditions()` retains transmissive inlet and outlet behavior for
verification and backward compatibility. It is not a final physical scramjet
inlet/outlet model.

P9.1 additionally supports a left fixed positive supersonic inflow and a right
supersonic outflow. A fixed inflow is specified only by the independent
primitive state `PrimitiveBoundaryState(rho, u, p)`. It requires `rho > 0`,
`p > 0`, `u > 0`, and `Mach > 1`.

At the left positive supersonic inflow, the characteristic speeds `u-a`, `u`,
and `u+a` are all positive, so all information enters the domain. The
boundary-face flux is deliberately `F_in = F(U_in)` and therefore does not
depend on the first interior cell or on the selected numerical flux scheme.

At the right positive supersonic outflow, all three characteristics leave the
domain. No exterior thermodynamic state is supplied; the boundary-face flux is
`F_out = F(U_N)`, where `U_N` is the final interior cell. Both physical face
fluxes retain the existing quasi-1D face-area weighting. The geometric area
source, Rusanov/Steger-Warming formulas, SSP-RK3, and CFL rule are unchanged.

Subsonic inlet/outlet, outlet pressure, back pressure, characteristic
relaxation, reservoir, choked, and reverse-flow boundary conditions are not
implemented in P9.1.

## P9.2 Right Subsonic Static-Pressure Outlet

`outlet="subsonic-pressure"` requires one finite, positive
`outlet_static_pressure`. For rightward subsonic interior flow, the outlet
reconstruction preserves `K_i = p_i/rho_i^gamma` and
`J+_i = u_i + 2 a_i/(gamma-1)`: `p_b=p_out`,
`rho_b=(p_out/K_i)^(1/gamma)`, `a_b=sqrt(gamma p_out/rho_b)`, and
`u_b=J+_i-2a_b/(gamma-1)`. The boundary numerical flux is evaluated between
the final interior state and this reconstructed state.

The model accepts only `u_i>0`, `0<M_i<1`, and a reconstructed state with
`u_b>0`, `M_b<1`; mismatches raise `ValueError` rather than switching boundary
models. This is a controlled characteristic static-pressure outlet, not a
fully non-reflecting, NSCBC, reservoir, or reverse-flow treatment.
