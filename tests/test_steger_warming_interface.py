"""Tests for the two-state Steger-Warming interface numerical flux."""

import math

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.config import GasProperties
from scramjet1d.flux import euler_flux
from scramjet1d.state import primitive_to_conservative
from scramjet1d.steger_warming import steger_warming_flux, steger_warming_split_flux


GAS = GasProperties()


def state(rho: object, u: object, p: object) -> np.ndarray:
    return primitive_to_conservative(rho, u, p, GAS)


@pytest.mark.parametrize("u", [0.0, 100.0, -100.0, 800.0, -800.0])
def test_equal_state_flux_is_consistent(u: float) -> None:
    U = state(1.0, u, 100_000.0)
    assert_allclose(steger_warming_flux(U, U, GAS), euler_flux(U, GAS), rtol=1e-12, atol=1e-10)


@pytest.mark.parametrize("sign", [1.0, -1.0])
def test_sonic_equal_state_flux_is_finite_and_consistent(sign: float) -> None:
    a = math.sqrt(GAS.gamma * 100_000.0)
    U = state(1.0, sign * a, 100_000.0)
    result = steger_warming_flux(U, U, GAS)
    assert np.all(np.isfinite(result))
    assert_allclose(result, euler_flux(U, GAS))


def test_right_supersonic_flux_uses_only_left_state() -> None:
    left = state(1.0, 900.0, 100_000.0)
    right_1 = state(0.8, 850.0, 80_000.0)
    right_2 = state(1.2, 1000.0, 120_000.0)
    expected = euler_flux(left, GAS)
    assert_allclose(steger_warming_flux(left, right_1, GAS), expected)
    assert_allclose(steger_warming_flux(left, right_2, GAS), expected)


def test_left_supersonic_flux_uses_only_right_state() -> None:
    left_1 = state(1.0, -900.0, 100_000.0)
    left_2 = state(0.8, -850.0, 80_000.0)
    right = state(0.7, -950.0, 90_000.0)
    expected = euler_flux(right, GAS)
    assert_allclose(steger_warming_flux(left_1, right, GAS), expected)
    assert_allclose(steger_warming_flux(left_2, right, GAS), expected)


def test_subsonic_interface_wires_left_positive_and_right_negative_parts() -> None:
    left, right = state(1.0, 100.0, 100_000.0), state(0.9, -80.0, 90_000.0)
    left_plus, _ = steger_warming_split_flux(left, GAS)
    _, right_minus = steger_warming_split_flux(right, GAS)
    assert_allclose(steger_warming_flux(left, right, GAS), left_plus + right_minus)


def test_static_equal_state_returns_hand_written_physical_flux() -> None:
    U = state(1.2, 0.0, 100_000.0)
    assert_allclose(steger_warming_flux(U, U, GAS), [0.0, 100_000.0, 0.0])


def test_vectorized_batched_and_broadcast_interfaces() -> None:
    right = state(np.ones(6), np.linspace(-800.0, 800.0, 6), np.full(6, 100_000.0))
    left = state(1.0, 100.0, 100_000.0)
    result = steger_warming_flux(left, right, GAS)
    assert result.shape == (6, 3)
    assert_allclose(result, np.stack([steger_warming_flux(left, item, GAS) for item in right]))
    batched = steger_warming_flux(np.stack((right[:4], right[:4])), np.stack((right[:4], right[:4])), GAS)
    assert batched.shape == (2, 4, 3)


def test_batched_left_single_right_broadcasts() -> None:
    left = state(np.ones(4), np.linspace(-200.0, 200.0, 4), np.full(4, 100_000.0))
    right = state(1.1, -50.0, 90_000.0)
    assert_allclose(steger_warming_flux(left, right, GAS), np.stack([steger_warming_flux(item, right, GAS) for item in left]))


def test_inputs_are_not_modified_and_mixed_regimes_are_finite() -> None:
    left, right = state(1.0, 100.0, 100_000.0), state(0.9, 800.0, 90_000.0)
    left_original, right_original = left.copy(), right.copy()
    result = steger_warming_flux(left, right, GAS)
    assert np.all(np.isfinite(result))
    assert_allclose(left, left_original)
    assert_allclose(right, right_original)


@pytest.mark.parametrize("left,right", [(np.array(1.0), state(1., 0., 1e5)), (np.ones(4), state(1., 0., 1e5)), (state(1., 0., 1e5), np.ones(4)), (np.ones((2, 3)), np.ones((4, 3))), (np.array([[np.nan, 0., 1.], [1., 0., 1.]]), state(np.ones(2), np.zeros(2), np.ones(2)*1e5))])
def test_interface_rejects_invalid_shapes_or_states(left: np.ndarray, right: np.ndarray) -> None:
    with pytest.raises(ValueError):
        steger_warming_flux(left, right, GAS)
