"""Spatial assembly for baseline and quasi-one-dimensional Euler operators."""

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import GasProperties
from .flux import rusanov_flux
from .steger_warming import steger_warming_flux
from .geometry import AreaProfile
from .source_terms import geometric_area_source
from .validation import require_finite, require_positive_scalar


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


def internal_steger_warming_fluxes(U: ArrayLike, gas: GasProperties) -> NDArray[np.float64]:
    """Return internal Steger-Warming fluxes for cell-centered U[..., N, 3]."""
    states = np.asarray(U, dtype=float)
    if states.ndim < 2 or states.shape[-1] != 3 or states.shape[-2] < 2:
        raise ValueError("U must have shape (..., N, 3) with N >= 2")
    return steger_warming_flux(states[..., :-1, :], states[..., 1:, :], gas)


def internal_numerical_fluxes(U: ArrayLike, gas: GasProperties, scheme: object = "rusanov") -> NDArray[np.float64]:
    """Return internal interface fluxes for an explicitly selected numerical scheme."""
    if scheme == "rusanov":
        return internal_rusanov_fluxes(U, gas)
    if scheme == "steger-warming":
        return internal_steger_warming_fluxes(U, gas)
    raise ValueError("supported schemes are 'rusanov' and 'steger-warming'")


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


def area_weighted_flux_residual(
    interface_fluxes: ArrayLike, geometry: AreaProfile, dx: object
) -> NDArray[np.float64]:
    """Return ``-Δ(A F_hat)/(A_i dx)`` for complete interface fluxes in SI units."""
    if not isinstance(geometry, AreaProfile):
        raise TypeError("geometry must be an AreaProfile")

    fluxes = np.asarray(interface_fluxes, dtype=float)
    if fluxes.ndim < 2 or fluxes.shape[-1] != 3:
        raise ValueError("interface_fluxes must include an interface dimension and final flux dimension of length 3")
    if fluxes.shape[-2] != geometry.num_cells + 1:
        raise ValueError("interface_fluxes count must equal geometry.num_cells + 1")
    require_finite("interface_fluxes", fluxes)
    spacing = require_positive_scalar("dx", dx)

    weighted_fluxes = fluxes * geometry.face_area[:, np.newaxis]
    flux_difference = weighted_fluxes[..., 1:, :] - weighted_fluxes[..., :-1, :]
    return -flux_difference / (geometry.cell_area[:, np.newaxis] * spacing)


def quasi_1d_residual(
    U: ArrayLike,
    interface_fluxes: ArrayLike,
    geometry: AreaProfile,
    dx: object,
    gas: GasProperties,
) -> NDArray[np.float64]:
    """Return the quasi-1D semi-discrete RHS from supplied complete interface fluxes.

    This function does not create boundary states or select a numerical flux;
    callers provide the complete ``N + 1`` interface-flux array.
    """
    flux_part = area_weighted_flux_residual(interface_fluxes, geometry, dx)
    source_part = geometric_area_source(U, geometry, dx, gas)
    return flux_part + source_part
