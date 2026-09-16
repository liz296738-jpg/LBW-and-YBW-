"""Source-defined Cao combustion-mode criteria with explicit evidence limits.

The criteria in this module are transcribed from Cao Ruifeng's doctoral
reference supplied by the teacher. They are kept separate from project-defined
solver admissibility guards and from the incomplete Cao Case 2 reproduction.

Two levels are exposed:

1. the later-dissertation two-mode thermal-throat criterion, based on Eq. (3-2)
   and Section 4.2.1;
2. the more detailed Table 3-1 criteria, which require isolator/shock-train state
   variables that are not currently produced by the accepted integrated solver.

No numerical sonic tolerance is sourced by the dissertation. Callers must pass
one explicitly when applying the thermal-throat criterion to floating-point
results.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from typing import Iterable

import numpy as np


class ThermalThroatState(str, Enum):
    """Two-mode branch relative to Cao's source-defined sonic boundary."""

    SCRAM_SIDE = "SCRAM_SIDE"
    CRITICAL_TRANSITION_BAND = "CRITICAL_TRANSITION_BAND"
    RAM_SIDE = "RAM_SIDE"


class CaoTable31State(str, Enum):
    """Detailed Table 3-1 state when all required source variables are known."""

    NO_SHOCK_SCRAM = "NO_SHOCK_SCRAM"
    OBLIQUE_SHOCK_SCRAM = "OBLIQUE_SHOCK_SCRAM"
    RAM = "RAM"
    BOUNDARY_OR_UNCLASSIFIED = "BOUNDARY_OR_UNCLASSIFIED"


@dataclass(frozen=True)
class ThermalThroatClassification:
    state: ThermalThroatState
    minimum_mach: float
    sonic_tolerance: float


@dataclass(frozen=True)
class CaoTable31Classification:
    state: CaoTable31State
    ma_s: float
    ma_2: float
    ma_3m: float
    ma_2min: float


def _positive_finite(name: str, value: object) -> float:
    scalar = float(value)
    if not isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"{name} must be finite and strictly positive")
    return scalar


def _mach_profile(value: Iterable[float] | np.ndarray) -> np.ndarray:
    if isinstance(value, np.ndarray):
        mach = np.asarray(value, dtype=float)
    else:
        try:
            mach = np.asarray(tuple(value), dtype=float)
        except TypeError as error:
            raise ValueError(
                "mach_profile must be a nonempty one-dimensional profile"
            ) from error
    if mach.ndim != 1 or mach.size < 1:
        raise ValueError("mach_profile must be a nonempty one-dimensional profile")
    if not np.all(np.isfinite(mach)) or np.any(mach <= 0.0):
        raise ValueError("mach_profile must be finite and strictly positive")
    return mach


def classify_thermal_throat(
    mach_profile: Iterable[float] | np.ndarray,
    *,
    sonic_tolerance: float,
) -> ThermalThroatClassification:
    """Apply Cao Eq. (3-2) to an admissible converged Mach profile.

    Source definition:
      * ``min(Ma(x)) > 1``: scram side;
      * ``min(Ma(x)) < 1``: ram side;
      * the transition boundary occurs at a critical thermal throat, ``Ma=1``.

    ``sonic_tolerance`` is deliberately mandatory because the dissertation does
    not prescribe a floating-point tolerance. The returned transition *band* is
    therefore a project numerical representation of the source's exact boundary,
    not an additional physical threshold.
    """

    mach = _mach_profile(mach_profile)
    tolerance = _positive_finite("sonic_tolerance", sonic_tolerance)
    if tolerance >= 1.0:
        raise ValueError("sonic_tolerance must be smaller than 1")

    minimum = float(np.min(mach))
    if minimum > 1.0 + tolerance:
        state = ThermalThroatState.SCRAM_SIDE
    elif minimum < 1.0 - tolerance:
        state = ThermalThroatState.RAM_SIDE
    else:
        state = ThermalThroatState.CRITICAL_TRANSITION_BAND
    return ThermalThroatClassification(state, minimum, tolerance)


def classify_cao_table_3_1(
    *,
    ma_s: float,
    ma_2: float,
    ma_3m: float,
    ma_2min: float,
) -> CaoTable31Classification:
    """Evaluate the strict inequalities transcribed from Cao Table 3-1.

    Equality cases, uncovered combinations, and mathematically overlapping
    combinations are returned as ``BOUNDARY_OR_UNCLASSIFIED`` rather than being
    forced into a combustion mode. The latter protects the code from treating
    the table's physically coupled variables as independent arbitrary numbers.
    """

    mas = _positive_finite("ma_s", ma_s)
    ma2 = _positive_finite("ma_2", ma_2)
    ma3m = _positive_finite("ma_3m", ma_3m)
    ma2min = _positive_finite("ma_2min", ma_2min)
    if ma2min >= ma3m:
        raise ValueError("ma_2min must be smaller than ma_3m")

    separation_threshold = 0.762 * ma2
    matches: list[CaoTable31State] = []
    if mas > separation_threshold:
        matches.append(CaoTable31State.NO_SHOCK_SCRAM)
    if ma2 > ma3m and mas < separation_threshold:
        matches.append(CaoTable31State.OBLIQUE_SHOCK_SCRAM)
    if ma2min < ma2 < ma3m:
        matches.append(CaoTable31State.RAM)

    state = (
        matches[0]
        if len(matches) == 1
        else CaoTable31State.BOUNDARY_OR_UNCLASSIFIED
    )
    return CaoTable31Classification(state, mas, ma2, ma3m, ma2min)
