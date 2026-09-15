# P11.3L — Teacher variable-composition boundary adapter

The teacher-reference review identifies prescribed inlet static `p/T/u` and first-order outlet extrapolation as the target case semantics. P11.3L implements those semantics for the already verified source-enabled H2/C2H4 compatibility path.

## Inlet

The first physical cells remain air-only because P11.3J requires an interior injector. The prescribed inlet state is reconstructed from

`rho_in = p_in / [R(Y_air) T_in]`

and the source-backed variable-thermochemistry state conversion. The current adapter requires `u_in > 0` and `Mach_in > 1`; this matches the rightward supersonic scramjet-inlet path and avoids inventing a subsonic static-inlet characteristic treatment not frozen by the teacher source.

For that supersonic inlet, the left boundary flux is the physical Euler flux of the prescribed inlet state and is therefore independent of the first interior state.

## Outlet

The right boundary uses the physical Euler flux of the last interior state, corresponding to the current first-order/zero-gradient extrapolation compatibility treatment.

## Interior and sources

Internal interfaces still use the verified variable-composition Rusanov flux. The Eq. (11.38) source vector is recomputed at every SSP-RK3 stage exactly as in P11.3K. Fuel mass/momentum/enthalpy enters once at the interior injector cell; wall friction is state-dependent; any dimensional `d(delta q)/dx` remains an explicit caller input.

## Remaining numerical gate

The teacher chapter specifies Steger–Warming flux-vector splitting and a near-sonic eigenvalue smoothing relation. The project must freeze that exact source rule before replacing Rusanov in the variable-property path. In particular, no smoothing epsilon will be guessed simply to mark the item complete.
