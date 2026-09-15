"""Teacher-reference convergence compatibility tests."""

import numpy as np
import pytest

from scramjet1d.config import GasProperties
from scramjet1d.convergence import max_relative_density_change
from scramjet1d.state import primitive_to_conservative


def _state(rho: np.ndarray) -> np.ndarray:
    gas = GasProperties()
    u = np.full_like(rho, 600.0, dtype=float)
    p = np.full_like(rho, 101325.0, dtype=float)
    return primitive_to_conservative(rho, u, p, gas)


def test_max_relative_density_change_matches_teacher_equation() -> None:
    gas = GasProperties()
    previous = _state(np.array([1.0, 0.8, 1.2]))
    current = _state(np.array([1.001, 0.7996, 1.1988]))

    value = max_relative_density_change(previous, current, gas)

    assert value == pytest.approx(1.0e-3, rel=0.0, abs=1.0e-14)


def test_identical_states_have_zero_density_change() -> None:
    gas = GasProperties()
    state = _state(np.array([1.0, 0.9]))

    assert max_relative_density_change(state, state.copy(), gas) == 0.0


def test_density_change_requires_matching_conservative_shapes() -> None:
    gas = GasProperties()
    previous = _state(np.array([1.0, 0.9]))
    current = _state(np.array([1.0]))

    with pytest.raises(ValueError, match="same shape"):
        max_relative_density_change(previous, current, gas)


def test_density_change_rejects_nonphysical_previous_density() -> None:
    gas = GasProperties()
    previous = _state(np.array([1.0, 0.9]))
    current = previous.copy()
    previous[0, 0] = -1.0

    with pytest.raises(ValueError):
        max_relative_density_change(previous, current, gas)
