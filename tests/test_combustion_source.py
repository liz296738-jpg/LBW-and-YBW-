"""Acceptance tests for the standalone P8.1 prescribed heat-release source."""

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from scramjet1d.config import GasProperties
from scramjet1d.source_terms import combustion_heat_release_source
from scramjet1d.state import primitive_to_conservative


GAS = GasProperties()


def _state(shape=(), rho=1.0, velocity=500.0, pressure=100_000.0):
    return primitive_to_conservative(
        np.full(shape, rho), np.full(shape, velocity), np.full(shape, pressure), GAS
    )


def test_heat_release_has_exact_energy_only_components() -> None:
    source = combustion_heat_release_source(_state(), 2.5e6, GAS)

    assert source[0] == 0.0
    assert source[1] == 0.0
    assert source[2] == 2.5e6


def test_zero_heat_release_is_an_exactly_zero_source() -> None:
    assert_array_equal(combustion_heat_release_source(_state((4,)), 0.0, GAS), 0.0)


def test_scalar_and_nonuniform_heat_release_broadcast_to_cells() -> None:
    cells = _state((5,))
    scalar = combustion_heat_release_source(cells, 1.0e6, GAS)
    array = combustion_heat_release_source(cells, np.linspace(0.0, 2.0e6, 5), GAS)

    assert_array_equal(scalar[:, :2], 0.0)
    assert_array_equal(scalar[:, 2], 1.0e6)
    assert_array_equal(array[:, :2], 0.0)
    assert_array_equal(array[:, 2], np.linspace(0.0, 2.0e6, 5))


def test_heat_release_is_independent_of_the_valid_thermodynamic_state() -> None:
    state_a = _state(rho=1.0, velocity=300.0, pressure=100_000.0)
    state_b = _state(rho=0.4, velocity=1500.0, pressure=50_000.0)

    assert_array_equal(
        combustion_heat_release_source(state_a, 1.25e6, GAS),
        combustion_heat_release_source(state_b, 1.25e6, GAS),
    )


def test_batched_states_preserve_shape_and_broadcast_cell_values() -> None:
    source = combustion_heat_release_source(_state((2, 4)), np.arange(1.0, 5.0), GAS)

    assert source.shape == (2, 4, 3)
    assert_array_equal(source[..., :2], 0.0)
    assert_array_equal(source[0, :, 2], np.arange(1.0, 5.0))
    assert_array_equal(source[1, :, 2], np.arange(1.0, 5.0))


@pytest.mark.parametrize("heat_release", [-1.0, np.array([0.0, -1.0])])
def test_negative_heat_release_is_rejected(heat_release) -> None:
    with pytest.raises(ValueError, match="finite and nonnegative"):
        combustion_heat_release_source(_state((2,)), heat_release, GAS)


@pytest.mark.parametrize("heat_release", [np.nan, np.inf, -np.inf])
def test_nonfinite_heat_release_is_rejected(heat_release: float) -> None:
    with pytest.raises(ValueError, match="finite and nonnegative"):
        combustion_heat_release_source(_state(), heat_release, GAS)


def test_nonbroadcastable_heat_release_is_rejected() -> None:
    with pytest.raises(ValueError, match="broadcast to the state shape"):
        combustion_heat_release_source(_state((12,)), np.ones(5), GAS)


@pytest.mark.parametrize(
    "invalid_state",
    [np.ones(4), np.array([np.nan, 1.0, 1.0]), np.array([-1.0, 0.0, 1.0]), np.array([1.0, 0.0, 0.0])],
)
def test_invalid_state_shape_or_physical_state_is_rejected(invalid_state: np.ndarray) -> None:
    with pytest.raises(ValueError):
        combustion_heat_release_source(invalid_state, 1.0, GAS)


def test_inputs_are_not_modified() -> None:
    state = _state((3,))
    heat_release = np.array([0.0, 1.0e6, 2.0e6])
    original_state = state.copy()
    original_heat_release = heat_release.copy()

    combustion_heat_release_source(state, heat_release, GAS)

    assert_allclose(state, original_state, rtol=0.0, atol=0.0)
    assert_array_equal(heat_release, original_heat_release)
