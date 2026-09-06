"""Primitive and conservative state conversions for P2."""

from typing import NamedTuple

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import GasProperties
from .gas import _require_finite, _require_positive, mach_number, temperature_from_density_pressure


class PrimitiveVariables(NamedTuple):
    """Primitive fields: rho [kg/m^3], u [m/s], p [Pa], T [K], and Mach [-]."""

    rho: NDArray[np.float64]
    u: NDArray[np.float64]
    p: NDArray[np.float64]
    T: NDArray[np.float64]
    Mach: NDArray[np.float64]


def primitive_to_conservative(
    rho: ArrayLike, u: ArrayLike, p: ArrayLike, gas: GasProperties
) -> NDArray[np.float64]:
    """Return U=[rho, rho*u, rho*E] from primitive inputs in SI units."""
    density, velocity, pressure = np.broadcast_arrays(
        _require_positive("rho", rho), _require_finite("u", u), _require_positive("p", p)
    )
    specific_energy = pressure / (density * (gas.gamma - 1.0)) + velocity**2 / 2.0
    return np.stack((density, density * velocity, density * specific_energy), axis=-1)


def conservative_to_primitive(U: ArrayLike, gas: GasProperties) -> PrimitiveVariables:
    """Return primitive variables from U=[rho, rho*u, rho*E] in SI units."""
    conservative = np.asarray(U, dtype=float)
    if conservative.ndim == 0 or conservative.shape[-1] != 3:
        raise ValueError("U last dimension must have length 3")

    rho = _require_positive("rho", conservative[..., 0])
    _require_finite("U", conservative)
    momentum = conservative[..., 1]
    rho_E = conservative[..., 2]
    u = momentum / rho
    p = (gas.gamma - 1.0) * (rho_E - momentum**2 / (2.0 * rho))
    p = _require_positive("p", p)
    T = temperature_from_density_pressure(rho, p, gas)
    return PrimitiveVariables(rho=rho, u=u, p=p, T=T, Mach=mach_number(u, T, gas))
