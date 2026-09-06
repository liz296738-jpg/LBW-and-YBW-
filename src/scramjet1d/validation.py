"""Small, shared validation helpers for numeric inputs."""

import numpy as np
from numpy.typing import ArrayLike, NDArray


def require_positive(name: str, value: ArrayLike) -> NDArray[np.float64]:
    """Return value as floats after requiring finite, strictly positive entries."""
    array = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(array) & (array > 0.0)):
        raise ValueError(f"{name} must be finite and strictly positive")
    return array


def require_finite(name: str, value: ArrayLike) -> NDArray[np.float64]:
    """Return value as floats after requiring all entries to be finite."""
    array = np.asarray(value, dtype=float)
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    return array
