"""Acceptance tests for the independent P7.1 prescribed fuel source."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.config import GasProperties
from scramjet1d.source_terms import fuel_injection_source
from scramjet1d.state import primitive_to_conservative


GAS = GasProperties()


def _state(shape=()):
    return primitive_to_conservative(np.ones(shape), np.full(shape, 300.0), np.full(shape, 100_000.0), GAS)


def test_fuel_source_matches_hand_derived_scalar_mapping() -> None:
    source = fuel_injection_source(_state(), 2.0, 150.0, 1.2e6, GAS)
    assert_allclose(source, [2.0, 300.0, 2_400_000.0])


def test_zero_mass_injection_is_exactly_zero() -> None:
    assert_allclose(fuel_injection_source(_state(), 0.0, 500.0, 2e6, GAS), [0.0, 0.0, 0.0], rtol=0.0, atol=0.0)


def test_axial_velocity_controls_only_momentum_sign_and_magnitude() -> None:
    zero = fuel_injection_source(_state(), 2.0, 0.0, 1e6, GAS)
    reverse = fuel_injection_source(_state(), 2.0, -50.0, 1e6, GAS)
    doubled = fuel_injection_source(_state(), 2.0, 100.0, 1e6, GAS)
    assert zero[0] > 0.0 and zero[1] == 0.0 and zero[2] != 0.0
    assert reverse[0] > 0.0 and reverse[1] < 0.0
    assert_allclose(doubled, [2.0, 200.0, 2e6])


def test_mass_velocity_and_enthalpy_scaling_are_independent() -> None:
    base = fuel_injection_source(_state(), 1.0, 100.0, 1e6, GAS)
    assert_allclose(fuel_injection_source(_state(), 2.0, 100.0, 1e6, GAS), 2.0 * base)
    velocity = fuel_injection_source(_state(), 1.0, 200.0, 1e6, GAS)
    enthalpy = fuel_injection_source(_state(), 1.0, 100.0, 2e6, GAS)
    assert_allclose(velocity[[0, 2]], base[[0, 2]])
    assert_allclose(velocity[1], 2.0 * base[1])
    assert_allclose(enthalpy[:2], base[:2])
    assert_allclose(enthalpy[2], 2.0 * base[2])


def test_total_enthalpy_already_contains_injection_kinetic_energy() -> None:
    slow = fuel_injection_source(_state(), 1.0, 100.0, 1.2e6, GAS)
    fast = fuel_injection_source(_state(), 1.0, 1000.0, 1.2e6, GAS)
    assert slow[2] == fast[2]


def test_source_is_independent_of_valid_gas_state() -> None:
    state_a = primitive_to_conservative(0.5, 100.0, 50_000.0, GAS)
    state_b = primitive_to_conservative(2.0, 1200.0, 500_000.0, GAS)
    assert_allclose(fuel_injection_source(state_a, 1.0, -20.0, -1e5, GAS), fuel_injection_source(state_b, 1.0, -20.0, -1e5, GAS))


def test_vectorized_and_mixed_batch_broadcasting_preserve_state_shape() -> None:
    cells = _state((5,))
    source = fuel_injection_source(cells, np.arange(1.0, 6.0), np.full(5, 10.0), np.full(5, 100.0), GAS)
    assert source.shape == (5, 3)
    assert_allclose(source[3], [4.0, 40.0, 400.0])
    batch = _state((2, 5))
    mixed = fuel_injection_source(batch, np.arange(1.0, 6.0), 10.0, np.full((2, 5), 100.0), GAS)
    assert mixed.shape == (2, 5, 3)
    assert_allclose(mixed[1, 4], [5.0, 50.0, 500.0])


def test_inputs_are_not_modified() -> None:
    state = _state((2,)); mass = np.array([1.0, 2.0]); velocity = np.array([-3.0, 4.0]); enthalpy = np.array([-5.0, 6.0])
    originals = [value.copy() for value in (state, mass, velocity, enthalpy)]
    fuel_injection_source(state, mass, velocity, enthalpy, GAS)
    for actual, expected in zip((state, mass, velocity, enthalpy), originals): assert_allclose(actual, expected)


@pytest.mark.parametrize("mass_rate", [-1.0, np.nan, np.inf])
def test_invalid_mass_rate_is_rejected(mass_rate: float) -> None:
    with pytest.raises(ValueError): fuel_injection_source(_state(), mass_rate, 1.0, 1.0, GAS)


@pytest.mark.parametrize("velocity", [np.nan, np.inf, -np.inf])
def test_nonfinite_velocity_is_rejected_but_negative_finite_is_allowed(velocity: float) -> None:
    with pytest.raises(ValueError): fuel_injection_source(_state(), 1.0, velocity, 1.0, GAS)
    assert fuel_injection_source(_state(), 1.0, -1.0, 1.0, GAS)[1] < 0.0


@pytest.mark.parametrize("enthalpy", [np.nan, np.inf, -np.inf])
def test_nonfinite_enthalpy_is_rejected_but_negative_finite_is_allowed(enthalpy: float) -> None:
    with pytest.raises(ValueError): fuel_injection_source(_state(), 1.0, 1.0, enthalpy, GAS)
    assert fuel_injection_source(_state(), 1.0, 1.0, -1.0, GAS)[2] < 0.0


@pytest.mark.parametrize("parameter", [np.ones(3), np.ones((2, 3))])
def test_nonbroadcastable_parameters_are_rejected(parameter: np.ndarray) -> None:
    with pytest.raises(ValueError): fuel_injection_source(_state((2, 5)), parameter, 1.0, 1.0, GAS)


def test_nonbroadcastable_velocity_and_enthalpy_are_rejected() -> None:
    with pytest.raises(ValueError): fuel_injection_source(_state((2, 5)), 1.0, np.ones(3), 1.0, GAS)
    with pytest.raises(ValueError): fuel_injection_source(_state((2, 5)), 1.0, 1.0, np.ones(3), GAS)


@pytest.mark.parametrize("state", [np.array([np.nan, 1.0, 1.0]), np.array([np.inf, 1.0, 1.0]), np.array([-1.0, 0.0, 1.0]), np.array([1.0, 0.0, 0.0])])
def test_invalid_cfd_state_is_rejected(state: np.ndarray) -> None:
    with pytest.raises(ValueError): fuel_injection_source(state, 1.0, 1.0, 1.0, GAS)
