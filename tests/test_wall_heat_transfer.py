"""Tests for the independent prescribed wall-heat-flux source model."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.config import GasProperties
from scramjet1d.source_terms import wall_heat_transfer_source
from scramjet1d.state import primitive_to_conservative


GAS = GasProperties()


def _state(rho: object, velocity: object, pressure: object = 100_000.0) -> np.ndarray:
    return primitive_to_conservative(rho, velocity, pressure, GAS)


def test_wall_heat_transfer_matches_independent_scalar_heating_formula() -> None:
    source = wall_heat_transfer_source(_state(1.2, 300.0), 0.1, 100_000.0, GAS)
    assert_allclose(source, [0.0, 0.0, 4_000_000.0], rtol=0.0, atol=1e-9)


def test_wall_heat_transfer_preserves_cooling_sign() -> None:
    source = wall_heat_transfer_source(_state(1.2, 300.0), 0.1, -100_000.0, GAS)
    assert_allclose(source, [0.0, 0.0, -4_000_000.0], rtol=0.0, atol=1e-9)


def test_wall_heat_transfer_is_zero_for_adiabatic_wall() -> None:
    assert_allclose(wall_heat_transfer_source(_state(1.2, 300.0), 0.1, 0.0, GAS), 0.0, rtol=0.0, atol=0.0)


def test_wall_heat_transfer_has_zero_mass_and_momentum_components() -> None:
    source = wall_heat_transfer_source(_state([0.8, 1.2, 1.6], [-300.0, 0.0, 500.0], [80_000.0, 100_000.0, 120_000.0]), [0.05, 0.1, 0.2], [-50_000.0, 0.0, 100_000.0], GAS)
    assert_allclose(source[:, 0], 0.0, rtol=0.0, atol=0.0)
    assert_allclose(source[:, 1], 0.0, rtol=0.0, atol=0.0)


@pytest.mark.parametrize("heat_flux", [100_000.0, -100_000.0])
def test_wall_heat_transfer_scales_linearly_with_signed_heat_flux(heat_flux: float) -> None:
    baseline = wall_heat_transfer_source(_state(1.2, 300.0), 0.1, heat_flux, GAS)[2]
    doubled = wall_heat_transfer_source(_state(1.2, 300.0), 0.1, 2.0 * heat_flux, GAS)[2]
    assert doubled == pytest.approx(2.0 * baseline)


def test_wall_heat_transfer_scales_inversely_with_hydraulic_diameter() -> None:
    baseline = wall_heat_transfer_source(_state(1.2, 300.0), 0.1, 100_000.0, GAS)[2]
    assert wall_heat_transfer_source(_state(1.2, 300.0), 0.2, 100_000.0, GAS)[2] == pytest.approx(0.5 * baseline)


def test_wall_heat_transfer_is_independent_of_state_when_flux_is_prescribed() -> None:
    low_state = _state(0.5, 100.0, 50_000.0)
    high_state = _state(2.0, 1000.0, 500_000.0)
    assert_allclose(wall_heat_transfer_source(low_state, 0.1, 100_000.0, GAS), wall_heat_transfer_source(high_state, 0.1, 100_000.0, GAS))


def test_wall_heat_transfer_vectorized_cells_match_scalar_evaluations() -> None:
    state = _state([1.0, 1.1, 1.2, 1.3, 1.4], [-200.0, -100.0, 0.0, 100.0, 200.0])
    diameter = np.array([0.05, 0.06, 0.07, 0.08, 0.09])
    heat_flux = np.array([-200_000.0, -100_000.0, 0.0, 100_000.0, 200_000.0])
    result = wall_heat_transfer_source(state, diameter, heat_flux, GAS)
    assert result.shape == (5, 3)
    assert_allclose(result, np.stack([wall_heat_transfer_source(cell, cell_diameter, cell_flux, GAS) for cell, cell_diameter, cell_flux in zip(state, diameter, heat_flux)]))


def test_wall_heat_transfer_supports_scalar_and_batched_broadcasting() -> None:
    state = np.stack((_state(np.ones(5), np.linspace(-200.0, 200.0, 5)), _state(np.full(5, 1.2), np.linspace(-100.0, 300.0, 5))))
    scalar = wall_heat_transfer_source(state[0], 0.1, 100_000.0, GAS)
    mixed = wall_heat_transfer_source(state, np.linspace(0.05, 0.1, 5), 100_000.0, GAS)
    batched_flux = wall_heat_transfer_source(state, 0.1, np.array([[-100_000.0] * 5, [100_000.0] * 5]), GAS)
    assert scalar.shape == (5, 3)
    assert mixed.shape == (2, 5, 3)
    assert batched_flux.shape == (2, 5, 3)
    assert_allclose(mixed[0], wall_heat_transfer_source(state[0], np.linspace(0.05, 0.1, 5), 100_000.0, GAS))


def test_wall_heat_transfer_single_state_and_inputs_are_unmodified() -> None:
    state = _state(1.2, 300.0)
    diameter, heat_flux = np.array(0.1), np.array(-100_000.0)
    original_state, original_diameter, original_heat_flux = state.copy(), diameter.copy(), heat_flux.copy()
    result = wall_heat_transfer_source(state, diameter, heat_flux, GAS)
    assert result.shape == (3,)
    assert_allclose(state, original_state)
    assert_allclose(diameter, original_diameter)
    assert_allclose(heat_flux, original_heat_flux)


@pytest.mark.parametrize("diameter", [0.0, -0.1, np.nan, np.inf])
def test_wall_heat_transfer_rejects_invalid_hydraulic_diameter(diameter: float) -> None:
    with pytest.raises(ValueError):
        wall_heat_transfer_source(_state(1.0, 100.0), diameter, 100_000.0, GAS)


@pytest.mark.parametrize("heat_flux", [np.nan, np.inf, -np.inf])
def test_wall_heat_transfer_rejects_nonfinite_heat_flux_and_accepts_cooling(heat_flux: float) -> None:
    with pytest.raises(ValueError):
        wall_heat_transfer_source(_state(1.0, 100.0), 0.1, heat_flux, GAS)
    assert wall_heat_transfer_source(_state(1.0, 100.0), 0.1, -1.0, GAS)[2] < 0.0


@pytest.mark.parametrize("parameter", [np.ones(3), np.ones((2, 3))])
def test_wall_heat_transfer_rejects_parameters_that_expand_state_shape(parameter: np.ndarray) -> None:
    state = _state(np.ones((2, 5)), np.ones((2, 5)))
    with pytest.raises(ValueError):
        wall_heat_transfer_source(state, parameter, 100_000.0, GAS)
    with pytest.raises(ValueError):
        wall_heat_transfer_source(state, 0.1, parameter, GAS)


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
def test_wall_heat_transfer_rejects_invalid_conservative_state(invalid_state: np.ndarray) -> None:
    with pytest.raises(ValueError):
        wall_heat_transfer_source(invalid_state, 0.1, 100_000.0, GAS)


def test_wall_heat_transfer_has_dimensional_magnitude_sanity_and_vector_signs() -> None:
    source = wall_heat_transfer_source(_state(1.0, 1000.0), 0.1, 1_000_000.0, GAS)
    assert 39_000_000.0 < source[2] < 41_000_000.0
    signed = wall_heat_transfer_source(_state(np.ones(5), np.zeros(5)), 0.1, [-200_000.0, -100_000.0, 0.0, 100_000.0, 200_000.0], GAS)
    assert np.array_equal(np.sign(signed[:, 2]), [-1.0, -1.0, 0.0, 1.0, 1.0])
