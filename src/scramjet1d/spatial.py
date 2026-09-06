"""Spatial assembly for the source-free, one-dimensional Euler baseline."""

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import GasProperties
from .flux import rusanov_flux
from .validation import require_finite


def internal_rusanov_fluxes(U: ArrayLike, gas: GasProperties) -> NDArray[np.float64]:
    """Return internal Rusanov fluxes for cell-centered U[..., N, 3] in SI units."""
    states = np.asarray(U, dtype=float)
    if states.ndim < 2:
        raise ValueError("U must include a cell dimension and a final state dimension")
    if states.shape[-1] != 3:
        raise ValueError("U last dimension must have length 3")
    if states.shape[-2] < 2:
        raise ValueError("U must contain at least two cells")
    return rusanov_flux(states[..., :-1, :], states[..., 1:, :], gas)


def finite_volume_residual(interface_fluxes: ArrayLike, dx: float) -> NDArray[np.float64]:
    """Return dU/dt=-(F_right-F_left)/dx from complete uniform-grid interface fluxes."""
    fluxes = np.asarray(interface_fluxes, dtype=float)
    if fluxes.ndim < 2:
        raise ValueError("interface_fluxes must include an interface dimension and final flux dimension")
    if fluxes.shape[-1] != 3:
        raise ValueError("interface_fluxes last dimension must have length 3")
    if fluxes.shape[-2] < 2:
        raise ValueError("interface_fluxes must contain at least two interfaces")
    require_finite("interface_fluxes", fluxes)

    spacing = np.asarray(dx, dtype=float)
    if spacing.ndim != 0 or not np.isfinite(spacing) or spacing <= 0.0:
        raise ValueError("dx must be a finite and strictly positive scalar")
    return -(fluxes[..., 1:, :] - fluxes[..., :-1, :]) / spacing
