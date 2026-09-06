"""Ideal, calorically perfect gas relations for P2."""

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import GasProperties
from .validation import require_finite, require_positive


def pressure_from_density_temperature(
    rho: ArrayLike, T: ArrayLike, gas: GasProperties
) -> NDArray[np.float64]:
    """Return pressure [Pa] from density rho [kg/m^3] and temperature T [K]."""
    return require_positive("rho", rho) * gas.R * require_positive("T", T)


def temperature_from_density_pressure(
    rho: ArrayLike, p: ArrayLike, gas: GasProperties
) -> NDArray[np.float64]:
    """Return temperature [K] from density rho [kg/m^3] and pressure p [Pa]."""
    return require_positive("p", p) / (require_positive("rho", rho) * gas.R)


def speed_of_sound(T: ArrayLike, gas: GasProperties) -> NDArray[np.float64]:
    """Return sound speed [m/s] from temperature T [K]."""
    return np.sqrt(gas.gamma * gas.R * require_positive("T", T))


def specific_internal_energy(
    p: ArrayLike, rho: ArrayLike, gas: GasProperties
) -> NDArray[np.float64]:
    """Return specific internal energy [J/kg] from pressure p [Pa] and rho [kg/m^3]."""
    return require_positive("p", p) / (require_positive("rho", rho) * (gas.gamma - 1.0))


def specific_total_energy(
    rho: ArrayLike, u: ArrayLike, p: ArrayLike, gas: GasProperties
) -> NDArray[np.float64]:
    """Return specific total energy [J/kg]; velocity u is in m/s."""
    velocity = require_finite("u", u)
    return specific_internal_energy(p, rho, gas) + velocity**2 / 2.0


def mach_number(u: ArrayLike, T: ArrayLike, gas: GasProperties) -> NDArray[np.float64]:
    """Return signed Mach number from velocity u [m/s] and temperature T [K]."""
    return require_finite("u", u) / speed_of_sound(T, gas)
