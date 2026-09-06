"""Generic, single-step time integration methods."""

from collections.abc import Callable

import numpy as np
from numpy.typing import ArrayLike, NDArray


def _finite_state(name: str, value: ArrayLike, shape: tuple[int, ...] | None = None) -> NDArray[np.float64]:
    """Convert a state to floats and require finite values and an optional shape."""
    array = np.asarray(value, dtype=float)
    if shape is not None and array.shape != shape:
        raise ValueError("rhs output must have the same shape as the state")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    return array


def ssp_rk3_step(U: ArrayLike, dt: float, rhs: Callable[[NDArray[np.float64]], ArrayLike]) -> NDArray[np.float64]:
    """Advance dU/dt=rhs(U) by one positive scalar dt with third-order SSP-RK3."""
    U0 = _finite_state("state", U)
    timestep = np.asarray(dt, dtype=float)
    if timestep.ndim != 0 or not np.isfinite(timestep) or timestep <= 0.0:
        raise ValueError("dt must be a finite and strictly positive scalar")

    k1 = _finite_state("rhs output", rhs(U0), U0.shape)
    stage1 = _finite_state("stage1", U0 + timestep * k1)
    k2 = _finite_state("rhs output", rhs(stage1), U0.shape)
    stage2 = _finite_state("stage2", 0.75 * U0 + 0.25 * (stage1 + timestep * k2))
    k3 = _finite_state("rhs output", rhs(stage2), U0.shape)
    return _finite_state("U_next", (1.0 / 3.0) * U0 + (2.0 / 3.0) * (stage2 + timestep * k3))
