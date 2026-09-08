"""Tests for raw single-state Steger-Warming flux vector splitting."""

import math

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.config import GasProperties
from scramjet1d.flux import euler_flux
from scramjet1d.state import primitive_to_conservative
from scramjet1d.steger_warming import euler_characteristic_speeds, steger_warming_split_flux


GAS = GasProperties()


def _state(rho: object, u: object, p: object) -> np.ndarray:
    return primitive_to_conservative(rho, u, p, GAS)


def test_characteristic_speeds_match_independent_hand_calculation() -> None:
    state = _state(1.2, 300.0, 100_000.0)
    a = math.sqrt(GAS.gamma * 100_000.0 / 1.2)
    assert_allclose(euler_characteristic_speeds(state, GAS), [300.0 - a, 300.0, 300.0 + a])


def test_negative_velocity_characteristic_speeds_preserve_order() -> None:
    state = _state(1.0, -400.0, 100_000.0)
    a = math.sqrt(GAS.gamma * 100_000.0)
    assert_allclose(euler_characteristic_speeds(state, GAS), [-400.0 - a, -400.0, -400.0 + a])


@pytest.mark.parametrize("rho,u,p", [(1.0, 0.0, 100_000.0), (1.0, 100.0, 100_000.0), (1.0, -100.0, 100_000.0), (1.0, 800.0, 100_000.0), (1.0, -800.0, 100_000.0)])
def test_split_flux_reconstructs_euler_flux(rho: float, u: float, p: float) -> None:
    state = _state(rho, u, p)
    positive, negative = steger_warming_split_flux(state, GAS)
    assert_allclose(positive + negative, euler_flux(state, GAS), rtol=1e-12, atol=1e-10)


def test_split_flux_matches_independent_scalar_closed_form() -> None:
    rho, u, p = 1.2, 150.0, 100_000.0
    state = _state(rho, u, p)
    a = math.sqrt(GAS.gamma * p / rho)
    H = (state[2] + p) / rho
    eigenvalues = np.array([u - a, u, u + a])
    plus = 0.5 * (eigenvalues + np.abs(eigenvalues))
    minus = 0.5 * (eigenvalues - np.abs(eigenvalues))
    def closed(lam: np.ndarray) -> np.ndarray:
        return rho / (2.0 * GAS.gamma) * np.array([
            lam[0] + 2.0 * (GAS.gamma - 1.0) * lam[1] + lam[2],
            (u - a) * lam[0] + 2.0 * (GAS.gamma - 1.0) * u * lam[1] + (u + a) * lam[2],
            (H - u * a) * lam[0] + (GAS.gamma - 1.0) * u**2 * lam[1] + (H + u * a) * lam[2],
        ])
    actual_plus, actual_minus = steger_warming_split_flux(state, GAS)
    assert_allclose(actual_plus, closed(plus))
    assert_allclose(actual_minus, closed(minus))


def test_static_state_has_exact_split_components() -> None:
    rho, p = 1.2, 100_000.0
    state = _state(rho, 0.0, p)
    a = math.sqrt(GAS.gamma * p / rho)
    H = (state[2] + p) / rho
    positive, negative = steger_warming_split_flux(state, GAS)
    assert_allclose(positive, [rho * a / (2 * GAS.gamma), p / 2, rho * H * a / (2 * GAS.gamma)])
    assert_allclose(negative, [-rho * a / (2 * GAS.gamma), p / 2, -rho * H * a / (2 * GAS.gamma)])


@pytest.mark.parametrize("velocity,positive_is_flux", [(800.0, True), (-800.0, False)])
def test_supersonic_directionality(velocity: float, positive_is_flux: bool) -> None:
    state = _state(1.0, velocity, 100_000.0)
    positive, negative = steger_warming_split_flux(state, GAS)
    flux = euler_flux(state, GAS)
    if positive_is_flux:
        assert_allclose(positive, flux, rtol=1e-13, atol=1e-10)
        assert_allclose(negative, 0.0, atol=1e-12)
    else:
        assert_allclose(positive, 0.0, atol=1e-12)
        assert_allclose(negative, flux, rtol=1e-13, atol=1e-10)


@pytest.mark.parametrize("sign", [1.0, -1.0])
def test_sonic_states_are_finite_and_reconstruct_flux(sign: float) -> None:
    rho, p = 1.0, 100_000.0
    a = math.sqrt(GAS.gamma * p / rho)
    state = _state(rho, sign * a, p)
    speeds = euler_characteristic_speeds(state, GAS)
    positive, negative = steger_warming_split_flux(state, GAS)
    assert np.all(np.isfinite(positive)) and np.all(np.isfinite(negative))
    assert_allclose(speeds[0 if sign > 0 else 2], 0.0, atol=1e-12)
    assert_allclose(positive + negative, euler_flux(state, GAS))


def test_vectorized_and_batched_states_preserve_shape_and_input() -> None:
    states = _state(np.ones((2, 4)), np.array([[-800., -100., 0., 100.], [800., -200., 200., 0.]]), np.full((2, 4), 100_000.0))
    original = states.copy()
    positive, negative = steger_warming_split_flux(states, GAS)
    assert positive.shape == negative.shape == (2, 4, 3)
    assert_allclose(positive + negative, euler_flux(states, GAS))
    assert_allclose(states, original)


@pytest.mark.parametrize("bad", [np.array(1.0), np.ones((2, 4)), np.array([[np.nan, 0., 1.], [1., 0., 1.]]), np.array([[0., 0., 1.], [1., 0., 1.]]), np.array([[1., 0., -1.], [1., 0., 1.]])])
def test_split_rejects_invalid_states(bad: np.ndarray) -> None:
    with pytest.raises(ValueError):
        steger_warming_split_flux(bad, GAS)
