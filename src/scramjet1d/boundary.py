"""Boundary treatment for the baseline constant-area Euler solver."""

import numpy as np
from numpy.typing import ArrayLike, NDArray


def transmissive_ghost_cells(U: ArrayLike) -> NDArray[np.float64]:
    """Return a new state array with zero-gradient ghost cells on the cell axis."""
    states = np.asarray(U, dtype=float)
    if states.ndim < 2 or states.shape[-1] != 3 or states.shape[-2] < 1:
        raise ValueError("U must have shape (..., N, 3) with at least one cell")
    if not np.all(np.isfinite(states)):
        raise ValueError("U must be finite")
    return np.concatenate((states[..., :1, :], states, states[..., -1:, :]), axis=-2)
