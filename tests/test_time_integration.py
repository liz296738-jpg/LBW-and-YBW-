"""Tests for generic SSP-RK3 time integration."""

import math

import numpy as np
import pytest

import scramjet1d.time_integration as time_integration


def test_zero_and_constant_rhs() -> None:
    """Zero RHS preserves state and constant RHS advances exactly."""
    U = np.array([1.0, 2.0, 3.0])
    np.testing.assert_allclose(time_integration.ssp_rk3_step(U, 0.2, lambda state: np.zeros_like(state)), U)
    np.testing.assert_allclose(time_integration.ssp_rk3_step(U, 0.2, lambda state: np.array([4.0, 5.0, 6.0])), [1.8, 3.0, 4.2])


def test_linear_ode_matches_ssp_rk3_stability_polynomial() -> None:
    """One linear ODE step follows R(z)=1+z+z^2/2+z^3/6."""
    value, rate, dt = np.array([1.5]), -2.0, 0.1
    z = rate * dt
    expected = (1.0 + z + z**2 / 2.0 + z**3 / 6.0) * value
    np.testing.assert_allclose(time_integration.ssp_rk3_step(value, dt, lambda state: rate * state), expected, rtol=1e-12)


def test_linear_decay_has_third_order_global_convergence() -> None:
    """Halving dt for y'=-y produces observed order greater than 2.7."""
    errors = []
    for dt in (0.1, 0.05, 0.025):
        value = np.array([1.0])
        for _ in range(round(1.0 / dt)):
            value = time_integration.ssp_rk3_step(value, dt, lambda state: -state)
        errors.append(abs(value[0] - math.exp(-1.0)))
    assert math.log(errors[0] / errors[1], 2.0) > 2.7
    assert math.log(errors[1] / errors[2], 2.0) > 2.7


def test_arbitrary_shape_input_is_not_modified_and_rhs_is_called_three_times() -> None:
    """RK3 preserves arbitrary shape, caller input, and exactly three RHS calls."""
    U = np.ones((2, 4, 3))
    original = U.copy()
    calls = 0

    def rhs(state: np.ndarray) -> np.ndarray:
        nonlocal calls
        calls += 1
        return -0.5 * state

    result = time_integration.ssp_rk3_step(U, 0.1, rhs)
    assert result.shape == U.shape
    np.testing.assert_allclose(U, original)
    assert calls == 3


@pytest.mark.parametrize("dt", [0.0, -0.1, np.nan, np.inf, np.array([0.1, 0.2])])
def test_rejects_invalid_dt(dt: object) -> None:
    """Only finite positive scalar dt is accepted."""
    with pytest.raises(ValueError):
        time_integration.ssp_rk3_step(np.ones(2), dt, lambda state: state)


@pytest.mark.parametrize("U", [np.array([np.nan]), np.array([np.inf])])
def test_rejects_nonfinite_state(U: np.ndarray) -> None:
    """Initial state must be finite."""
    with pytest.raises(ValueError):
        time_integration.ssp_rk3_step(U, 0.1, lambda state: state)


@pytest.mark.parametrize(
    "rhs",
    [
        lambda state: np.zeros((4,)),
        lambda state: np.full_like(state, np.nan),
        lambda state: np.full_like(state, np.inf),
    ],
)
def test_rejects_bad_rhs_output(rhs: object) -> None:
    """RHS output must preserve shape and be finite at every stage."""
    with pytest.raises(ValueError):
        time_integration.ssp_rk3_step(np.ones((2, 3)), 0.1, rhs)
