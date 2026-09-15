"""Explicit combustion-efficiency policy for the teacher Chapter 11 model.

The teacher source provides two related pieces of information:

* Eq. (11.18) defines combustion efficiency from injected and residual fuel;
  as a physical efficiency it is bounded by 0--100 percent.
* Eq. (11.19) provides empirical mixing-efficiency correlations and the text
  approximates combustion efficiency by mixing efficiency.

Eq. (11.19) is intentionally kept untouched in :mod:`teacher_combustion`.
Some branches can return a raw value slightly above one near or beyond complete
mixing.  This module therefore makes the required modeling choice explicit:
when raw mixing efficiency is used as the combustion-efficiency surrogate, it
is saturated at unity.

That saturation is a *project adapter policy*, not a modification of Eq.
(11.19), and must be called explicitly by higher-level teacher-model code.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike, NDArray


def combustion_efficiency_from_fuel_mass_rates(
    injected_fuel_mass_rate: ArrayLike,
    residual_fuel_mass_rate: ArrayLike,
) -> NDArray[np.float64]:
    """Return fractional combustion efficiency from teacher Eq. (11.18).

    The source prints the result as a percentage,

    ``eta[%] = (m_fi - m_fr) / m_fi * 100%``.

    CFD composition equations use ``eta`` as a dimensionless fraction, so this
    function returns

    ``eta = (m_fi - m_fr) / m_fi``.

    Both inputs must be finite, ``m_fi > 0`` and ``0 <= m_fr <= m_fi``.
    Arrays are broadcast using NumPy semantics.
    """

    injected = np.asarray(injected_fuel_mass_rate, dtype=float)
    residual = np.asarray(residual_fuel_mass_rate, dtype=float)
    try:
        injected, residual = np.broadcast_arrays(injected, residual)
    except ValueError as error:
        raise ValueError("injected and residual fuel mass rates must broadcast together") from error

    if not np.all(np.isfinite(injected)) or np.any(injected <= 0.0):
        raise ValueError("injected_fuel_mass_rate must be finite and strictly positive")
    if not np.all(np.isfinite(residual)) or np.any(residual < 0.0):
        raise ValueError("residual_fuel_mass_rate must be finite and nonnegative")
    if np.any(residual > injected):
        raise ValueError("residual_fuel_mass_rate must not exceed injected_fuel_mass_rate")

    return np.asarray((injected - residual) / injected, dtype=float)


def combustion_efficiency_from_raw_mixing(
    raw_mixing_efficiency: ArrayLike,
) -> NDArray[np.float64]:
    """Map raw Eq. (11.19) mixing efficiency to physical ``eta`` in ``[0,1]``.

    This is the explicit project policy used when the teacher approximation
    ``eta ≈ eta_m`` is invoked:

    ``eta = min(eta_m_raw, 1)``.

    The raw correlation itself remains available separately and is never
    silently clipped.  Negative or non-finite raw values are rejected because
    they do not represent a physical mixing efficiency.
    """

    raw = np.asarray(raw_mixing_efficiency, dtype=float)
    if not np.all(np.isfinite(raw)):
        raise ValueError("raw_mixing_efficiency must be finite")
    if np.any(raw < 0.0):
        raise ValueError("raw_mixing_efficiency must be nonnegative")
    return np.asarray(np.minimum(raw, 1.0), dtype=float)
