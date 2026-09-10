"""P8.3 solver integration checks for prescribed distributed combustion heat release."""

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from scramjet1d.boundary import transmissive_ghost_cells
from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.geometry import constant_area_profile
from scramjet1d.solver import quasi_1d_rhs_transmissive, solve_quasi_1d
from scramjet1d.source_terms import (
    combined_wall_source,
    distributed_combustion_heat_release_source,
    distributed_fuel_injection_source,
)
from scramjet1d.spatial import internal_numerical_fluxes, quasi_1d_residual
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative


GAS = GasProperties()
NUMERICAL = NumericalConfig(cfl=0.5)
SCHEMES = ["rusanov", "steger-warming"]


def _state(num_cells: int = 12) -> np.ndarray:
    return primitive_to_conservative(
        np.ones(num_cells), np.full(num_cells, 500.0), np.full(num_cells, 100_000.0), GAS
    )


@pytest.mark.parametrize("scheme", SCHEMES)
def test_rhs_matches_manual_combustion_only_composition(scheme: str) -> None:
    """Catch omission or double addition of the P8.2 source in the RHS."""
    state = primitive_to_conservative(
        [1.0, 0.9, 1.1], [300.0, 350.0, 250.0], [100_000.0, 110_000.0, 90_000.0], GAS
    )
    geometry = constant_area_profile(3, 0.02)
    burn = np.array([0.001, 0.002, 0.003])
    lhv = np.array([40.0e6, 42.0e6, 44.0e6])
    base = quasi_1d_rhs_transmissive(state, geometry, 0.1, GAS, flux_scheme=scheme)
    combustion = distributed_combustion_heat_release_source(state, geometry, burn, lhv, GAS)

    actual = quasi_1d_rhs_transmissive(
        state, geometry, 0.1, GAS, flux_scheme=scheme,
        fuel_burn_rate_per_length=burn, fuel_lower_heating_value=lhv,
    )

    assert_allclose(actual, base + combustion, rtol=0.0, atol=1.0e-10)


@pytest.mark.parametrize("scheme", SCHEMES)
def test_rhs_matches_manual_wall_fuel_and_combustion_composition(scheme: str) -> None:
    """Catch one optional source overwriting another in the composed RHS."""
    state = primitive_to_conservative(
        [1.0, 0.9, 1.1], [300.0, 350.0, 250.0], [100_000.0, 110_000.0, 90_000.0], GAS
    )
    geometry = constant_area_profile(3, 0.02)
    dx = 0.1
    mass_flow = np.array([0.005, 0.010, 0.015])
    velocity = np.array([10.0, 20.0, 30.0])
    enthalpy = np.array([1.0e5, 2.0e5, 3.0e5])
    burn = np.array([0.001, 0.002, 0.003])
    lhv = np.array([40.0e6, 42.0e6, 44.0e6])
    spatial = quasi_1d_residual(
        state, internal_numerical_fluxes(transmissive_ghost_cells(state), GAS, scheme=scheme), geometry, dx, GAS
    )
    wall = combined_wall_source(state, 0.1, 0.01, 20_000.0, GAS)
    fuel = distributed_fuel_injection_source(state, geometry, mass_flow, velocity, enthalpy, GAS)
    combustion = distributed_combustion_heat_release_source(state, geometry, burn, lhv, GAS)

    actual = quasi_1d_rhs_transmissive(
        state, geometry, dx, GAS, flux_scheme=scheme,
        hydraulic_diameter=0.1, darcy_friction_factor=0.01, wall_heat_flux=20_000.0,
        fuel_mass_flow_rate_per_length=mass_flow, fuel_axial_velocity=velocity,
        fuel_specific_total_enthalpy=enthalpy,
        fuel_burn_rate_per_length=burn, fuel_lower_heating_value=lhv,
    )

    assert_allclose(actual, spatial + wall + fuel + combustion, rtol=0.0, atol=1.0e-10)


@pytest.mark.parametrize("scheme", SCHEMES)
def test_default_and_explicit_zero_combustion_are_identical(scheme: str) -> None:
    args = (_state(), constant_area_profile(12, 0.02), 1 / 12, 1.0e-4, GAS, NUMERICAL)
    default = solve_quasi_1d(*args, flux_scheme=scheme)
    none_lhv = solve_quasi_1d(
        *args, flux_scheme=scheme, fuel_burn_rate_per_length=0.0, fuel_lower_heating_value=None
    )
    valid_lhv = solve_quasi_1d(
        *args, flux_scheme=scheme, fuel_burn_rate_per_length=0.0, fuel_lower_heating_value=43.0e6
    )

    for result in (none_lhv, valid_lhv):
        assert result.time == default.time and result.steps == default.steps
        assert_allclose(result.U, default.U, rtol=0.0, atol=0.0)


INVALID_COMBUSTION_CASES = [
    pytest.param({"fuel_burn_rate_per_length": -0.001, "fuel_lower_heating_value": 43.0e6}, id="negative-burn"),
    pytest.param({"fuel_burn_rate_per_length": np.nan, "fuel_lower_heating_value": 43.0e6}, id="nan-burn"),
    pytest.param({"fuel_burn_rate_per_length": np.inf, "fuel_lower_heating_value": 43.0e6}, id="positive-inf-burn"),
    pytest.param({"fuel_burn_rate_per_length": -np.inf, "fuel_lower_heating_value": 43.0e6}, id="negative-inf-burn"),
    pytest.param({"fuel_burn_rate_per_length": np.ones(5), "fuel_lower_heating_value": 43.0e6}, id="bad-burn-shape"),
    pytest.param({"fuel_burn_rate_per_length": 0.001, "fuel_lower_heating_value": None}, id="active-burn-none-lhv"),
    pytest.param({"fuel_burn_rate_per_length": 0.001, "fuel_lower_heating_value": 0.0}, id="zero-lhv"),
    pytest.param({"fuel_burn_rate_per_length": 0.001, "fuel_lower_heating_value": -1.0}, id="negative-lhv"),
    pytest.param({"fuel_burn_rate_per_length": 0.001, "fuel_lower_heating_value": np.nan}, id="nan-lhv"),
    pytest.param({"fuel_burn_rate_per_length": 0.001, "fuel_lower_heating_value": np.inf}, id="positive-inf-lhv"),
    pytest.param({"fuel_burn_rate_per_length": 0.001, "fuel_lower_heating_value": -np.inf}, id="negative-inf-lhv"),
    pytest.param({"fuel_burn_rate_per_length": np.full(12, 0.001), "fuel_lower_heating_value": np.ones(5)}, id="bad-lhv-shape"),
    pytest.param({"fuel_burn_rate_per_length": 0.0, "fuel_lower_heating_value": np.nan}, id="zero-burn-nan-lhv"),
]


@pytest.mark.parametrize("override", INVALID_COMBUSTION_CASES)
def test_invalid_combustion_inputs_fail_before_cfl(monkeypatch, override: dict[str, object]) -> None:
    """Catch delayed solver validation after a CFL calculation has started."""
    import scramjet1d.solver as solver_module

    def forbidden_cfl(*args, **kwargs):
        raise AssertionError("CFL evaluation must not be reached")

    monkeypatch.setattr(solver_module, "cfl_timestep", forbidden_cfl)
    with pytest.raises(ValueError):
        solver_module.solve_quasi_1d(
            _state(), constant_area_profile(12, 0.02), 1 / 12, 1.0e-4, GAS, NUMERICAL, **override
        )


@pytest.mark.parametrize("scheme", SCHEMES)
def test_uniform_combustion_source_transient_is_exact_in_conservative_variables(scheme: str) -> None:
    num_cells = 12
    area = 0.02
    burn = 0.001
    lhv = 40.0e6
    final_time = 1.0e-4
    initial = _state(num_cells)
    result = solve_quasi_1d(
        initial, constant_area_profile(num_cells, area), 1 / num_cells, final_time, GAS, NUMERICAL,
        flux_scheme=scheme, fuel_burn_rate_per_length=burn, fuel_lower_heating_value=lhv,
    )
    heat_release = burn * lhv / area
    expected = initial + np.array([0.0, 0.0, heat_release * final_time])
    primitive = conservative_to_primitive(result.U, GAS)
    initial_primitive = conservative_to_primitive(initial, GAS)

    assert_allclose(result.U[:, 0], expected[:, 0], rtol=1.0e-12, atol=1.0e-12)
    assert_allclose(result.U[:, 1], expected[:, 1], rtol=0.0, atol=1.0e-10)
    assert_allclose(result.U[:, 2], expected[:, 2], rtol=1.0e-12, atol=1.0e-8)
    assert_allclose(primitive.u, initial_primitive.u, rtol=1.0e-12, atol=1.0e-12)
    assert np.all(primitive.p > initial_primitive.p) and np.all(primitive.T > initial_primitive.T)
    assert np.all(np.isfinite(result.U)) and np.all(primitive.rho > 0.0) and np.all(primitive.p > 0.0)


def test_combustion_source_is_re_evaluated_for_each_rk3_stage(monkeypatch) -> None:
    """Catch caching a combustion source outside the SSP-RK3 RHS closure."""
    import scramjet1d.solver as solver_module

    calls = []
    original = solver_module.distributed_combustion_heat_release_source

    def wrapped(U, geometry, fuel_burn_rate_per_length, fuel_lower_heating_value, gas):
        calls.append((np.array(U, copy=True), geometry, fuel_burn_rate_per_length, fuel_lower_heating_value, gas))
        return original(U, geometry, fuel_burn_rate_per_length, fuel_lower_heating_value, gas)

    monkeypatch.setattr(solver_module, "distributed_combustion_heat_release_source", wrapped)
    burn = np.linspace(0.001, 0.002, 12)
    lhv = np.linspace(40.0e6, 44.0e6, 12)
    geometry = constant_area_profile(12, 0.02)
    solve_quasi_1d(
        _state(), geometry, 1 / 12, 1.0e-6, GAS, NUMERICAL,
        fuel_burn_rate_per_length=burn, fuel_lower_heating_value=lhv,
    )

    assert len(calls) == 3
    assert np.max(np.abs(calls[0][0] - calls[1][0])) > 0.0
    assert np.max(np.abs(calls[1][0] - calls[2][0])) > 0.0
    assert all(call[1] is geometry for call in calls)
    assert all(call[2] is burn and call[3] is lhv and call[4] is GAS for call in calls)


@pytest.mark.parametrize("scheme", SCHEMES)
def test_mixed_wall_fuel_and_combustion_transient_is_physical_and_immutable(scheme: str) -> None:
    num_cells = 20
    initial = _state(num_cells)
    geometry = constant_area_profile(num_cells, 0.02)
    mass_flow = np.full(num_cells, 0.002)
    velocity = np.full(num_cells, 100.0)
    enthalpy = np.full(num_cells, 1.0e6)
    burn = np.full(num_cells, 0.0002)
    lhv = np.full(num_cells, 40.0e6)
    diameter = np.full(num_cells, 0.1)
    friction = np.full(num_cells, 0.01)
    heat_flux = np.full(num_cells, 20_000.0)
    inputs = [initial, mass_flow, velocity, enthalpy, burn, lhv, diameter, friction, heat_flux, geometry.cell_area, geometry.face_area]
    originals = [np.array(value, copy=True) for value in inputs]

    result = solve_quasi_1d(
        initial, geometry, 0.05, 3.0e-4, GAS, NUMERICAL, flux_scheme=scheme,
        hydraulic_diameter=diameter, darcy_friction_factor=friction, wall_heat_flux=heat_flux,
        fuel_mass_flow_rate_per_length=mass_flow, fuel_axial_velocity=velocity,
        fuel_specific_total_enthalpy=enthalpy,
        fuel_burn_rate_per_length=burn, fuel_lower_heating_value=lhv,
    )
    primitive = conservative_to_primitive(result.U, GAS)

    assert result.steps > 1 and result.time == pytest.approx(3.0e-4)
    assert np.all(np.isfinite(result.U))
    assert np.all(primitive.rho > 0.0) and np.all(primitive.p > 0.0) and np.all(primitive.T > 0.0)
    for actual, original in zip(inputs, originals):
        assert_array_equal(actual, original)
