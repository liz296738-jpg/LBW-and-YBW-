"""Fixed-composition variable-thermochemistry Euler compatibility operators.

This module is the next isolated P11.3B bridge toward the teacher-reference
second-scheme solver. It does not replace the accepted constant-gamma
production operators. The composition is fixed for the supplied state array;
species evolution remains a later mixing/reaction-closure stage.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .geometry import AreaProfile, area_change_per_cell
from .thermochemistry import SpeciesThermoModel
from .validation import require_positive_scalar
from .variable_state import variable_conservative_to_primitive


def variable_euler_flux(
    U: ArrayLike,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return physical 1D Euler flux using local variable thermochemistry."""

    conservative = np.asarray(U, dtype=float)
    primitive = variable_conservative_to_primitive(
        conservative, mass_fractions, species
    )
    rho = primitive.rho
    u = primitive.u
    p = primitive.p
    rho_E = conservative[..., 2]

    return np.stack(
        (
            rho * u,
            rho * u**2 + p,
            u * (rho_E + p),
        ),
        axis=-1,
    )


def variable_rusanov_flux(
    U_left: ArrayLike,
    U_right: ArrayLike,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return fixed-composition Rusanov interface flux with local sound speed."""

    left = np.asarray(U_left, dtype=float)
    right = np.asarray(U_right, dtype=float)
    if left.ndim == 0 or left.shape[-1] != 3:
        raise ValueError("U_left last dimension must have length 3")
    if right.ndim == 0 or right.shape[-1] != 3:
        raise ValueError("U_right last dimension must have length 3")
    left, right = np.broadcast_arrays(left, right)

    primitive_left = variable_conservative_to_primitive(
        left, mass_fractions, species
    )
    primitive_right = variable_conservative_to_primitive(
        right, mass_fractions, species
    )
    flux_left = variable_euler_flux(left, mass_fractions, species)
    flux_right = variable_euler_flux(right, mass_fractions, species)

    sound_left = np.sqrt(
        primitive_left.gamma * primitive_left.R * primitive_left.T
    )
    sound_right = np.sqrt(
        primitive_right.gamma * primitive_right.R * primitive_right.T
    )
    alpha = np.maximum(
        np.abs(primitive_left.u) + sound_left,
        np.abs(primitive_right.u) + sound_right,
    )
    return 0.5 * (flux_left + flux_right) - 0.5 * alpha[..., np.newaxis] * (
        right - left
    )


def variable_internal_rusanov_fluxes(
    U: ArrayLike,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return internal fixed-composition Rusanov fluxes for ``(..., N, 3)`` states."""

    states = np.asarray(U, dtype=float)
    if states.ndim < 2 or states.shape[-1] != 3 or states.shape[-2] < 2:
        raise ValueError("U must have shape (..., N, 3) with N >= 2")
    return variable_rusanov_flux(
        states[..., :-1, :],
        states[..., 1:, :],
        mass_fractions,
        species,
    )


def variable_transmissive_interface_fluxes(
    U: ArrayLike,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return ``N+1`` interface fluxes using zero-gradient ghost states.

    This is a compatibility/test boundary path, not the final teacher inlet/outlet
    case adapter. The first and last physical states are copied into ghost cells.
    """

    states = np.asarray(U, dtype=float)
    if states.ndim != 2 or states.shape[-1] != 3 or states.shape[0] < 1:
        raise ValueError("U must have shape (N, 3) with N >= 1")

    left_states = np.concatenate((states[:1], states), axis=0)
    right_states = np.concatenate((states, states[-1:]), axis=0)
    return variable_rusanov_flux(
        left_states, right_states, mass_fractions, species
    )


def variable_finite_volume_residual(
    interface_fluxes: ArrayLike,
    dx: object,
) -> NDArray[np.float64]:
    """Return conservative uniform-grid ``dU/dt = -Delta F / dx``."""

    fluxes = np.asarray(interface_fluxes, dtype=float)
    if fluxes.ndim != 2 or fluxes.shape[-1] != 3 or fluxes.shape[0] < 2:
        raise ValueError("interface_fluxes must have shape (N+1, 3) with N >= 1")
    if not np.all(np.isfinite(fluxes)):
        raise ValueError("interface_fluxes must be finite")
    spacing = require_positive_scalar("dx", dx)
    return -(fluxes[1:, :] - fluxes[:-1, :]) / spacing


def variable_geometric_area_source(
    U: ArrayLike,
    geometry: AreaProfile,
    dx: object,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return quasi-1D geometric momentum source with variable-thermo pressure."""

    if not isinstance(geometry, AreaProfile):
        raise TypeError("geometry must be an AreaProfile")
    states = np.asarray(U, dtype=float)
    if states.ndim != 2 or states.shape[-1] != 3:
        raise ValueError("U must have shape (N, 3)")
    if states.shape[0] != geometry.num_cells:
        raise ValueError("U cell count must match geometry.num_cells")
    spacing = require_positive_scalar("dx", dx)
    primitive = variable_conservative_to_primitive(
        states, mass_fractions, species
    )

    source = np.zeros_like(states, dtype=float)
    source[:, 1] = (
        primitive.p
        * area_change_per_cell(geometry)
        / geometry.cell_area
        / spacing
    )
    return source


def variable_area_weighted_flux_residual(
    interface_fluxes: ArrayLike,
    geometry: AreaProfile,
    dx: object,
) -> NDArray[np.float64]:
    """Return ``-Delta(A Fhat)/(A_i dx)`` for complete interface fluxes."""

    if not isinstance(geometry, AreaProfile):
        raise TypeError("geometry must be an AreaProfile")
    fluxes = np.asarray(interface_fluxes, dtype=float)
    if fluxes.ndim != 2 or fluxes.shape[-1] != 3:
        raise ValueError("interface_fluxes must have shape (N+1, 3)")
    if fluxes.shape[0] != geometry.num_cells + 1:
        raise ValueError("interface flux count must equal geometry.num_cells + 1")
    if not np.all(np.isfinite(fluxes)):
        raise ValueError("interface_fluxes must be finite")
    spacing = require_positive_scalar("dx", dx)

    weighted = fluxes * geometry.face_area[:, np.newaxis]
    return -(
        weighted[1:, :] - weighted[:-1, :]
    ) / (geometry.cell_area[:, np.newaxis] * spacing)


def variable_quasi_1d_residual(
    U: ArrayLike,
    interface_fluxes: ArrayLike,
    geometry: AreaProfile,
    dx: object,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return source-free quasi-1D Euler residual for fixed composition."""

    return variable_area_weighted_flux_residual(
        interface_fluxes, geometry, dx
    ) + variable_geometric_area_source(
        U, geometry, dx, mass_fractions, species
    )


def variable_quasi_1d_rhs_transmissive(
    U: ArrayLike,
    geometry: AreaProfile,
    dx: object,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return source-free fixed-composition quasi-1D RHS with transmissive faces."""

    fluxes = variable_transmissive_interface_fluxes(
        U, mass_fractions, species
    )
    return variable_quasi_1d_residual(
        U,
        fluxes,
        geometry,
        dx,
        mass_fractions,
        species,
    )
