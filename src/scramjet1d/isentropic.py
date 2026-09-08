"""Analytical isentropic quasi-one-dimensional reference utilities."""

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import GasProperties
from .state import PrimitiveVariables
from .validation import require_positive_scalar


def area_mach_ratio(mach: ArrayLike, gas: GasProperties) -> NDArray[np.float64]:
    """Return isentropic area ratio ``A/A*`` for positive Mach number(s) [-]."""
    M = np.asarray(mach, dtype=float)
    if not np.all(np.isfinite(M)) or not np.all(M > 0.0):
        raise ValueError("mach must be finite and strictly positive")
    factor = 2.0 / (gas.gamma + 1.0) * (1.0 + (gas.gamma - 1.0) * M**2 / 2.0)
    return (1.0 / M) * factor ** ((gas.gamma + 1.0) / (2.0 * (gas.gamma - 1.0)))


def _branch_name(branch: object) -> str:
    if branch not in ("subsonic", "supersonic"):
        raise ValueError("branch must be 'subsonic' or 'supersonic'")
    return str(branch)


def mach_from_area_ratio(
    area_ratio: ArrayLike, gas: GasProperties, branch: str
) -> NDArray[np.float64]:
    """Invert ``A/A*`` with bisection on the requested isentropic branch."""
    selected_branch = _branch_name(branch)
    ratios = np.asarray(area_ratio, dtype=float)
    if not np.all(np.isfinite(ratios)) or not np.all(ratios >= 1.0):
        raise ValueError("area_ratio must be finite and greater than or equal to one")

    result = np.empty_like(ratios, dtype=float)
    for index, target in np.ndenumerate(ratios):
        if target == 1.0:
            result[index] = 1.0
            continue
        if selected_branch == "subsonic":
            low = np.finfo(float).eps
            high = 1.0
            for _ in range(100):
                mid = 0.5 * (low + high)
                if area_mach_ratio(mid, gas) > target:
                    low = mid
                else:
                    high = mid
            result[index] = 0.5 * (low + high)
        else:
            low = 1.0
            high = 2.0
            expansions = 0
            while area_mach_ratio(high, gas) < target:
                high *= 2.0
                expansions += 1
                if expansions >= 100:
                    raise RuntimeError("could not bracket supersonic Mach solution")
            for _ in range(100):
                mid = 0.5 * (low + high)
                if area_mach_ratio(mid, gas) < target:
                    low = mid
                else:
                    high = mid
            result[index] = 0.5 * (low + high)
    return result


def isentropic_state_from_stagnation(
    mach: ArrayLike,
    stagnation_pressure: object,
    stagnation_temperature: object,
    gas: GasProperties,
) -> PrimitiveVariables:
    """Return SI primitive state(s) from Mach [-], stagnation pressure [Pa], and T0 [K]."""
    M = np.asarray(mach, dtype=float)
    if not np.all(np.isfinite(M)) or not np.all(M > 0.0):
        raise ValueError("mach must be finite and strictly positive")
    p0 = require_positive_scalar("stagnation_pressure", stagnation_pressure)
    T0 = require_positive_scalar("stagnation_temperature", stagnation_temperature)
    temperature_ratio = 1.0 + (gas.gamma - 1.0) * M**2 / 2.0
    temperature = T0 / temperature_ratio
    pressure = p0 * (temperature / T0) ** (gas.gamma / (gas.gamma - 1.0))
    density = pressure / (gas.R * temperature)
    velocity = M * np.sqrt(gas.gamma * gas.R * temperature)
    return PrimitiveVariables(rho=density, u=velocity, p=pressure, T=temperature, Mach=M)


def isentropic_nozzle_reference(
    area: ArrayLike,
    reference_area: object,
    reference_mach: object,
    stagnation_pressure: object,
    stagnation_temperature: object,
    gas: GasProperties,
    branch: str,
) -> PrimitiveVariables:
    """Return a branch-preserving isentropic nozzle reference for 1D area [m^2]."""
    selected_branch = _branch_name(branch)
    areas = np.asarray(area, dtype=float)
    if areas.ndim != 1 or areas.size < 1 or not np.all(np.isfinite(areas)) or not np.all(areas > 0.0):
        raise ValueError("area must be a nonempty one-dimensional array of finite positive values")
    A_ref = require_positive_scalar("reference_area", reference_area)
    M_ref = np.asarray(reference_mach, dtype=float)
    if M_ref.ndim != 0 or not np.isfinite(M_ref) or M_ref <= 0.0:
        raise ValueError("reference_mach must be a finite and strictly positive scalar")
    reference_mach_value = float(M_ref)
    if selected_branch == "subsonic" and reference_mach_value > 1.0:
        raise ValueError("subsonic reference_mach must not exceed one")
    if selected_branch == "supersonic" and reference_mach_value < 1.0:
        raise ValueError("supersonic reference_mach must be at least one")

    critical_area = A_ref / area_mach_ratio(reference_mach_value, gas)
    local_ratio = areas / critical_area
    mach = mach_from_area_ratio(local_ratio, gas, selected_branch)
    return isentropic_state_from_stagnation(mach, stagnation_pressure, stagnation_temperature, gas)
