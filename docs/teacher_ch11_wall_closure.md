# Teacher Chapter 11 wall closure

## Source scope

This P11.3D stage isolates the teacher wall correlations before solver coupling.

Primary source locators:

- p.257 Eq. (11.25): wall-friction coefficient `f(x)`;
- p.257 Eq. (11.26): wall heat coefficient `q(x)`;
- p.255 Eq. (11.16) and p.260 Eq. (11.38): placement of wall friction and wall heat in the quasi-one-dimensional source vector.

The local source photographs are `IMG_2463.HEIC.jpg`, `IMG_2465.HEIC.JPG`, and `IMG_2468.HEIC.JPG` from the teacher project material.

## Eq. (11.25): wall friction

With `z = phi*eta`, the teacher correlation is

`f = 0.0018 + 0.001958 z + 0.00927 z^2 - 0.0088525 z^3`.

The code returns this polynomial exactly. It is not clipped or forced positive. The polynomial can become negative if extrapolated far outside the practical regime, which is treated as a diagnostic that the empirical correlation has been pushed beyond a physically usable range.

## Eq. (11.26): wall heat coefficient

With the same `z = phi*eta`, the teacher correlation is

`q = 0.0009 + 0.001125 z + 0.00594 z^2 - 0.00469 z^3`.

The implementation deliberately returns only this raw coefficient. It does **not** reinterpret it as the generic solver input `wall_heat_flux [W/m^2]` because the photographed pages do not yet provide a source-traceable dimensional conversion from Eq. (11.26) to the Eq. (11.38) energy source `rho*u*d(delta_q)/dx`.

## Friction convention mapping to the existing solver

Teacher Eq. (11.38), after division by cross-sectional area, contains the momentum contribution

`S_m = -0.5 rho u^2 (4 f / D_e)`.

The project's existing generic wall source uses a Darcy factor:

`S_m = -0.5 f_D rho u |u| / D_h`.

For the teacher model's forward-flow convention (`u >= 0`) and the same hydraulic diameter (`D_h = D_e`), these are exactly equivalent when

`f_D = 4 f`.

This mapping is now explicit and unit-tested. It is not a guessed convention: it follows directly from the teacher source vector and the already implemented generic Darcy source.

## Heat-transfer coupling remains gated

The friction side is therefore ready for an explicit teacher adapter. The heat side is not. Before Eq. (11.26) is connected to the generic `wall_heat_flux` source, the project still needs a source-backed relation defining how the empirical `q(x)` coefficient determines `delta_q` or `d(delta_q)/dx` in Eq. (11.38).

Until that relation is frozen, no dimensional wall-heat flux is invented.

## Chemical-energy separation

Wall heat loss is external heat transfer. Chemical reaction energy is already represented through composition-dependent absolute species enthalpy in the teacher thermochemistry formulation. These two effects must remain separate, and the independent prescribed combustion `Qdot'(x)` surrogate must not be used to double-count the same reaction energy once variable composition is coupled.
