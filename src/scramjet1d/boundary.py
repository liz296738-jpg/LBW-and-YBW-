"""Boundary-condition configuration and physical interface-flux semantics."""

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import GasProperties
from .flux import euler_flux
from .gas import speed_of_sound
from .state import conservative_to_primitive, primitive_to_conservative


@dataclass(frozen=True)
class PrimitiveBoundaryState:
    """Immutable prescribed primitive state for a physical inflow boundary."""

    rho: float
    u: float
    p: float

    def __post_init__(self) -> None:
        values = np.asarray((self.rho, self.u, self.p), dtype=float)
        if not np.all(np.isfinite(values)):
            raise ValueError("boundary rho, u, and p must be finite")
        if values[0] <= 0.0 or values[2] <= 0.0:
            raise ValueError("boundary rho and p must be strictly positive")


@dataclass(frozen=True)
class BoundaryConditions:
    """Immutable P9.1 boundary configuration; defaults retain transmissive behavior."""

    inlet: Literal["transmissive", "supersonic-inflow"] = "transmissive"
    outlet: Literal["transmissive", "supersonic-outflow", "subsonic-pressure"] = "transmissive"
    inlet_state: PrimitiveBoundaryState | None = None
    outlet_static_pressure: float | None = None

    def __post_init__(self) -> None:
        if self.inlet not in ("transmissive", "supersonic-inflow"):
            raise ValueError("supported inlet boundaries are 'transmissive' and 'supersonic-inflow'")
        if self.outlet not in ("transmissive", "supersonic-outflow", "subsonic-pressure"):
            raise ValueError("supported outlet boundaries are 'transmissive', 'supersonic-outflow', and 'subsonic-pressure'")
        if self.inlet_state is not None and not isinstance(self.inlet_state, PrimitiveBoundaryState):
            raise TypeError("inlet_state must be a PrimitiveBoundaryState or None")
        if self.inlet == "transmissive" and self.inlet_state is not None:
            raise ValueError("inlet_state is only valid for supersonic-inflow")
        pressure = self.outlet_static_pressure
        if self.outlet == "subsonic-pressure":
            value = np.asarray(pressure, dtype=float)
            if value.ndim != 0 or not np.isfinite(value) or value <= 0.0:
                raise ValueError("subsonic-pressure requires a finite strictly positive outlet_static_pressure")
        elif pressure is not None:
            raise ValueError("outlet_static_pressure is only valid for subsonic-pressure")


def subsonic_pressure_outlet_state(
    interior_state: ArrayLike, outlet_static_pressure: object, gas: GasProperties
) -> NDArray[np.float64]:
    """Reconstruct a rightward subsonic outlet state from entropy and ``J+``."""
    pressure = np.asarray(outlet_static_pressure, dtype=float)
    if pressure.ndim != 0 or not np.isfinite(pressure) or pressure <= 0.0:
        raise ValueError("outlet_static_pressure must be a finite strictly positive scalar")
    interior = np.asarray(interior_state, dtype=float)
    if interior.ndim < 1 or interior.shape[-1] != 3:
        raise ValueError("interior_state must have shape (..., 3)")
    primitive = conservative_to_primitive(interior, gas)
    if np.any(primitive.u <= 0.0) or np.any(primitive.Mach >= 1.0):
        raise ValueError("subsonic-pressure requires rightward interior flow with 0 < Mach < 1")
    sound = speed_of_sound(primitive.T, gas)
    entropy = primitive.p / primitive.rho**gas.gamma
    rho_boundary = (float(pressure) / entropy)**(1.0 / gas.gamma)
    sound_boundary = np.sqrt(gas.gamma * float(pressure) / rho_boundary)
    velocity_boundary = primitive.u + 2.0 * (sound - sound_boundary) / (gas.gamma - 1.0)
    boundary = primitive_to_conservative(rho_boundary, velocity_boundary, float(pressure), gas)
    reconstructed = conservative_to_primitive(boundary, gas)
    if np.any(reconstructed.u <= 0.0) or np.any(reconstructed.Mach >= 1.0):
        raise ValueError("subsonic-pressure reconstruction must remain rightward and subsonic")
    return boundary


def validate_boundary_conditions(
    boundary_conditions: BoundaryConditions | None, U: ArrayLike, gas: GasProperties
) -> BoundaryConditions:
    """Validate physical-boundary applicability against the supplied current state."""
    conditions = BoundaryConditions() if boundary_conditions is None else boundary_conditions
    if not isinstance(conditions, BoundaryConditions):
        raise TypeError("boundary_conditions must be a BoundaryConditions instance or None")
    states = np.asarray(U, dtype=float)
    if states.ndim < 2 or states.shape[-1] != 3 or states.shape[-2] < 1:
        raise ValueError("U must have shape (..., N, 3) with at least one cell")
    if conditions.inlet == "supersonic-inflow":
        if conditions.inlet_state is None:
            raise ValueError("supersonic-inflow requires inlet_state")
        inlet = conditions.inlet_state
        inlet_state = primitive_to_conservative(inlet.rho, inlet.u, inlet.p, gas)
        inlet_primitive = conservative_to_primitive(inlet_state, gas)
        if inlet_primitive.u <= 0.0 or inlet_primitive.Mach <= 1.0:
            raise ValueError("left supersonic-inflow requires u > 0 and Mach > 1")
    if conditions.outlet == "supersonic-outflow":
        outlet = conservative_to_primitive(states[..., -1, :], gas)
        if np.any(outlet.u <= 0.0) or np.any(outlet.Mach <= 1.0):
            raise ValueError("right supersonic-outflow requires u > 0 and Mach > 1")
    if conditions.outlet == "subsonic-pressure":
        assert conditions.outlet_static_pressure is not None
        subsonic_pressure_outlet_state(states[..., -1, :], conditions.outlet_static_pressure, gas)
    return conditions


def transmissive_ghost_cells(U: ArrayLike) -> NDArray[np.float64]:
    """Return a new state array with zero-gradient ghost cells on the cell axis."""
    states = np.asarray(U, dtype=float)
    if states.ndim < 2 or states.shape[-1] != 3 or states.shape[-2] < 1:
        raise ValueError("U must have shape (..., N, 3) with at least one cell")
    if not np.all(np.isfinite(states)):
        raise ValueError("U must be finite")
    return np.concatenate((states[..., :1, :], states, states[..., -1:, :]), axis=-2)


def boundary_interface_fluxes(
    U: ArrayLike,
    gas: GasProperties,
    boundary_conditions: BoundaryConditions | None = None,
    *,
    scheme: object = "rusanov",
) -> NDArray[np.float64]:
    """Return all N+1 interface fluxes with explicit P9.1 boundary semantics.

    A fixed left supersonic inflow uses ``F(U_in)`` independently of the first
    interior state. A right supersonic outflow uses ``F(U_N)``. The all-
    transmissive path deliberately retains the historical ghost-cell assembly.
    """
    states = np.asarray(U, dtype=float)
    if states.ndim < 2 or states.shape[-1] != 3 or states.shape[-2] < 2:
        raise ValueError("U must have shape (..., N, 3) with N >= 2")
    conditions = validate_boundary_conditions(boundary_conditions, states, gas)
    from .spatial import internal_numerical_fluxes

    if conditions.inlet == "transmissive" and conditions.outlet == "transmissive":
        return internal_numerical_fluxes(transmissive_ghost_cells(states), gas, scheme=scheme)

    internal = internal_numerical_fluxes(states, gas, scheme=scheme)
    if conditions.inlet == "supersonic-inflow":
        inlet = conditions.inlet_state
        assert inlet is not None
        left = euler_flux(primitive_to_conservative(inlet.rho, inlet.u, inlet.p, gas), gas)
        left = np.broadcast_to(np.asarray(left, dtype=float), states.shape[:-2] + (3,))
    else:
        left = euler_flux(states[..., 0, :], gas)
    if conditions.outlet == "subsonic-pressure":
        assert conditions.outlet_static_pressure is not None
        boundary_state = subsonic_pressure_outlet_state(
            states[..., -1, :], conditions.outlet_static_pressure, gas
        )
        pair = np.stack((states[..., -1, :], boundary_state), axis=-2)
        right = internal_numerical_fluxes(pair, gas, scheme=scheme)[..., 0, :]
    else:
        right = euler_flux(states[..., -1, :], gas)
    return np.concatenate(
        (left[..., np.newaxis, :], internal, right[..., np.newaxis, :]), axis=-2
    )
