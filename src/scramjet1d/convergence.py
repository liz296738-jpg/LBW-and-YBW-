"""Steady-convergence diagnostics for quasi-one-dimensional integration."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import GasProperties
from .gas import speed_of_sound
from .state import conservative_to_primitive


@dataclass(frozen=True)
class SteadyResidualReference:
    """Fixed scales for a dimensionless semi-discrete steady residual."""

    time_scale: float
    conservative_scales: NDArray[np.float64]


def steady_residual_reference(
    U0: ArrayLike, dx: object, gas: GasProperties
) -> SteadyResidualReference:
    """Build fixed ``L_ref=N dx`` normalization scales from the initial state."""

    states = np.asarray(U0, dtype=float)
    spacing = np.asarray(dx, dtype=float)
    if states.ndim != 2 or states.shape[-1] != 3 or states.shape[0] < 1:
        raise ValueError("U0 must have shape (N, 3)")
    if spacing.ndim != 0 or not np.isfinite(spacing) or spacing <= 0:
        raise ValueError("dx must be a finite strictly positive scalar")

    q = conservative_to_primitive(states, gas)
    velocity = float(np.max(np.abs(q.u) + speed_of_sound(q.T, gas)))
    density = float(np.max(q.rho))
    energy = float(np.max(np.abs(states[:, 2])))
    scales = np.array((density, density * velocity, energy), dtype=float)
    if (
        not np.isfinite(velocity)
        or velocity <= 0
        or not np.all(np.isfinite(scales) & (scales > 0))
    ):
        raise ValueError(
            "initial state cannot establish finite positive steady residual scales"
        )
    return SteadyResidualReference(
        float(states.shape[0] * spacing / velocity), scales
    )


def normalized_steady_residual(
    rhs: ArrayLike, reference: SteadyResidualReference
) -> float:
    """Return ``max_j(t_ref / U_ref,j * max_i |R_i,j|)``."""

    residual = np.asarray(rhs, dtype=float)
    if residual.ndim != 2 or residual.shape[-1] != 3:
        raise ValueError("rhs must have shape (N, 3)")
    if not np.all(np.isfinite(residual)):
        raise ValueError("rhs must be finite")
    return float(
        np.max(
            reference.time_scale
            * np.max(np.abs(residual), axis=0)
            / reference.conservative_scales
        )
    )


def max_relative_density_change(
    U_previous: ArrayLike,
    U_current: ArrayLike,
    gas: GasProperties,
) -> float:
    """Return the teacher-reference maximum relative density iteration change.

    This implements the diagnostic form used by the teacher-provided Chapter 11
    steady criterion (Eq. 11.46):

    ``max_i |(rho_i^(n+1) - rho_i^n) / rho_i^n|``.

    It is an additional compatibility diagnostic, not a replacement for the
    repository's normalized semi-discrete steady residual. Both states must have
    identical ``(N, 3)`` conservative-state shapes and pass the existing physical
    state validation through :func:`conservative_to_primitive`.
    """

    previous = np.asarray(U_previous, dtype=float)
    current = np.asarray(U_current, dtype=float)
    if previous.ndim != 2 or previous.shape[-1] != 3 or previous.shape[0] < 1:
        raise ValueError("U_previous must have shape (N, 3)")
    if current.shape != previous.shape:
        raise ValueError("U_current must have the same shape as U_previous")
    if not np.all(np.isfinite(previous)) or not np.all(np.isfinite(current)):
        raise ValueError("conservative states must be finite")

    rho_previous = conservative_to_primitive(previous, gas).rho
    rho_current = conservative_to_primitive(current, gas).rho
    return float(
        np.max(np.abs((rho_current - rho_previous) / rho_previous))
    )
