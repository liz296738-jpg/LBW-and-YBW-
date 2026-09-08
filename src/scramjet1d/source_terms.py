"""Approved source-term contributions for the quasi-one-dimensional model."""

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
    direct addition to ``dU/dt``.  The only implemented source contribution is area
    geometry; friction, heat, fuel, and combustion remain unimplemented.
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
