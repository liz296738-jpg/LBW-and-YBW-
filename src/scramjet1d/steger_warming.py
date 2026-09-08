"""Raw single-state Steger-Warming Euler flux vector splitting."""

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import GasProperties
from .gas import speed_of_sound
from .state import conservative_to_primitive


def euler_characteristic_speeds(U: ArrayLike, gas: GasProperties) -> NDArray[np.float64]:
    """Return Euler eigenvalues ``[u-a, u, u+a]`` [m/s] for U[..., 3] in SI units."""
    states = np.asarray(U, dtype=float)
    if states.ndim == 0 or states.shape[-1] != 3:
        raise ValueError("U last dimension must have length 3")
    primitive = conservative_to_primitive(states, gas)
    sound_speed = speed_of_sound(primitive.T, gas)
    return np.stack((primitive.u - sound_speed, primitive.u, primitive.u + sound_speed), axis=-1)


def _split_eigenvalues(eigenvalues: NDArray[np.float64]) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return raw positive and negative parts of Euler eigenvalues [m/s]."""
    return (
        0.5 * (eigenvalues + np.abs(eigenvalues)),
        0.5 * (eigenvalues - np.abs(eigenvalues)),
    )


def steger_warming_split_flux(
    U: ArrayLike, gas: GasProperties
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return raw Steger-Warming ``F_plus, F_minus`` for U[..., 3] in SI units.

    This is a single-state mathematical split, not a two-state interface flux.
    Eigenvalue splitting is intentionally unsmoothed in P5.1.
    """
    states = np.asarray(U, dtype=float)
    if states.ndim == 0 or states.shape[-1] != 3:
        raise ValueError("U last dimension must have length 3")
    primitive = conservative_to_primitive(states, gas)
    rho, u, p = primitive.rho, primitive.u, primitive.p
    a = speed_of_sound(primitive.T, gas)
    H = (states[..., 2] + p) / rho
    lambda_plus, lambda_minus = _split_eigenvalues(euler_characteristic_speeds(states, gas))

    def split_flux(eigenvalues: NDArray[np.float64]) -> NDArray[np.float64]:
        lambda_1, lambda_2, lambda_3 = (
            eigenvalues[..., 0], eigenvalues[..., 1], eigenvalues[..., 2]
        )
        mass = lambda_1 + 2.0 * (gas.gamma - 1.0) * lambda_2 + lambda_3
        momentum = (u - a) * lambda_1 + 2.0 * (gas.gamma - 1.0) * u * lambda_2 + (u + a) * lambda_3
        energy = (H - u * a) * lambda_1 + (gas.gamma - 1.0) * u**2 * lambda_2 + (H + u * a) * lambda_3
        return (rho / (2.0 * gas.gamma))[..., np.newaxis] * np.stack((mass, momentum, energy), axis=-1)

    return split_flux(lambda_plus), split_flux(lambda_minus)
