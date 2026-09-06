"""Physical and numerical fluxes for the 1D Euler equations."""

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import GasProperties
from .gas import speed_of_sound
from .state import conservative_to_primitive


def euler_flux(U: ArrayLike, gas: GasProperties) -> NDArray[np.float64]:
    """Return 1D Euler physical flux F(U) for U=[rho, rho*u, rho*E] in SI units."""
    conservative = np.asarray(U, dtype=float)
    primitive = conservative_to_primitive(conservative, gas)

    rho = primitive.rho
    u = primitive.u
    p = primitive.p
    rho_E = conservative[..., 2]

    mass_flux = rho * u
    momentum_flux = rho * u**2 + p
    energy_flux = u * (rho_E + p)
    return np.stack((mass_flux, momentum_flux, energy_flux), axis=-1)


def rusanov_flux(
    U_left: ArrayLike, U_right: ArrayLike, gas: GasProperties
) -> NDArray[np.float64]:
    """Return the 1D Rusanov interface flux for left and right SI conservative states."""
    left = np.asarray(U_left, dtype=float)
    right = np.asarray(U_right, dtype=float)
    if left.ndim == 0 or left.shape[-1] != 3:
        raise ValueError("U_left last dimension must have length 3")
    if right.ndim == 0 or right.shape[-1] != 3:
        raise ValueError("U_right last dimension must have length 3")
    left, right = np.broadcast_arrays(left, right)

    primitive_left = conservative_to_primitive(left, gas)
    primitive_right = conservative_to_primitive(right, gas)
    flux_left = euler_flux(left, gas)
    flux_right = euler_flux(right, gas)

    wave_speed_left = np.abs(primitive_left.u) + speed_of_sound(primitive_left.T, gas)
    wave_speed_right = np.abs(primitive_right.u) + speed_of_sound(primitive_right.T, gas)
    alpha = np.maximum(wave_speed_left, wave_speed_right)

    return 0.5 * (flux_left + flux_right) - 0.5 * alpha[..., np.newaxis] * (right - left)
