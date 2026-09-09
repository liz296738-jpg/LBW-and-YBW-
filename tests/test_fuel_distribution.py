"""P7.2 tests for prescribed axial fuel-distribution conversion."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.config import GasProperties
from scramjet1d.geometry import AreaProfile, constant_area_profile
from scramjet1d.source_terms import distributed_fuel_injection_source, fuel_injection_source, fuel_mass_source_rate_from_axial_distribution
from scramjet1d.state import primitive_to_conservative

GAS = GasProperties()


def _state(shape):
    return primitive_to_conservative(np.ones(shape), np.full(shape, 300.0), np.full(shape, 100_000.0), GAS)


def test_constant_area_hand_mapping_and_composed_source() -> None:
    state, geometry = _state((3,)), constant_area_profile(3, 0.02)
    rate = fuel_mass_source_rate_from_axial_distribution(state, geometry, 0.01, GAS)
    source = distributed_fuel_injection_source(state, geometry, 0.01, 200.0, 1e6, GAS)
    assert_allclose(rate, [0.5, 0.5, 0.5])
    assert_allclose(source[0], [0.5, 100.0, 500_000.0])


def test_variable_area_inverse_mapping_and_composition() -> None:
    geometry = AreaProfile([.01, .02, .04], [.01, .015, .03, .04])
    state = _state((3,))
    rate = fuel_mass_source_rate_from_axial_distribution(state, geometry, .02, GAS)
    assert_allclose(rate, [2.0, 1.0, .5])
    assert_allclose(distributed_fuel_injection_source(state, geometry, .02, [1., 2., 3.], [4., 5., 6.], GAS), fuel_injection_source(state, rate, [1., 2., 3.], [4., 5., 6.], GAS))


def test_area_weighted_mass_momentum_energy_conservation() -> None:
    geometry = AreaProfile([.01, .02, .04], [.01, .015, .03, .04]); state = _state((3,)); dx = .1
    mprime = np.array([.01, .02, .03]); velocity = np.array([10., 20., 30.]); enthalpy = np.array([100., 200., 300.])
    source = distributed_fuel_injection_source(state, geometry, mprime, velocity, enthalpy, GAS)
    volume = geometry.cell_area * dx
    assert_allclose(np.sum(source[:, 0] * volume), np.sum(mprime * dx))
    assert_allclose(np.sum(source[:, 1] * volume), np.sum(mprime * velocity * dx))
    assert_allclose(np.sum(source[:, 2] * volume), np.sum(mprime * enthalpy * dx))


def test_batch_and_scalar_distribution_broadcasting() -> None:
    geometry = constant_area_profile(5, .02); state = _state((2, 5))
    rate = fuel_mass_source_rate_from_axial_distribution(state, geometry, np.arange(1., 6.), GAS)
    source = distributed_fuel_injection_source(state, geometry, np.arange(1., 6.), 10., np.full((2, 5), 100.), GAS)
    assert rate.shape == (2, 5) and source.shape == (2, 5, 3)
    assert_allclose(source[1, 4], [250., 2500., 25_000.])


@pytest.mark.parametrize("distribution", [-1., np.nan, np.inf, np.ones(3)])
def test_invalid_or_nonbroadcastable_distribution_is_rejected(distribution) -> None:
    with pytest.raises(ValueError): fuel_mass_source_rate_from_axial_distribution(_state((2, 5)), constant_area_profile(5), distribution, GAS)


def test_geometry_mismatch_single_state_and_type_are_rejected() -> None:
    with pytest.raises(ValueError): fuel_mass_source_rate_from_axial_distribution(_state((4,)), constant_area_profile(5), 1., GAS)
    with pytest.raises(ValueError): fuel_mass_source_rate_from_axial_distribution(_state(()), constant_area_profile(1), 1., GAS)
    with pytest.raises(TypeError): fuel_mass_source_rate_from_axial_distribution(_state((5,)), np.ones(5), 1., GAS)
