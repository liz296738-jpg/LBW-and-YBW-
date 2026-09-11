"""Euler and quasi-one-dimensional solvers with optional prescribed sources."""

from typing import NamedTuple

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .boundary import BoundaryConditions, boundary_interface_fluxes, transmissive_ghost_cells, validate_boundary_conditions
from .config import GasProperties, NumericalConfig
from .gas import speed_of_sound
from .geometry import AreaProfile
from .spatial import finite_volume_residual, internal_rusanov_fluxes, internal_numerical_fluxes, quasi_1d_residual
from .source_terms import (
    combined_wall_source,
    distributed_combustion_heat_release_source,
    distributed_fuel_injection_source,
    heat_release_rate_per_length_from_burned_fuel,
)
from .state import conservative_to_primitive
from .time_integration import ssp_rk3_step


class SolverResult(NamedTuple):
    """Final conservative state, final time [s], and completed step count."""

    U: NDArray[np.float64]
    time: float
    steps: int


def _positive_scalar(name: str, value: object) -> float:
    """Return a finite strictly positive scalar."""
    scalar = np.asarray(value, dtype=float)
    if scalar.ndim != 0 or not np.isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"{name} must be a finite and strictly positive scalar")
    return float(scalar)


def _wall_physics_enabled(
    states: NDArray[np.float64],
    hydraulic_diameter: object,
    darcy_friction_factor: object,
    wall_heat_flux: object,
) -> bool:
    """Validate wall-source configuration and return whether either source is active."""
    target_shape = states.shape[:-1]
    friction = np.asarray(darcy_friction_factor, dtype=float)
    heat_flux = np.asarray(wall_heat_flux, dtype=float)
    try:
        friction = np.broadcast_to(friction, target_shape)
        heat_flux = np.broadcast_to(heat_flux, target_shape)
    except ValueError as error:
        raise ValueError("darcy_friction_factor and wall_heat_flux must broadcast to the state shape") from error
    if not np.all(np.isfinite(friction) & (friction >= 0.0)):
        raise ValueError("darcy_friction_factor must be finite and nonnegative")
    if not np.all(np.isfinite(heat_flux)):
        raise ValueError("wall_heat_flux must be finite")

    active = bool(np.any(friction != 0.0) or np.any(heat_flux != 0.0))
    if hydraulic_diameter is None:
        if active:
            raise ValueError("hydraulic_diameter is required when wall friction or wall heat transfer is enabled")
        return False

    diameter = np.asarray(hydraulic_diameter, dtype=float)
    try:
        diameter = np.broadcast_to(diameter, target_shape)
    except ValueError as error:
        raise ValueError("hydraulic_diameter must broadcast to the state shape") from error
    if not np.all(np.isfinite(diameter) & (diameter > 0.0)):
        raise ValueError("hydraulic_diameter must be finite and strictly positive")
    return active


def _fuel_injection_enabled(states: NDArray[np.float64], mass_flow: object, velocity: object, enthalpy: object) -> bool:
    """Validate fuel inputs and return whether the prescribed distribution is active."""
    target_shape = states.shape[:-1]
    values = [np.asarray(value, dtype=float) for value in (mass_flow, velocity, enthalpy)]
    try:
        distribution, injection_velocity, total_enthalpy = [np.broadcast_to(value, target_shape) for value in values]
    except ValueError as error:
        raise ValueError("fuel inputs must broadcast to the state shape") from error
    if not np.all(np.isfinite(distribution) & (distribution >= 0.0)):
        raise ValueError("fuel_mass_flow_rate_per_length must be finite and nonnegative")
    if not np.all(np.isfinite(injection_velocity)) or not np.all(np.isfinite(total_enthalpy)):
        raise ValueError("fuel axial velocity and total enthalpy must be finite")
    return bool(np.any(distribution != 0.0))


def _combustion_enabled(
    states: NDArray[np.float64],
    fuel_burn_rate_per_length: object,
    fuel_lower_heating_value: object,
) -> bool:
    """Validate P8 inputs and return whether prescribed combustion is active."""
    target_shape = states.shape[:-1]
    burn_rate = np.asarray(fuel_burn_rate_per_length, dtype=float)
    try:
        burn_rate = np.broadcast_to(burn_rate, target_shape)
    except ValueError as error:
        raise ValueError("fuel_burn_rate_per_length must broadcast to the state shape") from error
    if not np.all(np.isfinite(burn_rate) & (burn_rate >= 0.0)):
        raise ValueError("fuel_burn_rate_per_length must be finite and nonnegative")
    if fuel_lower_heating_value is None:
        if np.any(burn_rate > 0.0):
            raise ValueError("fuel_lower_heating_value is required when combustion is active")
        return False

    line_heat_release = heat_release_rate_per_length_from_burned_fuel(
        burn_rate, fuel_lower_heating_value
    )
    try:
        np.broadcast_to(line_heat_release, target_shape)
    except ValueError as error:
        raise ValueError(
            "fuel_burn_rate_per_length and fuel_lower_heating_value must broadcast to the state shape"
        ) from error
    return bool(np.any(burn_rate > 0.0))


def cfl_timestep(U: ArrayLike, dx: object, gas: GasProperties, numerical: NumericalConfig) -> float:
    """Return CFL*dx/max(|u|+a) [s] for valid conservative states on a uniform grid."""
    spacing = _positive_scalar("dx", dx)
    primitive = conservative_to_primitive(U, gas)
    maximum_speed = np.max(np.abs(primitive.u) + speed_of_sound(primitive.T, gas))
    if not np.isfinite(maximum_speed) or maximum_speed <= 0.0:
        raise ValueError("maximum wave speed must be finite and strictly positive")
    return float(numerical.cfl * spacing / maximum_speed)


def euler_rhs_transmissive(U: ArrayLike, dx: object, gas: GasProperties) -> NDArray[np.float64]:
    """Return the complete source-free Euler RHS with transmissive edge states."""
    spacing = _positive_scalar("dx", dx)
    ghosted = transmissive_ghost_cells(U)
    interface_fluxes = internal_rusanov_fluxes(ghosted, gas)
    return finite_volume_residual(interface_fluxes, spacing)


def quasi_1d_rhs(
    U: ArrayLike,
    geometry: AreaProfile,
    dx: object,
    gas: GasProperties,
    *,
    flux_scheme: object = "rusanov",
    boundary_conditions: BoundaryConditions | None = None,
    hydraulic_diameter: object = None,
    darcy_friction_factor: object = 0.0,
    wall_heat_flux: object = 0.0,
    fuel_mass_flow_rate_per_length: object = 0.0,
    fuel_axial_velocity: object = 0.0,
    fuel_specific_total_enthalpy: object = 0.0,
    fuel_burn_rate_per_length: ArrayLike = 0.0,
    fuel_lower_heating_value: ArrayLike | None = None,
) -> NDArray[np.float64]:
    """Return quasi-1D RHS with selected P9.1 boundaries and optional sources.

    ``fuel_burn_rate_per_length`` [kg/(m s)] is a prescribed reacted-fuel
    distribution independent of P7's ``fuel_mass_flow_rate_per_length``.
    ``fuel_lower_heating_value`` [J/kg] is required when any burn rate is
    positive; ``None`` is valid only when all burn rates are zero. The P8.2
    source is re-evaluated from each supplied state and adds only energy.
    """
    if not isinstance(geometry, AreaProfile):
        raise TypeError("geometry must be an AreaProfile")
    states = np.asarray(U, dtype=float)
    if states.ndim < 2 or states.shape[-1] != 3:
        raise ValueError("U must include a cell dimension and final state dimension of length 3")
    if states.shape[-2] != geometry.num_cells:
        raise ValueError("U cell count must match geometry.num_cells")

    spacing = _positive_scalar("dx", dx)
    wall_active = _wall_physics_enabled(states, hydraulic_diameter, darcy_friction_factor, wall_heat_flux)
    fuel_active = _fuel_injection_enabled(states, fuel_mass_flow_rate_per_length, fuel_axial_velocity, fuel_specific_total_enthalpy)
    combustion_active = _combustion_enabled(
        states, fuel_burn_rate_per_length, fuel_lower_heating_value
    )
    interface_fluxes = boundary_interface_fluxes(
        states, gas, boundary_conditions, scheme=flux_scheme
    )
    rhs = quasi_1d_residual(states, interface_fluxes, geometry, spacing, gas)
    if wall_active:
        rhs = rhs + combined_wall_source(states, hydraulic_diameter, darcy_friction_factor, wall_heat_flux, gas)
    if fuel_active:
        rhs = rhs + distributed_fuel_injection_source(states, geometry, fuel_mass_flow_rate_per_length, fuel_axial_velocity, fuel_specific_total_enthalpy, gas)
    if combustion_active:
        rhs = rhs + distributed_combustion_heat_release_source(
            states, geometry, fuel_burn_rate_per_length, fuel_lower_heating_value, gas
        )
    return rhs


def quasi_1d_rhs_transmissive(
    U: ArrayLike,
    geometry: AreaProfile,
    dx: object,
    gas: GasProperties,
    *,
    flux_scheme: object = "rusanov",
    hydraulic_diameter: object = None,
    darcy_friction_factor: object = 0.0,
    wall_heat_flux: object = 0.0,
    fuel_mass_flow_rate_per_length: object = 0.0,
    fuel_axial_velocity: object = 0.0,
    fuel_specific_total_enthalpy: object = 0.0,
    fuel_burn_rate_per_length: ArrayLike = 0.0,
    fuel_lower_heating_value: ArrayLike | None = None,
) -> NDArray[np.float64]:
    """Legacy wrapper retaining exactly transmissive boundary semantics."""
    return quasi_1d_rhs(
        U, geometry, dx, gas, flux_scheme=flux_scheme,
        boundary_conditions=BoundaryConditions(), hydraulic_diameter=hydraulic_diameter,
        darcy_friction_factor=darcy_friction_factor, wall_heat_flux=wall_heat_flux,
        fuel_mass_flow_rate_per_length=fuel_mass_flow_rate_per_length,
        fuel_axial_velocity=fuel_axial_velocity,
        fuel_specific_total_enthalpy=fuel_specific_total_enthalpy,
        fuel_burn_rate_per_length=fuel_burn_rate_per_length,
        fuel_lower_heating_value=fuel_lower_heating_value,
    )


def solve_euler_1d(
    U0: ArrayLike,
    dx: object,
    t_final: object,
    gas: GasProperties,
    numerical: NumericalConfig,
    max_steps: int = 100_000,
) -> SolverResult:
    """Advance a uniform-grid baseline Euler state from time zero to t_final [s]."""
    state = np.asarray(U0, dtype=float)
    if state.ndim != 2 or state.shape[-1] != 3 or state.shape[0] < 2:
        raise ValueError("U0 must have shape (N, 3) with N >= 2")
    conservative_to_primitive(state, gas)
    spacing = _positive_scalar("dx", dx)
    final_time = _positive_scalar("t_final", t_final)
    if isinstance(max_steps, (bool, np.bool_)) or not isinstance(max_steps, (int, np.integer)) or max_steps <= 0:
        raise ValueError("max_steps must be a positive integer")

    state = np.array(state, dtype=float, copy=True)
    time = 0.0
    steps = 0
    def rhs(stage_state: NDArray[np.float64]) -> NDArray[np.float64]:
        return euler_rhs_transmissive(stage_state, spacing, gas)

    while time < final_time:
        if steps >= max_steps:
            raise RuntimeError("maximum solver step count reached before t_final")
        dt_cfl = cfl_timestep(state, spacing, gas, numerical)
        remaining = final_time - time
        final_step = dt_cfl >= remaining
        dt = remaining if final_step else dt_cfl
        state = ssp_rk3_step(state, dt, rhs)
        conservative_to_primitive(state, gas)
        steps += 1
        if final_step:
            time = final_time
        else:
            time += dt

    return SolverResult(U=state, time=time, steps=steps)


def solve_quasi_1d(
    U0: ArrayLike,
    geometry: AreaProfile,
    dx: object,
    t_final: object,
    gas: GasProperties,
    numerical: NumericalConfig,
    max_steps: int = 100_000,
    *,
    flux_scheme: object = "rusanov",
    hydraulic_diameter: object = None,
    darcy_friction_factor: object = 0.0,
    wall_heat_flux: object = 0.0,
    fuel_mass_flow_rate_per_length: object = 0.0,
    fuel_axial_velocity: object = 0.0,
    fuel_specific_total_enthalpy: object = 0.0,
    fuel_burn_rate_per_length: ArrayLike = 0.0,
    fuel_lower_heating_value: ArrayLike | None = None,
    boundary_conditions: BoundaryConditions | None = None,
) -> SolverResult:
    """Advance quasi-1D flow with optional wall, injection, and combustion sources.

    ``fuel_burn_rate_per_length`` [kg/(m s)] and its caller-supplied
    ``fuel_lower_heating_value`` [J/kg] define P8 chemical heat release and
    are independent from the P7 injected-fuel inputs. Zero burn with ``None``
    LHV disables combustion; an explicit LHV is always validated. Combustion
    is evaluated in the full SSP-RK3 RHS path and does not alter the CFL rule.
    """
    state = np.asarray(U0, dtype=float)
    if state.ndim != 2 or state.shape[-1] != 3 or state.shape[0] < 2:
        raise ValueError("U0 must have shape (N, 3) with N >= 2")
    if not isinstance(geometry, AreaProfile):
        raise TypeError("geometry must be an AreaProfile")
    if geometry.num_cells != state.shape[0]:
        raise ValueError("geometry.num_cells must match U0 cell count")
    conservative_to_primitive(state, gas)
    spacing = _positive_scalar("dx", dx)
    final_time = _positive_scalar("t_final", t_final)
    if isinstance(max_steps, (bool, np.bool_)) or not isinstance(max_steps, (int, np.integer)) or max_steps <= 0:
        raise ValueError("max_steps must be a positive integer")
    if flux_scheme not in ("rusanov", "steger-warming"):
        raise ValueError("supported schemes are 'rusanov' and 'steger-warming'")
    conditions = validate_boundary_conditions(boundary_conditions, state, gas)
    wall_active = _wall_physics_enabled(state, hydraulic_diameter, darcy_friction_factor, wall_heat_flux)
    fuel_active = _fuel_injection_enabled(state, fuel_mass_flow_rate_per_length, fuel_axial_velocity, fuel_specific_total_enthalpy)
    combustion_active = _combustion_enabled(
        state, fuel_burn_rate_per_length, fuel_lower_heating_value
    )
    if wall_active:
        combined_wall_source(state, hydraulic_diameter, darcy_friction_factor, wall_heat_flux, gas)
    if fuel_active:
        distributed_fuel_injection_source(state, geometry, fuel_mass_flow_rate_per_length, fuel_axial_velocity, fuel_specific_total_enthalpy, gas)

    state = np.array(state, dtype=float, copy=True)
    time = 0.0
    steps = 0
    source_kwargs: dict[str, object] = {}
    if wall_active:
        source_kwargs.update(hydraulic_diameter=hydraulic_diameter, darcy_friction_factor=darcy_friction_factor, wall_heat_flux=wall_heat_flux)
    if fuel_active:
        source_kwargs.update(fuel_mass_flow_rate_per_length=fuel_mass_flow_rate_per_length, fuel_axial_velocity=fuel_axial_velocity, fuel_specific_total_enthalpy=fuel_specific_total_enthalpy)
    if combustion_active:
        source_kwargs.update(
            fuel_burn_rate_per_length=fuel_burn_rate_per_length,
            fuel_lower_heating_value=fuel_lower_heating_value,
        )

    def rhs(stage_state: NDArray[np.float64]) -> NDArray[np.float64]:
        if boundary_conditions is None:
            return quasi_1d_rhs_transmissive(
                stage_state, geometry, spacing, gas, flux_scheme=flux_scheme, **source_kwargs
            )
        return quasi_1d_rhs(
            stage_state, geometry, spacing, gas, flux_scheme=flux_scheme,
            boundary_conditions=conditions, **source_kwargs,
        )

    while time < final_time:
        if steps >= max_steps:
            raise RuntimeError("maximum solver step count reached before t_final")
        dt_cfl = cfl_timestep(state, spacing, gas, numerical)
        remaining = final_time - time
        final_step = dt_cfl >= remaining
        dt = remaining if final_step else dt_cfl
        state = ssp_rk3_step(state, dt, rhs)
        conservative_to_primitive(state, gas)
        steps += 1
        if final_step:
            time = final_time
        else:
            time += dt

    return SolverResult(U=state, time=time, steps=steps)
