"""Physical fluxes for approved governing equations."""

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import GasProperties
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
