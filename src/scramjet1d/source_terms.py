"""Approved geometric and prescribed wall-friction source contributions."""

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
    direct addition to ``dU/dt``.  Geometry and the independent prescribed wall-
    friction source are implemented; heat, fuel, and combustion remain unimplemented.
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
    ``[0, -f_D rho u |u| / (2 D_h), 0]`` [kg/(m^2 s^2)]; it is not yet assembled
    into the quasi-1D solver.
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
