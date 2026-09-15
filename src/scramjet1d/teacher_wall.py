"""Teacher Chapter 11 wall-friction and wall-heat empirical closures.

The teacher-provided model gives empirical coefficient correlations on textbook
p. 257, Eqs. (11.25)--(11.26), and places the wall-friction coefficient in the
quasi-one-dimensional momentum source on pp. 255/260, Eqs. (11.16)/(11.38).

This module keeps those source relations separate from the generic production
wall-source interfaces:

* :func:`friction_coefficient_raw` returns Eq. (11.25) exactly;
* :func:`wall_heat_coefficient_raw` returns Eq. (11.26) exactly;
* :func:`darcy_friction_factor_from_teacher_f` exposes the explicit
  ``f_D = 4 f`` conversion required to match the project's existing Darcy
  source convention for forward flow.

No conversion from the empirical heat coefficient ``q(x)`` to a prescribed
wall heat flux [W/m^2] is made here because the photographed source pages do not
yet freeze the dimensional adapter between Eq. (11.26) and the ``rho*u*d(delta
q)/dx`` energy source in Eq. (11.38).  Inventing that adapter would be a silent
physics change.
"""

from __future__ import annotations

from math import isfinite

import numpy as np
from numpy.typing import ArrayLike, NDArray


# Teacher source p. 257, Eq. (11.25), polynomial in z = phi * eta.
_FRICTION_COEFFICIENT_POLYNOMIAL = (0.0018, 0.001958, 0.00927, -0.0088525)
# Teacher source p. 257, Eq. (11.26), polynomial in z = phi * eta.
_WALL_HEAT_COEFFICIENT_POLYNOMIAL = (0.0009, 0.001125, 0.00594, -0.00469)


def _nonnegative_array(name: str, value: ArrayLike) -> NDArray[np.float64]:
    array = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(array)) or np.any(array < 0.0):
        raise ValueError(f"{name} must be finite and nonnegative")
    return array


def _efficiency_array(value: ArrayLike) -> NDArray[np.float64]:
    eta = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(eta)) or np.any((eta < 0.0) | (eta > 1.0)):
        raise ValueError("eta must be finite and lie in [0, 1]")
    return eta


def _phi_eta(phi: ArrayLike, eta: ArrayLike) -> NDArray[np.float64]:
    equivalence_ratio = _nonnegative_array("phi", phi)
    efficiency = _efficiency_array(eta)
    try:
        equivalence_ratio, efficiency = np.broadcast_arrays(equivalence_ratio, efficiency)
    except ValueError as error:
        raise ValueError("phi and eta must be broadcast-compatible") from error
    return np.asarray(equivalence_ratio * efficiency, dtype=float)


def _cubic(z: NDArray[np.float64], coefficients: tuple[float, float, float, float]) -> NDArray[np.float64]:
    c0, c1, c2, c3 = coefficients
    return np.asarray(c0 + c1 * z + c2 * z**2 + c3 * z**3, dtype=float)


def friction_coefficient_raw(phi: ArrayLike, eta: ArrayLike) -> NDArray[np.float64]:
    """Return the unmodified teacher Eq. (11.25) wall-friction coefficient.

    ``f = 0.0018 + 0.001958 z + 0.00927 z^2 - 0.0088525 z^3``
    with ``z = phi*eta``.

    The empirical polynomial is intentionally not clipped or forced positive.
    If used outside its practical calibration range it can become negative; a
    future solver adapter must reject such a state rather than silently alter
    the source equation.
    """

    return _cubic(_phi_eta(phi, eta), _FRICTION_COEFFICIENT_POLYNOMIAL)


def wall_heat_coefficient_raw(phi: ArrayLike, eta: ArrayLike) -> NDArray[np.float64]:
    """Return the unmodified teacher Eq. (11.26) wall-heat coefficient.

    ``q = 0.0009 + 0.001125 z + 0.00594 z^2 - 0.00469 z^3``
    with ``z = phi*eta``.

    This function returns only the source correlation.  It does not claim that
    the dimensionless/empirical coefficient is already a wall heat flux in
    W/m^2 and therefore does not feed the generic wall-heat source directly.
    """

    return _cubic(_phi_eta(phi, eta), _WALL_HEAT_COEFFICIENT_POLYNOMIAL)


def darcy_friction_factor_from_teacher_f(teacher_f: ArrayLike) -> NDArray[np.float64]:
    """Map teacher wall coefficient ``f`` to the repo Darcy convention.

    Teacher Eq. (11.38) contributes, after division by area,

    ``S_m = -0.5*rho*u^2*(4*f/D_e)``.

    The existing generic wall source uses

    ``S_m = -0.5*f_D*rho*u*|u|/D_h``.

    For the teacher's forward-flow convention (``u >= 0``) and ``D_h=D_e`` the
    expressions are identical when ``f_D = 4*f``.  Negative empirical ``f`` is
    rejected here instead of turning it into nonphysical thrust.
    """

    coefficient = np.asarray(teacher_f, dtype=float)
    if not np.all(np.isfinite(coefficient)) or np.any(coefficient < 0.0):
        raise ValueError("teacher_f must be finite and nonnegative before Darcy mapping")
    return np.asarray(4.0 * coefficient, dtype=float)
