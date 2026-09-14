"""Regression tests for the direct prescribed line-heat-release P8 interface."""

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.geometry import constant_area_profile
from scramjet1d.solver import quasi_1d_rhs, solve_quasi_1d
from scramjet1d.state import primitive_to_conservative


GAS = GasProperties()


def _uniform_state(num_cells: int) -> np.ndarray:
    return primitive_to_conservative(
        np.full(num_cells, 1.0),
        np.full(num_cells, 700.0),
        np.full(num_cells, 100_000.0),
        GAS,
    )


def test_zero_direct_heat_preserves_legacy_rhs() -> None:
    state = _uniform_state(6)
    geometry = constant_area_profile(6, 0.02)

    legacy = quasi_1d_rhs(state, geometry, 0.01, GAS)
    explicit_zero = quasi_1d_rhs(
        state, geometry, 0.01, GAS, heat_release_rate_per_length=0.0
    )

    assert_array_equal(explicit_zero, legacy)


def test_direct_line_heat_maps_only_to_energy_rhs() -> None:
    state = _uniform_state(5)
    area = 0.02
    geometry = constant_area_profile(5, area)
    line_heat = np.array([0.0, 100.0, 250.0, 400.0, 0.0])

    base = quasi_1d_rhs(state, geometry, 0.01, GAS)
    heated = quasi_1d_rhs(
        state,
        geometry,
        0.01,
        GAS,
        heat_release_rate_per_length=line_heat,
    )
    delta = heated - base

    assert_allclose(delta[:, 0], 0.0, atol=0.0)
    assert_allclose(delta[:, 1], 0.0, atol=0.0)
    assert_allclose(delta[:, 2], line_heat / area, rtol=1.0e-13, atol=1.0e-13)


def test_direct_heat_is_exactly_equivalent_to_burned_fuel_lhv_energy_path() -> None:
    state = _uniform_state(7)
    geometry = constant_area_profile(7, 0.015)
    line_heat = np.linspace(0.0, 700_000.0, 7)
    lhv = 42.0e6
    burn_rate = line_heat / lhv

    direct = quasi_1d_rhs(
        state,
        geometry,
        0.02,
        GAS,
        heat_release_rate_per_length=line_heat,
    )
    burned_fuel = quasi_1d_rhs(
        state,
        geometry,
        0.02,
        GAS,
        fuel_burn_rate_per_length=burn_rate,
        fuel_lower_heating_value=lhv,
    )

    assert_allclose(direct, burned_fuel, rtol=1.0e-14, atol=1.0e-12)


def test_direct_and_burned_fuel_paths_cannot_be_active_together() -> None:
    state = _uniform_state(4)
    geometry = constant_area_profile(4, 0.02)

    with pytest.raises(ValueError, match="choose exactly one combustion-energy path"):
        quasi_1d_rhs(
            state,
            geometry,
            0.01,
            GAS,
            heat_release_rate_per_length=1000.0,
            fuel_burn_rate_per_length=1.0e-5,
            fuel_lower_heating_value=42.0e6,
        )


@pytest.mark.parametrize(
    "value",
    [-1.0, np.nan, np.inf, -np.inf, np.ones(3)],
)
def test_invalid_direct_heat_release_is_rejected(value) -> None:
    state = _uniform_state(4)
    geometry = constant_area_profile(4, 0.02)

    with pytest.raises(ValueError):
        quasi_1d_rhs(
            state,
            geometry,
            0.01,
            GAS,
            heat_release_rate_per_length=value,
        )


def test_transient_solver_propagates_direct_heat_path_without_fake_fuel() -> None:
    state = _uniform_state(8)
    geometry = constant_area_profile(8, 0.02)
    numerical = NumericalConfig(cfl=0.2, tolerance=1.0e-8)
    line_heat = np.full(8, 10_000.0)
    lhv = 42.0e6

    direct = solve_quasi_1d(
        state,
        geometry,
        0.01,
        1.0e-5,
        GAS,
        numerical,
        heat_release_rate_per_length=line_heat,
    )
    burned = solve_quasi_1d(
        state,
        geometry,
        0.01,
        1.0e-5,
        GAS,
        numerical,
        fuel_burn_rate_per_length=line_heat / lhv,
        fuel_lower_heating_value=lhv,
    )

    assert direct.steps > 0
    assert direct.time == pytest.approx(1.0e-5)
    assert_allclose(direct.U, burned.U, rtol=2.0e-14, atol=1.0e-9)
