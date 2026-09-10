"""Acceptance tests for the independent P8.2 burned-fuel heat-release closure."""

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from scramjet1d.config import GasProperties
from scramjet1d.geometry import AreaProfile, constant_area_profile
from scramjet1d.source_terms import (
    combustion_heat_release_source,
    distributed_combustion_heat_release_source,
    heat_release_rate_per_length_from_burned_fuel,
    volumetric_heat_release_rate_from_axial_distribution,
)
from scramjet1d.state import primitive_to_conservative


GAS = GasProperties()


def _state(shape, rho=1.0, velocity=500.0, pressure=100_000.0):
    return primitive_to_conservative(
        np.full(shape, rho), np.full(shape, velocity), np.full(shape, pressure), GAS
    )


def _variable_geometry():
    return AreaProfile([0.01, 0.02, 0.04], [0.01, 0.015, 0.03, 0.04])


def test_burned_fuel_and_lhv_have_exact_line_heat_release_mapping() -> None:
    assert heat_release_rate_per_length_from_burned_fuel(0.01, 43.0e6) == 430_000.0


def test_zero_burn_and_nonuniform_burn_lhv_arrays_map_elementwise() -> None:
    assert heat_release_rate_per_length_from_burned_fuel(0.0, 43.0e6) == 0.0
    burn = np.array([0.0, 0.005, 0.010, 0.015])
    lhv = np.array([42.0e6, 42.0e6, 43.0e6, 43.0e6])
    assert_array_equal(
        heat_release_rate_per_length_from_burned_fuel(burn, lhv), burn * lhv
    )


def test_line_heat_release_supports_scalar_and_batched_broadcasting() -> None:
    assert_array_equal(
        heat_release_rate_per_length_from_burned_fuel(np.array([0.01, 0.02]), 43.0e6),
        [430_000.0, 860_000.0],
    )
    assert_array_equal(
        heat_release_rate_per_length_from_burned_fuel(0.01, np.array([42.0e6, 43.0e6])),
        [420_000.0, 430_000.0],
    )
    assert_array_equal(
        heat_release_rate_per_length_from_burned_fuel(np.ones((2, 1)) * 0.01, np.array([42.0e6, 43.0e6])),
        [[420_000.0, 430_000.0], [420_000.0, 430_000.0]],
    )


@pytest.mark.parametrize(
    ("burn_rate", "lhv"),
    [(np.ones(3), np.ones(5)), (np.ones((2, 3)), np.ones(4))],
)
def test_burn_rate_and_lhv_incompatible_shapes_raise_value_error(burn_rate, lhv) -> None:
    """Catch removal of the closure's explicit incompatible-broadcast guard."""
    with pytest.raises(ValueError):
        heat_release_rate_per_length_from_burned_fuel(burn_rate, lhv)


def test_variable_area_mapping_uses_cell_area_without_dx() -> None:
    geometry = _variable_geometry()
    heat_per_length = np.array([100.0, 200.0, 400.0])
    volumetric = volumetric_heat_release_rate_from_axial_distribution(
        _state((3,)), geometry, heat_per_length, GAS
    )

    assert_array_equal(volumetric, [10_000.0, 10_000.0, 10_000.0])
    dx = 0.1
    assert_allclose(
        np.sum(geometry.cell_area * volumetric * dx),
        np.sum(heat_per_length * dx),
        rtol=1.0e-14,
        atol=1.0e-14,
    )


def test_distributed_combustion_source_satisfies_integrated_energy_identity() -> None:
    """Catch an area or dx error in the final distributed source mapping."""
    num_cells = 12
    dx = 0.04
    cell_area = np.linspace(0.015, 0.030, num_cells)
    geometry = AreaProfile(cell_area, np.linspace(0.015, 0.030, num_cells + 1))
    burn_rate = np.linspace(0.0, 0.02, num_cells)
    lhv = np.linspace(40.0e6, 44.0e6, num_cells)

    source = distributed_combustion_heat_release_source(
        _state((num_cells,)), geometry, burn_rate, lhv, GAS
    )
    reference = np.sum(burn_rate * lhv) * dx
    actual = np.sum(geometry.cell_area * source[:, 2]) * dx

    assert_array_equal(source[:, 0], np.zeros(num_cells))
    assert_array_equal(source[:, 1], np.zeros(num_cells))
    assert_allclose(actual, reference, rtol=1.0e-13, atol=1.0e-13)


def test_distributed_source_composes_through_p8_1(monkeypatch) -> None:
    import scramjet1d.source_terms as source_terms

    state = _state((3,))
    geometry = _variable_geometry()
    burn = np.array([0.01, 0.02, 0.03])
    lhv = np.array([40.0e6, 42.0e6, 43.0e6])
    calls = []
    original = source_terms.combustion_heat_release_source

    def wrapped(U, volumetric_heat_release_rate, gas):
        calls.append(np.array(volumetric_heat_release_rate, copy=True))
        return original(U, volumetric_heat_release_rate, gas)

    monkeypatch.setattr(source_terms, "combustion_heat_release_source", wrapped)
    source = source_terms.distributed_combustion_heat_release_source(
        state, geometry, burn, lhv, GAS
    )
    expected_heat = burn * lhv
    expected_volumetric = expected_heat / geometry.cell_area

    assert len(calls) == 1
    assert_array_equal(calls[0], expected_volumetric)
    assert_array_equal(source[:, :2], 0.0)
    assert_array_equal(source[:, 2], expected_volumetric)


def test_distributed_source_is_state_independent_and_preserves_batched_shape() -> None:
    geometry = constant_area_profile(4, 0.02)
    burn = np.array([0.0, 0.005, 0.010, 0.015])
    state_a = _state((2, 4), rho=1.0, velocity=300.0, pressure=100_000.0)
    state_b = _state((2, 4), rho=0.4, velocity=1500.0, pressure=50_000.0)

    source_a = distributed_combustion_heat_release_source(state_a, geometry, burn, 43.0e6, GAS)
    source_b = distributed_combustion_heat_release_source(state_b, geometry, burn, 43.0e6, GAS)

    assert source_a.shape == (2, 4, 3)
    assert_array_equal(source_a, source_b)
    assert_array_equal(source_a[..., :2], 0.0)


@pytest.mark.parametrize("burn", [-1.0, np.nan, np.inf, -np.inf])
def test_invalid_burn_rate_is_rejected(burn) -> None:
    with pytest.raises(ValueError):
        heat_release_rate_per_length_from_burned_fuel(burn, 43.0e6)


@pytest.mark.parametrize("lhv", [0.0, -1.0, np.nan, np.inf, -np.inf])
def test_invalid_lhv_is_rejected_even_for_zero_burn(lhv) -> None:
    with pytest.raises(ValueError):
        heat_release_rate_per_length_from_burned_fuel(0.0, lhv)


@pytest.mark.parametrize("heat_per_length", [-1.0, np.nan, np.inf, -np.inf, np.ones(5)])
def test_invalid_line_heat_release_is_rejected(heat_per_length) -> None:
    with pytest.raises(ValueError):
        volumetric_heat_release_rate_from_axial_distribution(
            _state((3,)), _variable_geometry(), heat_per_length, GAS
        )


def test_invalid_geometry_state_and_cell_count_are_rejected() -> None:
    with pytest.raises(TypeError):
        volumetric_heat_release_rate_from_axial_distribution(_state((3,)), np.ones(3), 1.0, GAS)
    with pytest.raises(ValueError):
        volumetric_heat_release_rate_from_axial_distribution(_state((2,)), _variable_geometry(), 1.0, GAS)
    with pytest.raises(ValueError):
        volumetric_heat_release_rate_from_axial_distribution(np.ones(3), _variable_geometry(), 1.0, GAS)


def _make_negative_density(U: np.ndarray) -> None:
    U[0, 0] = -1.0


def _make_nonpositive_recovered_pressure(U: np.ndarray) -> None:
    U[0, 2] = 0.0


def _make_nonfinite_state(U: np.ndarray) -> None:
    U[0, 1] = np.nan


@pytest.mark.parametrize(
    "mutator",
    [_make_negative_density, _make_nonpositive_recovered_pressure, _make_nonfinite_state],
    ids=["negative-density", "nonpositive-pressure", "nonfinite-state"],
)
def test_distributed_combustion_source_rejects_invalid_physical_state(mutator) -> None:
    """Catch bypassing conservative-state validation in the final P8.2 API."""
    state = _state((3,))
    mutator(state)

    with pytest.raises(ValueError):
        distributed_combustion_heat_release_source(state, _variable_geometry(), 0.01, 43.0e6, GAS)


def test_all_closure_inputs_remain_immutable() -> None:
    state = _state((3,))
    geometry = _variable_geometry()
    burn = np.array([0.01, 0.02, 0.03])
    lhv = np.array([40.0e6, 42.0e6, 43.0e6])
    heat_per_length = burn * lhv
    originals = [state.copy(), geometry.cell_area.copy(), geometry.face_area.copy(), burn.copy(), lhv.copy(), heat_per_length.copy()]

    distributed_combustion_heat_release_source(state, geometry, burn, lhv, GAS)
    volumetric_heat_release_rate_from_axial_distribution(state, geometry, heat_per_length, GAS)

    for actual, expected in zip(
        (state, geometry.cell_area, geometry.face_area, burn, lhv, heat_per_length), originals
    ):
        assert_array_equal(actual, expected)
