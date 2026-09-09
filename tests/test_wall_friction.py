"""Tests for the independent prescribed-Darcy wall-friction source model."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.config import GasProperties
from scramjet1d.source_terms import wall_friction_source
from scramjet1d.state import primitive_to_conservative


GAS = GasProperties()


def _state(rho: object, velocity: object, pressure: object = 100_000.0) -> np.ndarray:
    return primitive_to_conservative(rho, velocity, pressure, GAS)


def test_wall_friction_matches_independent_scalar_darcy_formula() -> None:
    source = wall_friction_source(_state(1.2, 300.0), 0.1, 0.02, GAS)
    assert_allclose(source, [0.0, -10_800.0, 0.0], rtol=0.0, atol=1e-10)


def test_wall_friction_reverses_sign_for_reverse_flow() -> None:
    source = wall_friction_source(_state(1.2, -300.0), 0.1, 0.02, GAS)
    assert source[1] == pytest.approx(10_800.0)
    assert source[1] * -300.0 < 0.0


def test_wall_friction_is_zero_for_zero_velocity_or_zero_darcy_factor() -> None:
    assert_allclose(wall_friction_source(_state(1.2, 0.0), 0.1, 0.02, GAS), 0.0, rtol=0.0, atol=0.0)
    assert_allclose(wall_friction_source(_state(1.2, 300.0), 0.1, 0.0, GAS), 0.0, rtol=0.0, atol=0.0)


def test_wall_friction_has_zero_mass_and_energy_sources() -> None:
    source = wall_friction_source(_state([0.8, 1.2, 1.6], [-300.0, 0.0, 500.0], [80_000.0, 100_000.0, 120_000.0]), [0.05, 0.1, 0.2], [0.01, 0.02, 0.03], GAS)
    assert_allclose(source[:, 0], 0.0, rtol=0.0, atol=0.0)
    assert_allclose(source[:, 2], 0.0, rtol=0.0, atol=0.0)


def test_wall_friction_opposes_each_nonzero_velocity() -> None:
    velocity = np.array([-500.0, -100.0, 0.0, 100.0, 500.0])
    source = wall_friction_source(_state(np.ones(5), velocity), 0.1, 0.02, GAS)
    assert np.all(source[velocity != 0.0, 1] * velocity[velocity != 0.0] < 0.0)
    assert source[2, 1] == 0.0


def test_wall_friction_scales_linearly_with_factor_and_density() -> None:
    baseline = wall_friction_source(_state(1.2, 300.0), 0.1, 0.02, GAS)[1]
    assert wall_friction_source(_state(1.2, 300.0), 0.1, 0.04, GAS)[1] == pytest.approx(2.0 * baseline)
    assert wall_friction_source(_state(2.4, 300.0), 0.1, 0.02, GAS)[1] == pytest.approx(2.0 * baseline)


def test_wall_friction_scales_quadratically_with_speed_and_inversely_with_diameter() -> None:
    baseline = wall_friction_source(_state(1.2, 300.0), 0.1, 0.02, GAS)[1]
    assert wall_friction_source(_state(1.2, 600.0), 0.1, 0.02, GAS)[1] == pytest.approx(4.0 * baseline)
    assert wall_friction_source(_state(1.2, 300.0), 0.2, 0.02, GAS)[1] == pytest.approx(0.5 * baseline)


def test_wall_friction_vectorized_cells_match_scalar_evaluations() -> None:
    state = _state([1.0, 1.1, 1.2, 1.3, 1.4], [-200.0, -100.0, 0.0, 100.0, 200.0])
    diameter = np.array([0.05, 0.06, 0.07, 0.08, 0.09])
    factor = np.array([0.01, 0.015, 0.02, 0.025, 0.03])
    result = wall_friction_source(state, diameter, factor, GAS)
    assert result.shape == (5, 3)
    assert_allclose(result, np.stack([wall_friction_source(cell, cell_diameter, cell_factor, GAS) for cell, cell_diameter, cell_factor in zip(state, diameter, factor)]))


def test_wall_friction_supports_scalar_and_batched_cell_broadcasting() -> None:
    state = np.stack((_state(np.ones(5), np.linspace(-200.0, 200.0, 5)), _state(np.full(5, 1.2), np.linspace(-100.0, 300.0, 5))))
    scalar = wall_friction_source(state[0], 0.1, 0.02, GAS)
    batched = wall_friction_source(state, np.linspace(0.05, 0.1, 5), 0.02, GAS)
    assert scalar.shape == (5, 3)
    assert batched.shape == (2, 5, 3)
    assert_allclose(batched[0], wall_friction_source(state[0], np.linspace(0.05, 0.1, 5), 0.02, GAS))


def test_wall_friction_single_state_and_inputs_are_unmodified() -> None:
    state = _state(1.2, 300.0)
    diameter, factor = np.array(0.1), np.array(0.02)
    original_state, original_diameter, original_factor = state.copy(), diameter.copy(), factor.copy()
    result = wall_friction_source(state, diameter, factor, GAS)
    assert result.shape == (3,)
    assert_allclose(state, original_state)
    assert_allclose(diameter, original_diameter)
    assert_allclose(factor, original_factor)


@pytest.mark.parametrize("diameter", [0.0, -0.1, np.nan, np.inf])
def test_wall_friction_rejects_invalid_hydraulic_diameter(diameter: float) -> None:
    with pytest.raises(ValueError):
        wall_friction_source(_state(1.0, 100.0), diameter, 0.02, GAS)


@pytest.mark.parametrize("factor", [-0.01, np.nan, np.inf])
def test_wall_friction_rejects_invalid_darcy_factor(factor: float) -> None:
    with pytest.raises(ValueError):
        wall_friction_source(_state(1.0, 100.0), 0.1, factor, GAS)


@pytest.mark.parametrize("parameter", [np.ones(3), np.ones((2, 3))])
def test_wall_friction_rejects_parameters_that_expand_state_shape(parameter: np.ndarray) -> None:
    with pytest.raises(ValueError):
        wall_friction_source(_state(np.ones((2, 5)), np.ones((2, 5))), parameter, 0.02, GAS)
    with pytest.raises(ValueError):
        wall_friction_source(_state(np.ones((2, 5)), np.ones((2, 5))), 0.1, parameter, GAS)


@pytest.mark.parametrize(
    "invalid_state",
    [
        np.array([np.nan, 0.0, 1.0]),
        np.array([np.inf, 0.0, 1.0]),
        np.array([0.0, 0.0, 1.0]),
        np.array([1.0, 0.0, 0.0]),
    ],
    ids=["nan", "infinite", "nonpositive-density", "nonpositive-pressure"],
)
def test_wall_friction_rejects_invalid_conservative_state(invalid_state: np.ndarray) -> None:
    with pytest.raises(ValueError):
        wall_friction_source(invalid_state, 0.1, 0.02, GAS)


def test_wall_friction_has_dimensional_magnitude_sanity() -> None:
    source = wall_friction_source(_state(1.0, 1000.0), 0.1, 0.02, GAS)
    assert 90_000.0 < abs(source[1]) < 110_000.0
