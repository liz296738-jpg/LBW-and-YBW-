"""Boundary-condition configuration and physical interface-flux semantics."""

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import GasProperties
from .flux import euler_flux
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
    outlet: Literal["transmissive", "supersonic-outflow"] = "transmissive"
    inlet_state: PrimitiveBoundaryState | None = None

    def __post_init__(self) -> None:
        if self.inlet not in ("transmissive", "supersonic-inflow"):
            raise ValueError("supported inlet boundaries are 'transmissive' and 'supersonic-inflow'")
        if self.outlet not in ("transmissive", "supersonic-outflow"):
            raise ValueError("supported outlet boundaries are 'transmissive' and 'supersonic-outflow'")
        if self.inlet_state is not None and not isinstance(self.inlet_state, PrimitiveBoundaryState):
            raise TypeError("inlet_state must be a PrimitiveBoundaryState or None")
        if self.inlet == "transmissive" and self.inlet_state is not None:
            raise ValueError("inlet_state is only valid for supersonic-inflow")


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
    if states.ndim != 2 or states.shape[-1] != 3 or states.shape[0] < 2:
        raise ValueError("U must have shape (N, 3) with N >= 2")
    conditions = validate_boundary_conditions(boundary_conditions, states, gas)
    from .spatial import internal_numerical_fluxes

    if conditions.inlet == "transmissive" and conditions.outlet == "transmissive":
        return internal_numerical_fluxes(transmissive_ghost_cells(states), gas, scheme=scheme)

    internal = internal_numerical_fluxes(states, gas, scheme=scheme)
    if conditions.inlet == "supersonic-inflow":
        inlet = conditions.inlet_state
        assert inlet is not None
        left = euler_flux(primitive_to_conservative(inlet.rho, inlet.u, inlet.p, gas), gas)
    else:
        left = euler_flux(states[0], gas)
    right = euler_flux(states[-1], gas)
    return np.concatenate((np.asarray(left, dtype=float)[np.newaxis, :], internal, np.asarray(right, dtype=float)[np.newaxis, :]), axis=0)
