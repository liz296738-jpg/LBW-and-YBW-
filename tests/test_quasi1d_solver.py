"""Integration tests for the P4.3 variable-area quasi-one-dimensional solver."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.boundary import transmissive_ghost_cells
from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.geometry import AreaProfile, constant_area_profile
from scramjet1d.solver import (
    cfl_timestep,
    euler_rhs_transmissive,
    quasi_1d_rhs_transmissive,
    solve_euler_1d,
    solve_quasi_1d,
)
from scramjet1d.spatial import internal_rusanov_fluxes, quasi_1d_residual
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative


GAS = GasProperties()
NUMERICAL = NumericalConfig(cfl=0.5)


def _state(rho: object, u: object, p: object) -> np.ndarray:
    return primitive_to_conservative(rho, u, p, GAS)


def _nonuniform_state() -> np.ndarray:
    return _state([1.0, 0.9, 1.1, 0.8], [300.0, 250.0, 350.0, 280.0], [100_000.0, 95_000.0, 105_000.0, 90_000.0])


def test_transmissive_quasi_rhs_reduces_to_p3_for_constant_area() -> None:
    state = _nonuniform_state()
    geometry = constant_area_profile(state.shape[0], area=0.03)

    assert_allclose(
        quasi_1d_rhs_transmissive(state, geometry, 0.1, GAS),
        euler_rhs_transmissive(state, 0.1, GAS),
        rtol=1e-13,
        atol=1e-13,
    )


def test_transmissive_quasi_rhs_preserves_static_equal_pressure_variable_area() -> None:
    geometry = AreaProfile(
        [1.05, 1.18, 1.32, 1.35, 1.4, 1.6, 1.65, 1.7],
        [1.0, 1.1, 1.25, 1.4, 1.3, 1.5, 1.7, 1.6, 1.8],
    )
    state = _state(np.full(8, 1.2), np.zeros(8), np.full(8, 100_000.0))

    assert_allclose(quasi_1d_rhs_transmissive(state, geometry, 0.1, GAS), 0.0, rtol=0.0, atol=1e-8)


def test_transmissive_quasi_rhs_is_existing_module_assembly() -> None:
    state = _nonuniform_state()
    geometry = AreaProfile([1.1, 1.2, 1.3, 1.4], [1.0, 1.15, 1.25, 1.35, 1.5])
    ghosted = transmissive_ghost_cells(state)
    fluxes = internal_rusanov_fluxes(ghosted, GAS)
    expected = quasi_1d_residual(state, fluxes, geometry, 0.1, GAS)

    assert_allclose(quasi_1d_rhs_transmissive(state, geometry, 0.1, GAS), expected)


def test_constant_area_full_solver_matches_p3_solver() -> None:
    initial = _nonuniform_state()
    baseline = solve_euler_1d(initial, 0.05, 2.3e-4, GAS, NUMERICAL)
    quasi = solve_quasi_1d(initial, constant_area_profile(4, 0.02), 0.05, 2.3e-4, GAS, NUMERICAL)

    assert quasi.time == baseline.time
    assert quasi.steps == baseline.steps
    assert_allclose(quasi.U, baseline.U, rtol=1e-11, atol=1e-10)


def test_variable_area_static_equilibrium_is_preserved_across_multiple_steps() -> None:
    geometry = AreaProfile([1.1, 1.35, 1.4, 1.45, 1.8], [1.0, 1.2, 1.5, 1.3, 1.6, 2.0])
    initial = _state(np.full(5, 1.2), np.zeros(5), np.full(5, 100_000.0))
    dt0 = cfl_timestep(initial, 0.1, GAS, NUMERICAL)

    result = solve_quasi_1d(initial, geometry, 0.1, 4.25 * dt0, GAS, NUMERICAL)

    assert result.steps >= 5
    assert result.time == 4.25 * dt0
    assert_allclose(result.U, initial, rtol=0.0, atol=1e-8)


def test_quasi_solver_does_not_mutate_initial_state() -> None:
    initial = _nonuniform_state()
    original = initial.copy()

    result = solve_quasi_1d(initial, constant_area_profile(4), 0.05, 1e-4, GAS, NUMERICAL)

    assert_allclose(initial, original)
    assert not np.shares_memory(result.U, initial)


def test_quasi_solver_hits_nonintegral_final_time_exactly() -> None:
    initial = _nonuniform_state()
    result = solve_quasi_1d(initial, constant_area_profile(4), 0.05, 2.3e-4, GAS, NUMERICAL)

    assert result.time == 2.3e-4
    assert result.steps > 1


def test_quasi_solver_stops_at_max_steps() -> None:
    with pytest.raises(RuntimeError):
        solve_quasi_1d(_nonuniform_state(), constant_area_profile(4), 0.05, 1e-2, GAS, NUMERICAL, max_steps=1)


@pytest.mark.parametrize("geometry", [None, {}, np.ones(4)])
def test_quasi_rhs_and_solver_reject_wrong_geometry_type(geometry: object) -> None:
    state = _nonuniform_state()
    with pytest.raises(TypeError):
        quasi_1d_rhs_transmissive(state, geometry, 0.1, GAS)
    with pytest.raises(TypeError):
        solve_quasi_1d(state, geometry, 0.1, 1e-4, GAS, NUMERICAL)


@pytest.mark.parametrize("num_cells", [3, 5])
def test_quasi_rhs_and_solver_reject_geometry_cell_count_mismatch(num_cells: int) -> None:
    state = _nonuniform_state()
    geometry = constant_area_profile(num_cells)
    with pytest.raises(ValueError):
        quasi_1d_rhs_transmissive(state, geometry, 0.1, GAS)
    with pytest.raises(ValueError):
        solve_quasi_1d(state, geometry, 0.1, 1e-4, GAS, NUMERICAL)


@pytest.mark.parametrize(
    "initial",
    [
        np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 1.0]]),
        np.array([[1.0, 0.0, -1.0], [1.0, 0.0, 1.0]]),
        np.array([[np.nan, 0.0, 1.0], [1.0, 0.0, 1.0]]),
        np.array([[np.inf, 0.0, 1.0], [1.0, 0.0, 1.0]]),
        np.ones((4, 4)),
        np.ones((1, 3)),
    ],
)
def test_quasi_solver_rejects_invalid_initial_state(initial: np.ndarray) -> None:
    geometry = constant_area_profile(initial.shape[0] if initial.ndim == 2 else 2)
    with pytest.raises(ValueError):
        solve_quasi_1d(initial, geometry, 0.1, 1e-4, GAS, NUMERICAL)


@pytest.mark.parametrize("bad_value", [0.0, -0.1, np.nan, np.inf, [0.1]])
def test_quasi_solver_rejects_invalid_dx_and_final_time(bad_value: object) -> None:
    initial = _nonuniform_state()
    geometry = constant_area_profile(4)
    with pytest.raises(ValueError):
        solve_quasi_1d(initial, geometry, bad_value, 1e-4, GAS, NUMERICAL)
    with pytest.raises(ValueError):
        solve_quasi_1d(initial, geometry, 0.1, bad_value, GAS, NUMERICAL)


@pytest.mark.parametrize("max_steps", [0, -1, True, 3.5, "3", None])
def test_quasi_solver_rejects_invalid_max_steps(max_steps: object) -> None:
    with pytest.raises(ValueError):
        solve_quasi_1d(_nonuniform_state(), constant_area_profile(4), 0.1, 1e-4, GAS, NUMERICAL, max_steps=max_steps)


def test_quasi_solver_recomputes_rhs_at_each_rk_stage(monkeypatch: pytest.MonkeyPatch) -> None:
    import scramjet1d.solver as solver_module

    initial = _nonuniform_state()
    calls: list[np.ndarray] = []
    original_rhs = solver_module.quasi_1d_rhs_transmissive

    def recording_rhs(state: np.ndarray, geometry: AreaProfile, dx: object, gas: GasProperties, **kwargs: object) -> np.ndarray:
        calls.append(state.copy())
        return original_rhs(state, geometry, dx, gas)

    monkeypatch.setattr(solver_module, "quasi_1d_rhs_transmissive", recording_rhs)
    solve_quasi_1d(initial, constant_area_profile(4), 0.05, 1e-5, GAS, NUMERICAL)

    assert len(calls) == 3
    assert not np.array_equal(calls[0], calls[1])
    assert not np.array_equal(calls[1], calls[2])


def test_quasi_solver_computes_cfl_once_per_completed_step(monkeypatch: pytest.MonkeyPatch) -> None:
    import scramjet1d.solver as solver_module

    initial = _nonuniform_state()
    cfl_calls = 0
    rhs_calls = 0
    original_cfl = solver_module.cfl_timestep
    original_rhs = solver_module.quasi_1d_rhs_transmissive

    def recording_cfl(*args: object, **kwargs: object) -> float:
        nonlocal cfl_calls
        cfl_calls += 1
        return original_cfl(*args, **kwargs)

    def recording_rhs(*args: object, **kwargs: object) -> np.ndarray:
        nonlocal rhs_calls
        rhs_calls += 1
        return original_rhs(*args, **kwargs)

    monkeypatch.setattr(solver_module, "cfl_timestep", recording_cfl)
    monkeypatch.setattr(solver_module, "quasi_1d_rhs_transmissive", recording_rhs)
    result = solve_quasi_1d(initial, constant_area_profile(4), 0.05, 2.3e-4, GAS, NUMERICAL)

    assert cfl_calls == result.steps
    assert rhs_calls == 3 * result.steps


def test_variable_area_transient_smoke_case_advances_physically() -> None:
    num_cells = 40
    face_area = np.linspace(1.0, 1.1, num_cells + 1)
    geometry = AreaProfile(0.5 * (face_area[:-1] + face_area[1:]), face_area)
    pressure = np.full(num_cells, 100_000.0)
    pressure[18:22] *= 1.02
    initial = _state(np.ones(num_cells), np.full(num_cells, 200.0), pressure)

    result = solve_quasi_1d(initial, geometry, 0.01, 2.0e-5, GAS, NUMERICAL)
    primitive = conservative_to_primitive(result.U, GAS)

    assert result.time == 2.0e-5
    assert result.steps > 1
    assert np.all(np.isfinite(primitive.rho)) and np.all(primitive.rho > 0.0)
    assert np.all(np.isfinite(primitive.p)) and np.all(primitive.p > 0.0)
    assert np.all(np.isfinite(primitive.T)) and np.all(primitive.T > 0.0)
    assert not np.allclose(result.U, initial)
