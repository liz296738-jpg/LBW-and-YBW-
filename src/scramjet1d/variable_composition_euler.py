"""Euler/Rusanov compatibility operators for cell-wise teacher composition.

This P11.3F layer extends the already verified variable-thermochemistry Euler
operators to interfaces whose left and right cells may use different
source-backed H2/C2H4 composition vectors.

The numerical state remains the three quasi-one-dimensional conservative flow
variables ``[rho, rho*u, rho*E]``.  Composition is supplied algebraically by a
:class:`TeacherCompositionField`; this module does not add species-transport
PDEs, reaction kinetics, or an independent chemical heat-release source.
"""

from __future__ import annotations

from typing import Mapping

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .geometry import AreaProfile, area_change_per_cell
from .thermochemistry import SpeciesThermoModel
from .validation import require_positive_scalar
from .variable_composition import (
    TeacherCompositionField,
    variable_composition_conservative_to_primitive,
)
from .variable_euler import variable_area_weighted_flux_residual, variable_euler_flux
from .variable_state import variable_conservative_to_primitive


def _single_state(name: str, U: ArrayLike) -> NDArray[np.float64]:
    state = np.asarray(U, dtype=float)
    if state.shape != (3,):
        raise ValueError(f"{name} must have shape (3,)")
    if not np.all(np.isfinite(state)):
        raise ValueError(f"{name} must be finite")
    return state


def variable_composition_euler_fluxes(
    U: ArrayLike,
    field: TeacherCompositionField,
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return one physical Euler flux per cell using that cell's composition."""

    if not isinstance(field, TeacherCompositionField):
        raise TypeError("field must be a TeacherCompositionField")
    states = np.asarray(U, dtype=float)
    if states.shape != (field.num_cells, 3):
        raise ValueError(
            f"U must have shape ({field.num_cells}, 3) matching the composition field"
        )
    if not np.all(np.isfinite(states)):
        raise ValueError("U must be finite")

    fluxes = np.empty_like(states, dtype=float)
    for index in range(field.num_cells):
        fluxes[index] = variable_euler_flux(
            states[index], field.composition_at(index), species
        )
    return fluxes


def variable_composition_rusanov_flux(
    U_left: ArrayLike,
    U_right: ArrayLike,
    mass_fractions_left: Mapping[str, float],
    mass_fractions_right: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return one Rusanov flux with independently recovered left/right mixtures.

    Each conservative state is interpreted using its own supplied composition.
    The dissipation speed is

    ``max(|u_L| + a_L, |u_R| + a_R)``

    with ``a = sqrt(gamma(T,Y) R(Y) T)`` evaluated independently on each side.
    The function intentionally returns only the three flow-equation fluxes; it
    does not construct species fluxes.
    """

    left = _single_state("U_left", U_left)
    right = _single_state("U_right", U_right)

    primitive_left = variable_conservative_to_primitive(
        left, mass_fractions_left, species
    )
    primitive_right = variable_conservative_to_primitive(
        right, mass_fractions_right, species
    )
    flux_left = variable_euler_flux(left, mass_fractions_left, species)
    flux_right = variable_euler_flux(right, mass_fractions_right, species)

    sound_left = float(
        np.sqrt(primitive_left.gamma * primitive_left.R * primitive_left.T)
    )
    sound_right = float(
        np.sqrt(primitive_right.gamma * primitive_right.R * primitive_right.T)
    )
    alpha = max(
        abs(float(primitive_left.u)) + sound_left,
        abs(float(primitive_right.u)) + sound_right,
    )
    return 0.5 * (flux_left + flux_right) - 0.5 * alpha * (right - left)


def variable_composition_internal_rusanov_fluxes(
    U: ArrayLike,
    field: TeacherCompositionField,
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return the ``N-1`` internal interface fluxes for a composition field."""

    if not isinstance(field, TeacherCompositionField):
        raise TypeError("field must be a TeacherCompositionField")
    states = np.asarray(U, dtype=float)
    if states.shape != (field.num_cells, 3):
        raise ValueError(
            f"U must have shape ({field.num_cells}, 3) matching the composition field"
        )
    if field.num_cells < 2:
        raise ValueError("at least two cells are required for internal interface fluxes")
    if not np.all(np.isfinite(states)):
        raise ValueError("U must be finite")

    fluxes = np.empty((field.num_cells - 1, 3), dtype=float)
    for index in range(field.num_cells - 1):
        fluxes[index] = variable_composition_rusanov_flux(
            states[index],
            states[index + 1],
            field.composition_at(index),
            field.composition_at(index + 1),
            species,
        )
    return fluxes


def variable_composition_transmissive_interface_fluxes(
    U: ArrayLike,
    field: TeacherCompositionField,
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return ``N+1`` Rusanov fluxes with zero-gradient boundary ghost states.

    Boundary ghost states copy both the conservative state and composition of
    the adjacent physical cell.  These boundaries remain a verification path,
    not the final teacher inlet/outlet model.
    """

    if not isinstance(field, TeacherCompositionField):
        raise TypeError("field must be a TeacherCompositionField")
    states = np.asarray(U, dtype=float)
    if states.shape != (field.num_cells, 3):
        raise ValueError(
            f"U must have shape ({field.num_cells}, 3) matching the composition field"
        )
    if not np.all(np.isfinite(states)):
        raise ValueError("U must be finite")

    fluxes = np.empty((field.num_cells + 1, 3), dtype=float)
    first_composition = field.composition_at(0)
    last_composition = field.composition_at(field.num_cells - 1)
    fluxes[0] = variable_composition_rusanov_flux(
        states[0], states[0], first_composition, first_composition, species
    )
    if field.num_cells > 1:
        fluxes[1:-1] = variable_composition_internal_rusanov_fluxes(
            states, field, species
        )
    fluxes[-1] = variable_composition_rusanov_flux(
        states[-1], states[-1], last_composition, last_composition, species
    )
    return fluxes


def variable_composition_geometric_area_source(
    U: ArrayLike,
    field: TeacherCompositionField,
    geometry: AreaProfile,
    dx: object,
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return quasi-1D geometric momentum source using per-cell pressure."""

    if not isinstance(field, TeacherCompositionField):
        raise TypeError("field must be a TeacherCompositionField")
    if not isinstance(geometry, AreaProfile):
        raise TypeError("geometry must be an AreaProfile")
    if field.num_cells != geometry.num_cells:
        raise ValueError("composition field cell count must match geometry.num_cells")
    states = np.asarray(U, dtype=float)
    if states.shape != (field.num_cells, 3):
        raise ValueError(
            f"U must have shape ({field.num_cells}, 3) matching the composition field"
        )
    spacing = require_positive_scalar("dx", dx)
    primitive = variable_composition_conservative_to_primitive(
        states, field, species
    )

    source = np.zeros_like(states, dtype=float)
    source[:, 1] = (
        primitive.p
        * area_change_per_cell(geometry)
        / geometry.cell_area
        / spacing
    )
    return source


def variable_composition_quasi_1d_rhs_transmissive(
    U: ArrayLike,
    field: TeacherCompositionField,
    geometry: AreaProfile,
    dx: object,
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return source-free quasi-1D RHS for a prescribed cell-wise composition.

    Only the Euler area operator is included.  Fuel injection, wall friction,
    wall heat transfer, reaction/composition evolution, and time advancement are
    intentionally outside this compatibility step.
    """

    fluxes = variable_composition_transmissive_interface_fluxes(
        U, field, species
    )
    return variable_area_weighted_flux_residual(
        fluxes, geometry, dx
    ) + variable_composition_geometric_area_source(
        U, field, geometry, dx, species
    )
