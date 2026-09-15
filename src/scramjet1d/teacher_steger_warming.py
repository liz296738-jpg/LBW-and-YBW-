"""Teacher Chapter 11 variable-property Steger-Warming flux-vector splitting.

The photographed Chapter 11 source freezes Eqs. (11.42)--(11.44):

* local characteristic speeds ``lambda_1=u``, ``lambda_2=u-c``,
  ``lambda_3=u+c``;
* the Steger-Warming split-flux vector of Eq. (11.42);
* raw eigenvalue splitting ``lambda_i^+/-=(lambda_i +/- |lambda_i|)/2``;
* the near-zero smoothing form
  ``lambda_i^+/-=(lambda_i +/- sqrt(lambda_i^2+epsilon^2))/2``.

The source image does not provide a numerical value for ``epsilon``.  This
module therefore requires ``epsilon_m_per_s`` explicitly on every split/flux
call and intentionally provides no default.  ``epsilon=0`` is useful for the
source Eq. (11.43) limiting case; a non-zero production/case value must carry
separate provenance.

The textbook Eq. (11.42) is written for the area-weighted flux ``A F`` and
contains a prefactor ``rho*A/(2*gamma)``.  The repository's finite-volume
operator already multiplies numerical face fluxes by face area.  Functions here
therefore return the *per-unit-area* split flux, i.e. Eq. (11.42) divided by
``A``.  This prevents area from being counted twice.
"""

from __future__ import annotations

from math import isfinite
from typing import Mapping

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .thermochemistry import SpeciesThermoModel
from .variable_composition import TeacherCompositionField
from .variable_state import variable_conservative_to_primitive


def _single_state(name: str, U: ArrayLike) -> NDArray[np.float64]:
    state = np.asarray(U, dtype=float)
    if state.shape != (3,):
        raise ValueError(f"{name} must have shape (3,)")
    if not np.all(np.isfinite(state)):
        raise ValueError(f"{name} must be finite")
    return state


def _epsilon(value: object) -> float:
    epsilon = float(value)
    if not isfinite(epsilon) or epsilon < 0.0:
        raise ValueError("epsilon_m_per_s must be finite and nonnegative")
    return epsilon


def teacher_smoothed_eigenvalue_split(
    eigenvalues_m_per_s: ArrayLike,
    *,
    epsilon_m_per_s: object,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return teacher Eq. (11.44) positive/negative eigenvalue parts.

    ``epsilon_m_per_s=0`` reduces exactly to the raw Eq. (11.43) split.  The
    numerical epsilon is deliberately caller-supplied because the photographed
    source freezes the formula but not a value.
    """

    eigenvalues = np.asarray(eigenvalues_m_per_s, dtype=float)
    if not np.all(np.isfinite(eigenvalues)):
        raise ValueError("eigenvalues_m_per_s must be finite")
    epsilon = _epsilon(epsilon_m_per_s)
    magnitude = np.sqrt(eigenvalues**2 + epsilon**2)
    return (
        np.asarray(0.5 * (eigenvalues + magnitude), dtype=float),
        np.asarray(0.5 * (eigenvalues - magnitude), dtype=float),
    )


def teacher_variable_characteristic_speeds(
    U: ArrayLike,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Return local teacher ordering ``[u, u-c, u+c]`` [m/s]."""

    state = _single_state("U", U)
    primitive = variable_conservative_to_primitive(state, mass_fractions, species)
    u = float(primitive.u)
    sound_speed = float(np.sqrt(primitive.gamma * primitive.R * primitive.T))
    return np.array([u, u - sound_speed, u + sound_speed], dtype=float)


def teacher_variable_steger_warming_split_flux(
    U: ArrayLike,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
    *,
    epsilon_m_per_s: object,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return per-area Eq. (11.42) ``F_plus`` and ``F_minus`` for one state.

    Local ``gamma``, ``c`` and total enthalpy are recovered from the same
    source-backed variable thermochemistry used by the teacher composition
    path.  Total enthalpy is ``H=(rhoE+p)/rho``, matching ``h_t=e_t+p/rho``.
    """

    state = _single_state("U", U)
    primitive = variable_conservative_to_primitive(state, mass_fractions, species)
    rho = float(primitive.rho)
    u = float(primitive.u)
    p = float(primitive.p)
    gamma = float(primitive.gamma)
    sound_speed = float(np.sqrt(gamma * primitive.R * primitive.T))
    total_enthalpy = float((state[2] + p) / rho)

    eigenvalues = np.array([u, u - sound_speed, u + sound_speed], dtype=float)
    positive, negative = teacher_smoothed_eigenvalue_split(
        eigenvalues, epsilon_m_per_s=epsilon_m_per_s
    )

    def split_flux(split: NDArray[np.float64]) -> NDArray[np.float64]:
        lambda_1, lambda_2, lambda_3 = split
        mass = 2.0 * (gamma - 1.0) * lambda_1 + lambda_2 + lambda_3
        momentum = (
            2.0 * (gamma - 1.0) * u * lambda_1
            + (u - sound_speed) * lambda_2
            + (u + sound_speed) * lambda_3
        )
        energy = (
            (gamma - 1.0) * u**2 * lambda_1
            + (total_enthalpy - sound_speed * u) * lambda_2
            + (total_enthalpy + sound_speed * u) * lambda_3
        )
        return (rho / (2.0 * gamma)) * np.array(
            [mass, momentum, energy], dtype=float
        )

    return split_flux(positive), split_flux(negative)


def teacher_variable_steger_warming_flux(
    U_left: ArrayLike,
    U_right: ArrayLike,
    mass_fractions_left: Mapping[str, float],
    mass_fractions_right: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
    *,
    epsilon_m_per_s: object,
) -> NDArray[np.float64]:
    """Return first-order FVS interface flux ``F+(L)+F-(R)``."""

    left = _single_state("U_left", U_left)
    right = _single_state("U_right", U_right)
    left_plus, _ = teacher_variable_steger_warming_split_flux(
        left,
        mass_fractions_left,
        species,
        epsilon_m_per_s=epsilon_m_per_s,
    )
    _, right_minus = teacher_variable_steger_warming_split_flux(
        right,
        mass_fractions_right,
        species,
        epsilon_m_per_s=epsilon_m_per_s,
    )
    return left_plus + right_minus


def teacher_variable_composition_internal_steger_warming_fluxes(
    U: ArrayLike,
    field: TeacherCompositionField,
    species: Mapping[str, SpeciesThermoModel],
    *,
    epsilon_m_per_s: object,
) -> NDArray[np.float64]:
    """Return ``N-1`` teacher FVS fluxes for a prescribed composition field."""

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

    # Validate once even before the first interface loop so bad epsilon fails
    # deterministically for every field size.
    epsilon = _epsilon(epsilon_m_per_s)
    fluxes = np.empty((field.num_cells - 1, 3), dtype=float)
    for index in range(field.num_cells - 1):
        fluxes[index] = teacher_variable_steger_warming_flux(
            states[index],
            states[index + 1],
            field.composition_at(index),
            field.composition_at(index + 1),
            species,
            epsilon_m_per_s=epsilon,
        )
    return fluxes
