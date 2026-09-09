"""P6.3 composition and quasi-1D solver integration tests for wall sources."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.boundary import transmissive_ghost_cells
from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.geometry import AreaProfile, constant_area_profile
from scramjet1d.solver import cfl_timestep, quasi_1d_rhs_transmissive, solve_quasi_1d
from scramjet1d.spatial import internal_numerical_fluxes, quasi_1d_residual
from scramjet1d.source_terms import combined_wall_source, wall_friction_source, wall_heat_transfer_source
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative


GAS = GasProperties()
NUMERICAL = NumericalConfig()


def _state(rho: object, velocity: object, pressure: object = 100_000.0) -> np.ndarray:
    return primitive_to_conservative(rho, velocity, pressure, GAS)


def _uniform(count: int = 10) -> np.ndarray:
    return _state(np.ones(count), np.full(count, 300.0), np.full(count, 100_000.0))


def test_combined_wall_source_is_the_sum_of_independent_sources() -> None:
    state = _state([1.0, 1.2], [300.0, -200.0])
    expected = wall_friction_source(state, [0.1, 0.2], 0.02, GAS) + wall_heat_transfer_source(state, [0.1, 0.2], [-50_000.0, 100_000.0], GAS)
    assert_allclose(combined_wall_source(state, [0.1, 0.2], 0.02, [-50_000.0, 100_000.0], GAS), expected)


def test_combined_wall_source_has_expected_signed_components_and_broadcasting() -> None:
    state = np.stack((_state(np.ones(5), np.linspace(-200.0, 200.0, 5)), _state(np.full(5, 1.2), np.linspace(-100.0, 300.0, 5))))
    source = combined_wall_source(state, np.linspace(0.05, 0.1, 5), 0.02, np.array([[-50_000.0] * 5, [100_000.0] * 5]), GAS)
    assert source.shape == (2, 5, 3)
    assert_allclose(source[..., 0], 0.0, rtol=0.0, atol=0.0)
    assert source[0, 0, 1] > 0.0 and source[1, -1, 1] < 0.0
    assert source[0, 0, 2] < 0.0 and source[1, -1, 2] > 0.0
    assert_allclose(combined_wall_source(state, 0.1, 0.0, 0.0, GAS), 0.0, rtol=0.0, atol=0.0)


@pytest.mark.parametrize("scheme", ["rusanov", "steger-warming"])
def test_integrated_rhs_matches_manual_baseline_plus_wall_source(scheme: str) -> None:
    state = _state([1.0, 0.9, 1.1], [200.0, 100.0, -50.0], [100_000.0, 90_000.0, 110_000.0])
    geometry = AreaProfile([1.1, 1.2, 1.3], [1.0, 1.2, 1.3, 1.4])
    diameter, factor, heat_flux = np.array([0.08, 0.1, 0.12]), 0.02, np.array([-10_000.0, 0.0, 20_000.0])
    fluxes = internal_numerical_fluxes(transmissive_ghost_cells(state), GAS, scheme=scheme)
    expected = quasi_1d_residual(state, fluxes, geometry, 0.1, GAS) + combined_wall_source(state, diameter, factor, heat_flux, GAS)
    actual = quasi_1d_rhs_transmissive(state, geometry, 0.1, GAS, flux_scheme=scheme, hydraulic_diameter=diameter, darcy_friction_factor=factor, wall_heat_flux=heat_flux)
    assert_allclose(actual, expected)


def test_default_and_explicit_zero_wall_rhs_are_identical() -> None:
    state = _state([1.0, 0.9, 1.1], [200.0, 100.0, -50.0], [100_000.0, 90_000.0, 110_000.0])
    geometry = constant_area_profile(3)
    baseline = quasi_1d_rhs_transmissive(state, geometry, 0.1, GAS)
    assert_allclose(quasi_1d_rhs_transmissive(state, geometry, 0.1, GAS, hydraulic_diameter=0.1, darcy_friction_factor=0.0, wall_heat_flux=0.0), baseline, rtol=0.0, atol=0.0)


def test_default_and_explicit_zero_wall_solver_are_identical() -> None:
    initial = _uniform(6)
    geometry = constant_area_profile(6)
    baseline = solve_quasi_1d(initial, geometry, 0.1, 1e-4, GAS, NUMERICAL)
    explicit = solve_quasi_1d(initial, geometry, 0.1, 1e-4, GAS, NUMERICAL, hydraulic_diameter=0.1, darcy_friction_factor=0.0, wall_heat_flux=0.0)
    assert baseline.time == explicit.time and baseline.steps == explicit.steps
    assert_allclose(baseline.U, explicit.U, rtol=0.0, atol=0.0)


def test_uniform_friction_only_multistep_decelerates_without_mass_or_energy_change() -> None:
    initial = _uniform()
    dt = cfl_timestep(initial, 0.1, GAS, NUMERICAL)
    result = solve_quasi_1d(initial, constant_area_profile(10), 0.1, 2.25 * dt, GAS, NUMERICAL, hydraulic_diameter=0.1, darcy_friction_factor=0.02, wall_heat_flux=0.0)
    primitive = conservative_to_primitive(result.U, GAS)
    assert result.steps >= 3
    assert_allclose(result.U[:, 0], initial[:, 0], rtol=0.0, atol=1e-10)
    assert_allclose(result.U[:, 2], initial[:, 2], rtol=0.0, atol=1e-8)
    assert abs(np.mean(primitive.u)) < 300.0
    assert_allclose(primitive.rho, primitive.rho[0])
    assert_allclose(primitive.u, primitive.u[0])


def test_uniform_heating_only_multistep_matches_constant_energy_increment() -> None:
    initial = _uniform()
    dt = cfl_timestep(initial, 0.1, GAS, NUMERICAL)
    result = solve_quasi_1d(initial, constant_area_profile(10), 0.1, 2.25 * dt, GAS, NUMERICAL, hydraulic_diameter=0.1, darcy_friction_factor=0.0, wall_heat_flux=50_000.0)
    primitive = conservative_to_primitive(result.U, GAS)
    expected_increment = 4.0 * 50_000.0 / 0.1 * result.time
    assert result.steps >= 3
    assert_allclose(result.U[:, 0], initial[:, 0], rtol=0.0, atol=1e-10)
    assert_allclose(result.U[:, 1], initial[:, 1], rtol=0.0, atol=1e-8)
    assert_allclose(result.U[:, 2] - initial[:, 2], expected_increment, rtol=0.0, atol=1e-8)
    assert np.all(primitive.T > conservative_to_primitive(initial, GAS).T)
    assert np.all(primitive.p > conservative_to_primitive(initial, GAS).p)


def test_mild_cooling_reaches_final_time_with_physical_state() -> None:
    initial = _uniform()
    result = solve_quasi_1d(initial, constant_area_profile(10), 0.1, 1e-4, GAS, NUMERICAL, hydraulic_diameter=0.1, darcy_friction_factor=0.0, wall_heat_flux=-50_000.0)
    primitive = conservative_to_primitive(result.U, GAS)
    assert result.time == 1e-4
    assert np.all(result.U[:, 2] < initial[:, 2])
    assert np.all(primitive.rho > 0.0) and np.all(primitive.p > 0.0) and np.all(primitive.T > 0.0)


@pytest.mark.parametrize("scheme", ["rusanov", "steger-warming"])
def test_combined_friction_and_heating_smoke_is_physical(scheme: str) -> None:
    initial = _uniform()
    result = solve_quasi_1d(initial, constant_area_profile(10), 0.1, 1e-4, GAS, NUMERICAL, flux_scheme=scheme, hydraulic_diameter=0.1, darcy_friction_factor=0.02, wall_heat_flux=50_000.0)
    primitive = conservative_to_primitive(result.U, GAS)
    assert result.time == 1e-4
    assert np.all(np.abs(primitive.u) < 300.0)
    assert np.all(result.U[:, 2] > initial[:, 2])
    assert np.all(primitive.rho > 0.0) and np.all(primitive.p > 0.0) and np.all(primitive.T > 0.0)


def test_wall_sources_are_evaluated_at_all_three_rk_stages(monkeypatch: pytest.MonkeyPatch) -> None:
    import scramjet1d.solver as solver_module
    initial = _uniform(3)
    dt = cfl_timestep(initial, 0.1, GAS, NUMERICAL)
    states: list[np.ndarray] = []
    rhs_schemes: list[object] = []
    wall_parameters: list[tuple[object, object, object]] = []
    original_source = solver_module.combined_wall_source
    original_rhs = solver_module.quasi_1d_rhs_transmissive

    def record_source(state: np.ndarray, diameter: object, factor: object, heat_flux: object, gas: GasProperties) -> np.ndarray:
        states.append(state.copy())
        wall_parameters.append((diameter, factor, heat_flux))
        return original_source(state, diameter, factor, heat_flux, gas)

    def record_rhs(*args: object, **kwargs: object) -> np.ndarray:
        rhs_schemes.append(kwargs["flux_scheme"])
        return original_rhs(*args, **kwargs)

    monkeypatch.setattr(solver_module, "combined_wall_source", record_source)
    monkeypatch.setattr(solver_module, "quasi_1d_rhs_transmissive", record_rhs)
    result = solve_quasi_1d(initial, constant_area_profile(3), 0.1, 0.5 * dt, GAS, NUMERICAL, flux_scheme="steger-warming", hydraulic_diameter=0.1, darcy_friction_factor=0.02, wall_heat_flux=50_000.0)
    assert result.steps == 1
    assert len(states) == 4
    assert rhs_schemes == ["steger-warming"] * 3
    assert wall_parameters == [(0.1, 0.02, 50_000.0)] * 4
    assert not np.array_equal(states[1], states[2])
    assert not np.array_equal(states[2], states[3])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"darcy_friction_factor": 0.02},
        {"wall_heat_flux": 100_000.0},
        {"hydraulic_diameter": 0.0},
        {"hydraulic_diameter": -0.1},
        {"hydraulic_diameter": 0.1, "darcy_friction_factor": -0.01},
        {"hydraulic_diameter": 0.1, "darcy_friction_factor": np.nan},
        {"hydraulic_diameter": 0.1, "wall_heat_flux": np.inf},
        {"hydraulic_diameter": np.ones(3)},
        {"hydraulic_diameter": 0.1, "darcy_friction_factor": np.ones(3)},
        {"hydraulic_diameter": 0.1, "wall_heat_flux": np.ones(3)},
    ],
)
def test_invalid_wall_configuration_fails_before_cfl(monkeypatch: pytest.MonkeyPatch, kwargs: dict[str, object]) -> None:
    import scramjet1d.solver as solver_module
    monkeypatch.setattr(solver_module, "cfl_timestep", lambda *args: (_ for _ in ()).throw(AssertionError("CFL called")))
    with pytest.raises(ValueError):
        solve_quasi_1d(_uniform(5), constant_area_profile(5), 0.1, 1e-4, GAS, NUMERICAL, **kwargs)


def test_none_diameter_with_zero_scalars_or_arrays_preserves_baseline_and_inputs() -> None:
    initial = _uniform(5)
    factor, heat = np.zeros(5), np.zeros(5)
    initial_before, factor_before, heat_before = initial.copy(), factor.copy(), heat.copy()
    baseline = solve_quasi_1d(initial, constant_area_profile(5), 0.1, 1e-4, GAS, NUMERICAL)
    disabled = solve_quasi_1d(initial, constant_area_profile(5), 0.1, 1e-4, GAS, NUMERICAL, hydraulic_diameter=None, darcy_friction_factor=factor, wall_heat_flux=heat)
    assert_allclose(disabled.U, baseline.U, rtol=0.0, atol=0.0)
    assert_allclose(initial, initial_before)
    assert_allclose(factor, factor_before)
    assert_allclose(heat, heat_before)
