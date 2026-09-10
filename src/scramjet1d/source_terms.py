"""Geometry, prescribed wall, fuel-injection, and local heat-release sources."""

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import GasProperties
from .geometry import AreaProfile, area_change_per_cell
from .state import conservative_to_primitive
from .validation import require_positive_scalar


def geometric_area_source(
    U: ArrayLike, geometry: AreaProfile, dx: object, gas: GasProperties
) -> NDArray[np.float64]:
    """Return normalized geometric RHS source for U[..., N, 3] in SI units.

    The mass and energy components are zero.  The momentum component is
    ``p_i * (A_right - A_left) / (A_i * dx)`` [N/m^3], already normalized for
    direct addition to ``dU/dt``. Wall, prescribed fuel-injection, and local
    prescribed combustion heat-release sources are implemented independently.
    """
    if not isinstance(geometry, AreaProfile):
        raise TypeError("geometry must be an AreaProfile")

    states = np.asarray(U, dtype=float)
    if states.ndim < 2 or states.shape[-1] != 3:
        raise ValueError("U must include a cell dimension and final state dimension of length 3")
    if states.shape[-2] != geometry.num_cells:
        raise ValueError("U cell count must match geometry.num_cells")
    spacing = require_positive_scalar("dx", dx)
    primitive = conservative_to_primitive(states, gas)

    source = np.zeros_like(states, dtype=float)
    source[..., 1] = (
        primitive.p
        * area_change_per_cell(geometry)
        / geometry.cell_area
        / spacing
    )
    return source


def wall_friction_source(
    U: ArrayLike,
    hydraulic_diameter: ArrayLike,
    darcy_friction_factor: ArrayLike,
    gas: GasProperties,
) -> NDArray[np.float64]:
    """Return the prescribed-Darcy wall-friction source in SI units.

    ``hydraulic_diameter`` [m] and the Darcy friction factor may be scalar or
    broadcast to the state-cell shape.  This independent P6.1 contribution is
    ``[0, -f_D rho u |u| / (2 D_h), 0]`` [kg/(m^2 s^2)]. P6.3 composes this
    source with prescribed wall heat inside the quasi-1D solver.
    """
    states = np.asarray(U, dtype=float)
    if states.ndim < 1 or states.shape[-1] != 3:
        raise ValueError("U must have shape (..., 3)")
    primitive = conservative_to_primitive(states, gas)
    target_shape = primitive.rho.shape

    diameter = np.asarray(hydraulic_diameter, dtype=float)
    friction = np.asarray(darcy_friction_factor, dtype=float)
    try:
        diameter = np.broadcast_to(diameter, target_shape)
        friction = np.broadcast_to(friction, target_shape)
    except ValueError as error:
        raise ValueError("hydraulic_diameter and darcy_friction_factor must broadcast to the state shape") from error
    if not np.all(np.isfinite(diameter) & (diameter > 0.0)):
        raise ValueError("hydraulic_diameter must be finite and strictly positive")
    if not np.all(np.isfinite(friction) & (friction >= 0.0)):
        raise ValueError("darcy_friction_factor must be finite and nonnegative")

    source = np.zeros_like(states, dtype=float)
    source[..., 1] = -0.5 * friction / diameter * primitive.rho * primitive.u * np.abs(primitive.u)
    return source


def wall_heat_transfer_source(
    U: ArrayLike,
    hydraulic_diameter: ArrayLike,
    wall_heat_flux: ArrayLike,
    gas: GasProperties,
) -> NDArray[np.float64]:
    """Return the prescribed wall-heat-flux source in SI units.

    ``wall_heat_flux`` [W/m^2] is positive into the gas and negative for gas
    cooling. ``hydraulic_diameter`` [m] and heat flux may be scalar or broadcast
    to the state-cell shape. This independent P6.2 contribution is
    ``[0, 0, 4 q''_w / D_h]`` [W/m^3]. P6.3 composes this source with prescribed
    wall friction inside the quasi-1D solver.
    """
    states = np.asarray(U, dtype=float)
    if states.ndim < 1 or states.shape[-1] != 3:
        raise ValueError("U must have shape (..., 3)")
    primitive = conservative_to_primitive(states, gas)
    target_shape = primitive.rho.shape

    diameter = np.asarray(hydraulic_diameter, dtype=float)
    heat_flux = np.asarray(wall_heat_flux, dtype=float)
    try:
        diameter = np.broadcast_to(diameter, target_shape)
        heat_flux = np.broadcast_to(heat_flux, target_shape)
    except ValueError as error:
        raise ValueError("hydraulic_diameter and wall_heat_flux must broadcast to the state shape") from error
    if not np.all(np.isfinite(diameter) & (diameter > 0.0)):
        raise ValueError("hydraulic_diameter must be finite and strictly positive")
    if not np.all(np.isfinite(heat_flux)):
        raise ValueError("wall_heat_flux must be finite")

    source = np.zeros_like(states, dtype=float)
    source[..., 2] = 4.0 * heat_flux / diameter
    return source


def combined_wall_source(
    U: ArrayLike,
    hydraulic_diameter: ArrayLike,
    darcy_friction_factor: ArrayLike,
    wall_heat_flux: ArrayLike,
    gas: GasProperties,
) -> NDArray[np.float64]:
    """Return the sum of prescribed friction and wall-heat source contributions."""
    friction_source = wall_friction_source(U, hydraulic_diameter, darcy_friction_factor, gas)
    heat_source = wall_heat_transfer_source(U, hydraulic_diameter, wall_heat_flux, gas)
    return friction_source + heat_source


def combustion_heat_release_source(
    U: ArrayLike,
    volumetric_heat_release_rate: ArrayLike,
    gas: GasProperties,
) -> NDArray[np.float64]:
    """Return a prescribed local combustion heat-release source in SI units.

    ``volumetric_heat_release_rate`` is an externally prescribed local
    chemical heat-release rate [W/m^3]. It may be scalar or broadcast to the
    state-cell shape ``U.shape[:-1]`` and must be finite and nonnegative:
    zero disables local heat release, while positive values add energy to the
    gas. The returned source has the same shape as ``U`` and maps exactly to
    ``[0, 0, qdot_comb]``. It adds no mass or axial momentum and is independent
    of thermodynamic state after that state has passed normal physical-state
    validation. This standalone P8.1 source is not solver-integrated and does
    not infer heat release from fuel injection, LHV, efficiency, species,
    mixing, ignition, or chemical kinetics.
    """
    states = np.asarray(U, dtype=float)
    if states.ndim < 1 or states.shape[-1] != 3:
        raise ValueError("U must have shape (..., 3)")
    primitive = conservative_to_primitive(states, gas)
    target_shape = primitive.rho.shape

    heat_release = np.asarray(volumetric_heat_release_rate, dtype=float)
    try:
        heat_release = np.broadcast_to(heat_release, target_shape)
    except ValueError as error:
        raise ValueError("volumetric_heat_release_rate must broadcast to the state shape") from error
    if not np.all(np.isfinite(heat_release) & (heat_release >= 0.0)):
        raise ValueError("volumetric_heat_release_rate must be finite and nonnegative")

    source = np.zeros_like(states, dtype=float)
    source[..., 2] = heat_release
    return source


def fuel_injection_source(
    U: ArrayLike,
    fuel_mass_source_rate: ArrayLike,
    fuel_axial_velocity: ArrayLike,
    fuel_specific_total_enthalpy: ArrayLike,
    gas: GasProperties,
) -> NDArray[np.float64]:
    """Return prescribed local fuel injection source ``[mass, momentum, energy]``.

    ``fuel_mass_source_rate`` is nonnegative and expressed in kg/(m^3 s).
    ``fuel_axial_velocity`` [m/s] and ``fuel_specific_total_enthalpy`` [J/kg]
    are finite signed prescribed values.  The mapping is
    ``[rho_dot_f, rho_dot_f*u_f,x, rho_dot_f*h_t,f]``.  The supplied total
    enthalpy already includes injected-stream kinetic energy; no extra
    velocity-squared term or combustion heat release is added.
    """
    states = np.asarray(U, dtype=float)
    if states.ndim < 1 or states.shape[-1] != 3:
        raise ValueError("U must have shape (..., 3)")
    primitive = conservative_to_primitive(states, gas)
    target_shape = primitive.rho.shape

    mass_rate = np.asarray(fuel_mass_source_rate, dtype=float)
    injection_velocity = np.asarray(fuel_axial_velocity, dtype=float)
    total_enthalpy = np.asarray(fuel_specific_total_enthalpy, dtype=float)
    try:
        mass_rate = np.broadcast_to(mass_rate, target_shape)
        injection_velocity = np.broadcast_to(injection_velocity, target_shape)
        total_enthalpy = np.broadcast_to(total_enthalpy, target_shape)
    except ValueError as error:
        raise ValueError("fuel injection inputs must broadcast to the state shape") from error
    if not np.all(np.isfinite(mass_rate) & (mass_rate >= 0.0)):
        raise ValueError("fuel_mass_source_rate must be finite and nonnegative")
    if not np.all(np.isfinite(injection_velocity)):
        raise ValueError("fuel_axial_velocity must be finite")
    if not np.all(np.isfinite(total_enthalpy)):
        raise ValueError("fuel_specific_total_enthalpy must be finite")

    source = np.zeros_like(states, dtype=float)
    source[..., 0] = mass_rate
    source[..., 1] = mass_rate * injection_velocity
    source[..., 2] = mass_rate * total_enthalpy
    return source


def fuel_mass_source_rate_from_axial_distribution(
    U: ArrayLike,
    geometry: AreaProfile,
    fuel_mass_flow_rate_per_length: ArrayLike,
    gas: GasProperties,
) -> NDArray[np.float64]:
    """Convert prescribed ``d(mdot_f)/dx`` [kg/(m s)] to kg/(m^3 s).

    The local quasi-1D mapping is ``rho_dot_f = (d(mdot_f)/dx) / A_cell``;
    it deliberately has no ``dx`` argument.  A distributed source requires a
    cell dimension, so local single-state input ``(3,)`` is not accepted.
    """
    if not isinstance(geometry, AreaProfile):
        raise TypeError("geometry must be an AreaProfile")
    states = np.asarray(U, dtype=float)
    if states.ndim < 2 or states.shape[-1] != 3:
        raise ValueError("U must have shape (..., N, 3) for axial distribution")
    if states.shape[-2] != geometry.num_cells:
        raise ValueError("U cell count must match geometry.num_cells")
    primitive = conservative_to_primitive(states, gas)
    target_shape = primitive.rho.shape
    distribution = np.asarray(fuel_mass_flow_rate_per_length, dtype=float)
    try:
        distribution = np.broadcast_to(distribution, target_shape)
    except ValueError as error:
        raise ValueError("fuel_mass_flow_rate_per_length must broadcast to the state cell shape") from error
    if not np.all(np.isfinite(distribution) & (distribution >= 0.0)):
        raise ValueError("fuel_mass_flow_rate_per_length must be finite and nonnegative")
    return distribution / geometry.cell_area


def distributed_fuel_injection_source(
    U: ArrayLike,
    geometry: AreaProfile,
    fuel_mass_flow_rate_per_length: ArrayLike,
    fuel_axial_velocity: ArrayLike,
    fuel_specific_total_enthalpy: ArrayLike,
    gas: GasProperties,
) -> NDArray[np.float64]:
    """Compose axial-distribution conversion with the P7.1 fuel source."""
    mass_source_rate = fuel_mass_source_rate_from_axial_distribution(
        U, geometry, fuel_mass_flow_rate_per_length, gas
    )
    return fuel_injection_source(
        U, mass_source_rate, fuel_axial_velocity, fuel_specific_total_enthalpy, gas
    )
