"""Completion tests for P5.3 Steger-Warming solver integration."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.geometry import AreaProfile, constant_area_profile
from scramjet1d.solver import cfl_timestep, solve_quasi_1d
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative

GAS = GasProperties()
NUMERICAL = NumericalConfig()


def make_state(rho: object, velocity: object, pressure: object) -> np.ndarray:
    return primitive_to_conservative(rho, velocity, pressure, GAS)


def test_sw_uniform_flow_is_preserved_for_multiple_cfl_steps() -> None:
    initial = make_state(np.ones(20), np.full(20, 300.0), np.full(20, 100_000.0))
    original = initial.copy()
    dt = cfl_timestep(initial, 0.05, GAS, NUMERICAL)
    result = solve_quasi_1d(initial, constant_area_profile(20), 0.05, 4.25 * dt, GAS, NUMERICAL, flux_scheme="steger-warming")
    assert result.steps >= 5
    assert result.time == 4.25 * dt
    assert_allclose(result.U, initial, rtol=0.0, atol=1e-8)
    assert_allclose(initial, original)


def test_sw_variable_area_static_equilibrium_is_preserved_for_multiple_steps() -> None:
    face = np.array([1.0, 1.1, 1.25, 1.2, 1.35, 1.5])
    geometry = AreaProfile(np.array([1.05, 1.18, 1.23, 1.27, 1.42]), face)
    initial = make_state(np.full(5, 1.2), np.zeros(5), np.full(5, 100_000.0))
    dt = cfl_timestep(initial, 0.1, GAS, NUMERICAL)
    result = solve_quasi_1d(initial, geometry, 0.1, 4.25 * dt, GAS, NUMERICAL, flux_scheme="steger-warming")
    assert result.steps >= 5
    assert_allclose(result.U, initial, rtol=0.0, atol=1e-8)


def test_sw_mild_variable_area_transient_advances_to_physical_state() -> None:
    count = 40
    face = np.linspace(1.0, 1.05, count + 1)
    geometry = AreaProfile(0.5 * (face[:-1] + face[1:]), face)
    pressure = np.full(count, 100_000.0)
    pressure[count // 2 - 2 : count // 2 + 2] *= 1.01
    initial = make_state(np.ones(count), np.full(count, 250.0), pressure)
    dt = cfl_timestep(initial, 0.01, GAS, NUMERICAL)
    result = solve_quasi_1d(initial, geometry, 0.01, 3.25 * dt, GAS, NUMERICAL, flux_scheme="steger-warming")
    primitive = conservative_to_primitive(result.U, GAS)
    assert result.time == 3.25 * dt and result.steps > 1
    assert np.all(primitive.rho > 0.0) and np.all(primitive.p > 0.0) and np.all(primitive.T > 0.0)
    assert not np.allclose(result.U, initial)


def test_sw_scheme_reaches_all_three_rk_rhs_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    import scramjet1d.solver as solver_module
    initial = make_state(np.ones(3), np.full(3, 100.0), np.full(3, 100_000.0))
    seen: list[object] = []
    original = solver_module.quasi_1d_rhs_transmissive
    def recording(state: np.ndarray, geometry: AreaProfile, dx: object, gas: GasProperties, *, flux_scheme: object = "rusanov") -> np.ndarray:
        seen.append(flux_scheme)
        return original(state, geometry, dx, gas, flux_scheme=flux_scheme)
    monkeypatch.setattr(solver_module, "quasi_1d_rhs_transmissive", recording)
    dt = cfl_timestep(initial, 0.1, GAS, NUMERICAL)
    solve_quasi_1d(initial, constant_area_profile(3), 0.1, 0.5 * dt, GAS, NUMERICAL, flux_scheme="steger-warming")
    assert seen == ["steger-warming"] * 3


def test_invalid_scheme_fails_before_cfl(monkeypatch: pytest.MonkeyPatch) -> None:
    import scramjet1d.solver as solver_module
    initial = make_state(np.ones(3), np.zeros(3), np.full(3, 100_000.0))
    monkeypatch.setattr(solver_module, "cfl_timestep", lambda *args: (_ for _ in ()).throw(AssertionError("CFL called")))
    with pytest.raises(ValueError):
        solve_quasi_1d(initial, constant_area_profile(3), 0.1, 1e-5, GAS, NUMERICAL, flux_scheme="hll")


def test_both_schemes_use_the_common_cfl_timestep(monkeypatch: pytest.MonkeyPatch) -> None:
    import scramjet1d.solver as solver_module

    initial = make_state(np.ones(3), np.full(3, 100.0), np.full(3, 100_000.0))
    dt = cfl_timestep(initial, 0.1, GAS, NUMERICAL)
    calls: list[tuple[object, ...]] = []
    original = solver_module.cfl_timestep

    def recording(*args: object) -> float:
        calls.append(args)
        return original(*args)

    monkeypatch.setattr(solver_module, "cfl_timestep", recording)
    for scheme in ("rusanov", "steger-warming"):
        result = solve_quasi_1d(initial, constant_area_profile(3), 0.1, 0.5 * dt, GAS, NUMERICAL, flux_scheme=scheme)
        assert result.steps == 1
    assert len(calls) == 2
