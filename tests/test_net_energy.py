"""Tests for the signed reduced-order reference-source extension."""

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.geometry import constant_area_profile
from scramjet1d.net_energy import (
    quasi_1d_rhs_with_net_energy,
    signed_net_energy_source,
    signed_net_momentum_source,
    solve_quasi_1d_steady_with_net_energy,
)
from scramjet1d.solver import quasi_1d_rhs, solve_quasi_1d_steady
from scramjet1d.state import primitive_to_conservative


GAS = GasProperties()


def _state(num_cells: int) -> np.ndarray:
    return primitive_to_conservative(
        np.full(num_cells, 1.0),
        np.full(num_cells, 600.0),
        np.full(num_cells, 100_000.0),
        GAS,
    )


def test_signed_net_energy_maps_only_to_energy_equation() -> None:
    state = _state(5)
    geometry = constant_area_profile(5, 0.02)
    line = np.array([-400.0, -100.0, 0.0, 250.0, 700.0])

    source = signed_net_energy_source(state, geometry, line, GAS)

    assert_allclose(source[:, 0], 0.0, atol=0.0)
    assert_allclose(source[:, 1], 0.0, atol=0.0)
    assert_allclose(source[:, 2], line / 0.02, rtol=1.0e-14, atol=1.0e-14)


def test_signed_net_momentum_maps_only_to_momentum_equation() -> None:
    state = _state(5)
    geometry = constant_area_profile(5, 0.02)
    line_force = np.array([-40.0, -10.0, 0.0, 25.0, 70.0])

    source = signed_net_momentum_source(state, geometry, line_force, GAS)

    assert_allclose(source[:, 0], 0.0, atol=0.0)
    assert_allclose(source[:, 1], line_force / 0.02, rtol=1.0e-14, atol=1.0e-14)
    assert_allclose(source[:, 2], 0.0, atol=0.0)


def test_zero_reference_sources_are_exactly_legacy_rhs() -> None:
    state = _state(6)
    geometry = constant_area_profile(6, 0.03)

    legacy = quasi_1d_rhs(state, geometry, 0.01, GAS)
    wrapped = quasi_1d_rhs_with_net_energy(
        state,
        geometry,
        0.01,
        GAS,
        net_energy_rate_per_length=0.0,
        net_momentum_rate_per_length=0.0,
    )

    assert_array_equal(wrapped, legacy)


def test_signed_reference_sources_compose_without_cross_coupling() -> None:
    state = _state(4)
    geometry = constant_area_profile(4, 0.01)
    base = quasi_1d_rhs(state, geometry, 0.02, GAS)
    energy = np.array([-200.0, 0.0, 300.0, -50.0])
    momentum = np.array([-20.0, 5.0, -3.0, 0.0])

    actual = quasi_1d_rhs_with_net_energy(
        state,
        geometry,
        0.02,
        GAS,
        net_energy_rate_per_length=energy,
        net_momentum_rate_per_length=momentum,
    )
    expected = (
        signed_net_energy_source(state, geometry, energy, GAS)
        + signed_net_momentum_source(state, geometry, momentum, GAS)
    )

    assert_allclose(actual - base, expected)


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf, np.ones(3)])
def test_invalid_net_energy_is_rejected(value) -> None:
    state = _state(4)
    geometry = constant_area_profile(4, 0.02)
    with pytest.raises(ValueError):
        signed_net_energy_source(state, geometry, value, GAS)


@pytest.mark.parametrize("value", [np.nan, np.inf, -np.inf, np.ones(3)])
def test_invalid_net_momentum_is_rejected(value) -> None:
    state = _state(4)
    geometry = constant_area_profile(4, 0.02)
    with pytest.raises(ValueError):
        signed_net_momentum_source(state, geometry, value, GAS)


def test_zero_reference_source_steady_wrapper_matches_production_solver() -> None:
    state = _state(8)
    geometry = constant_area_profile(8, 0.02)
    numerical = NumericalConfig(cfl=0.2, tolerance=1.0e-14)

    baseline = solve_quasi_1d_steady(
        state,
        geometry,
        0.01,
        1.0e-5,
        GAS,
        numerical,
    )
    wrapped = solve_quasi_1d_steady_with_net_energy(
        state,
        geometry,
        0.01,
        1.0e-5,
        GAS,
        numerical,
        net_energy_rate_per_length=0.0,
        net_momentum_rate_per_length=0.0,
    )

    assert wrapped.termination_reason == baseline.termination_reason
    assert wrapped.steps == baseline.steps
    assert wrapped.time == pytest.approx(baseline.time)
    assert_allclose(wrapped.U, baseline.U, rtol=0.0, atol=0.0)
    assert_allclose(wrapped.residual_history, baseline.residual_history, rtol=0.0, atol=0.0)
