"""Tests for the P4.2 quasi-one-dimensional spatial operator."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.config import GasProperties
from scramjet1d.geometry import AreaProfile, constant_area_profile
from scramjet1d.source_terms import geometric_area_source
from scramjet1d.spatial import (
    area_weighted_flux_residual,
    finite_volume_residual,
    quasi_1d_residual,
)
from scramjet1d.state import primitive_to_conservative


GAS = GasProperties()


def _state(pressure: object, *, velocity: object = 0.0, density: object = 1.2) -> np.ndarray:
    """Build valid conservative states from simple SI primitive data."""
    return primitive_to_conservative(density, velocity, pressure, GAS)


def test_area_weighted_flux_residual_matches_hand_calculation() -> None:
    geometry = AreaProfile([2.0, 4.0, 5.0], [1.0, 2.0, 4.0, 5.0])
    fluxes = np.array(
        [[1.0, 10.0, 100.0], [2.0, 20.0, 200.0], [3.0, 30.0, 300.0], [4.0, 40.0, 400.0]]
    )

    result = area_weighted_flux_residual(fluxes, geometry, dx=0.5)

    expected = np.array([[-3.0, -30.0, -300.0], [-4.0, -40.0, -400.0], [-3.2, -32.0, -320.0]])
    assert_allclose(result, expected)


def test_area_weighted_flux_residual_reduces_to_constant_area_baseline() -> None:
    fluxes = np.array([[1.0, -2.0, 3.0], [2.0, -4.0, 6.0], [4.0, -1.0, 9.0], [8.0, 3.0, 12.0]])
    geometry = constant_area_profile(3, area=0.02)

    assert_allclose(
        area_weighted_flux_residual(fluxes, geometry, dx=0.25),
        finite_volume_residual(fluxes, dx=0.25),
    )


def test_geometric_area_source_is_zero_for_constant_area() -> None:
    state = _state([90_000.0, 110_000.0, 125_000.0], velocity=[10.0, -5.0, 25.0])

    assert_allclose(geometric_area_source(state, constant_area_profile(3), 0.1, GAS), 0.0)


def test_geometric_area_source_matches_known_momentum_values() -> None:
    geometry = AreaProfile([1.1, 1.35, 1.7], [1.0, 1.2, 1.5, 1.9])
    state = _state([100_000.0, 120_000.0, 90_000.0])

    result = geometric_area_source(state, geometry, 0.1, GAS)

    expected = np.zeros((3, 3))
    expected[:, 1] = np.array([100_000.0 * 0.2 / (1.1 * 0.1), 120_000.0 * 0.3 / (1.35 * 0.1), 90_000.0 * 0.4 / (1.7 * 0.1)])
    assert_allclose(result, expected)


def test_converging_geometry_has_negative_momentum_source() -> None:
    geometry = AreaProfile([1.9, 1.5], [2.0, 1.8, 1.2])

    source = geometric_area_source(_state([100_000.0, 100_000.0]), geometry, 0.2, GAS)

    assert np.all(source[:, 1] < 0.0)


def test_static_equal_pressure_state_is_well_balanced() -> None:
    geometry = AreaProfile([1.1, 1.35, 1.4, 1.45, 1.8], [1.0, 1.2, 1.5, 1.3, 1.6, 2.0])
    pressure = 100_000.0
    state = _state(np.full(5, pressure))
    fluxes = np.tile([0.0, pressure, 0.0], (6, 1))

    result = quasi_1d_residual(state, fluxes, geometry, 0.1, GAS)

    assert_allclose(result, 0.0, rtol=0.0, atol=1e-8)


def test_full_quasi_one_d_residual_reduces_to_p3_for_constant_area() -> None:
    state = _state([100_000.0, 105_000.0, 95_000.0], velocity=[10.0, 0.0, -5.0])
    fluxes = np.array([[1.0, 2.0, 3.0], [2.0, 4.0, 6.0], [3.0, 6.0, 9.0], [4.0, 8.0, 12.0]])

    assert_allclose(
        quasi_1d_residual(state, fluxes, constant_area_profile(3, 0.5), 0.2, GAS),
        finite_volume_residual(fluxes, 0.2),
    )


def test_geometric_area_source_supports_batched_states() -> None:
    geometry = AreaProfile([1.1, 1.35], [1.0, 1.2, 1.5])
    state = _state(np.array([[100_000.0, 120_000.0], [90_000.0, 80_000.0]]))

    result = geometric_area_source(state, geometry, 0.1, GAS)

    expected_momentum = np.array([[100_000.0 * 0.2 / 0.11, 120_000.0 * 0.3 / 0.135], [90_000.0 * 0.2 / 0.11, 80_000.0 * 0.3 / 0.135]])
    assert result.shape == (2, 2, 3)
    assert_allclose(result[..., 0], 0.0)
    assert_allclose(result[..., 1], expected_momentum)
    assert_allclose(result[..., 2], 0.0)


def test_area_weighted_flux_residual_supports_batched_fluxes() -> None:
    geometry = AreaProfile([2.0, 4.0], [1.0, 2.0, 4.0])
    fluxes = np.array([[[1.0, 2.0, 3.0], [2.0, 4.0, 6.0], [3.0, 6.0, 9.0]], [[2.0, 1.0, -1.0], [3.0, 2.0, -2.0], [5.0, 4.0, -4.0]]])

    result = area_weighted_flux_residual(fluxes, geometry, 0.5)

    expected = np.array([[[-3.0, -6.0, -9.0], [-4.0, -8.0, -12.0]], [[-4.0, -3.0, 3.0], [-7.0, -6.0, 6.0]]])
    assert_allclose(result, expected)


def test_quasi_one_d_residual_supports_batched_inputs() -> None:
    geometry = AreaProfile([1.1, 1.35], [1.0, 1.2, 1.5])
    state = _state(np.array([[100_000.0, 110_000.0], [90_000.0, 120_000.0]]))
    fluxes = np.array([[[1.0, 2.0, 3.0], [2.0, 4.0, 6.0], [3.0, 6.0, 9.0]], [[3.0, 2.0, 1.0], [2.0, 4.0, 8.0], [1.0, 6.0, 12.0]]])

    result = quasi_1d_residual(state, fluxes, geometry, 0.2, GAS)

    assert result.shape == (2, 2, 3)
    assert_allclose(
        result,
        area_weighted_flux_residual(fluxes, geometry, 0.2) + geometric_area_source(state, geometry, 0.2, GAS),
    )


def test_negative_finite_flux_components_are_legal() -> None:
    geometry = constant_area_profile(2)
    fluxes = np.array([[-1.0, 2.0, -3.0], [-2.0, 4.0, -6.0], [-3.0, 6.0, -9.0]])

    assert_allclose(area_weighted_flux_residual(fluxes, geometry, 0.5), [[2.0, -4.0, 6.0], [2.0, -4.0, 6.0]])


@pytest.mark.parametrize("fluxes", [np.ones((3, 3)), np.ones((4, 4)), np.ones((3,))])
def test_area_weighted_flux_residual_rejects_bad_interface_shape(fluxes: np.ndarray) -> None:
    with pytest.raises(ValueError):
        area_weighted_flux_residual(fluxes, constant_area_profile(3), 0.1)


@pytest.mark.parametrize("state", [np.ones((2, 3)), np.ones((4, 3)), np.ones((3, 4))])
def test_source_and_combined_residual_reject_bad_state_shape_or_count(state: np.ndarray) -> None:
    geometry = constant_area_profile(3)
    fluxes = np.ones((4, 3))
    with pytest.raises(ValueError):
        geometric_area_source(state, geometry, 0.1, GAS)
    with pytest.raises(ValueError):
        quasi_1d_residual(state, fluxes, geometry, 0.1, GAS)


@pytest.mark.parametrize("bad_dx", [0.0, -0.1, np.nan, np.inf, [0.1]])
def test_all_new_operators_reject_invalid_dx(bad_dx: object) -> None:
    geometry = constant_area_profile(2)
    state = _state([100_000.0, 100_000.0])
    fluxes = np.ones((3, 3))
    with pytest.raises(ValueError):
        area_weighted_flux_residual(fluxes, geometry, bad_dx)
    with pytest.raises(ValueError):
        geometric_area_source(state, geometry, bad_dx, GAS)
    with pytest.raises(ValueError):
        quasi_1d_residual(state, fluxes, geometry, bad_dx, GAS)


@pytest.mark.parametrize("bad_geometry", [None, {}, np.ones(3)])
def test_all_new_operators_reject_wrong_geometry_type(bad_geometry: object) -> None:
    state = _state([100_000.0, 100_000.0])
    fluxes = np.ones((3, 3))
    with pytest.raises(TypeError):
        area_weighted_flux_residual(fluxes, bad_geometry, 0.1)
    with pytest.raises(TypeError):
        geometric_area_source(state, bad_geometry, 0.1, GAS)
    with pytest.raises(TypeError):
        quasi_1d_residual(state, fluxes, bad_geometry, 0.1, GAS)


@pytest.mark.parametrize("bad_flux", [np.array([[np.nan, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]), np.array([[np.inf, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])])
def test_area_weighted_flux_residual_rejects_nonfinite_fluxes(bad_flux: np.ndarray) -> None:
    with pytest.raises(ValueError):
        area_weighted_flux_residual(bad_flux, constant_area_profile(2), 0.1)


@pytest.mark.parametrize("state", [np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 1.0]]), np.array([[1.0, 0.0, -1.0], [1.0, 0.0, 1.0]])])
def test_geometric_area_source_rejects_nonphysical_state(state: np.ndarray) -> None:
    with pytest.raises(ValueError):
        geometric_area_source(state, constant_area_profile(2), 0.1, GAS)
