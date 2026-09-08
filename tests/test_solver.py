"""Verification of the constant-area, source-free Euler solver assembly."""

import numpy as np
import pytest

import scramjet1d.boundary as boundary
import scramjet1d.solver as solver
from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.flux import euler_flux, rusanov_flux
from scramjet1d.spatial import internal_rusanov_fluxes
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative
from scramjet1d.time_integration import ssp_rk3_step


GAS = GasProperties()
NUMERICAL = NumericalConfig()


@pytest.fixture
def uniform_state() -> np.ndarray:
    """Twenty identical cells in SI units."""
    return np.tile(primitive_to_conservative(1.2, 500.0, 120_000.0, GAS), (20, 1))


@pytest.mark.parametrize("cfl", [0.5, 1.5])
def test_cfl_formula_uses_fastest_cell_and_absolute_velocity(cfl: float) -> None:
    """Negative velocity can set the global wave speed; CFL has no fixed upper cap."""
    rho = np.array([1.0, 0.8, 1.2])
    u = np.array([200.0, -800.0, 50.0])
    p = np.array([100_000.0, 80_000.0, 150_000.0])
    U = primitive_to_conservative(rho, u, p, GAS)
    dx = 0.02
    expected = cfl * dx / np.max(np.abs(u) + np.sqrt(GAS.gamma * p / rho))

    actual = solver.cfl_timestep(U, dx, GAS, NumericalConfig(cfl=cfl))

    assert isinstance(actual, float)
    assert actual == pytest.approx(expected, rel=1e-12)


@pytest.mark.parametrize("dx", [0.0, -0.1, np.nan, np.inf, [0.1], [0.1, 0.1]])
def test_cfl_rejects_invalid_spacing(uniform_state: np.ndarray, dx: object) -> None:
    with pytest.raises(ValueError, match="dx"):
        solver.cfl_timestep(uniform_state, dx, GAS, NUMERICAL)


def test_uniform_flow_rhs_is_zero(uniform_state: np.ndarray) -> None:
    residual = solver.euler_rhs_transmissive(uniform_state, 0.01, GAS)

    assert residual.shape == uniform_state.shape
    np.testing.assert_allclose(residual, 0.0, rtol=0.0, atol=1e-12)


@pytest.mark.parametrize("batched", [False, True])
def test_rhs_uses_complete_boundary_and_internal_fluxes(batched: bool) -> None:
    """The complete RHS keeps every cell and uses both transmissive edge fluxes."""
    U = primitive_to_conservative(
        [1.0, 0.8, 0.6], [300.0, -100.0, 400.0], [100_000.0, 90_000.0, 80_000.0], GAS
    )
    if batched:
        U = np.stack((U, U[::-1]))
    original = U.copy()
    dx = 0.02
    ghosted = boundary.transmissive_ghost_cells(U)
    interfaces = internal_rusanov_fluxes(ghosted, GAS)
    residual = solver.euler_rhs_transmissive(U, dx, GAS)
    # Approved fluxes form an independent check of the spatial indexing.
    expected_fluxes = np.stack(
        (
            euler_flux(U[..., 0, :], GAS),
            rusanov_flux(U[..., 0, :], U[..., 1, :], GAS),
            rusanov_flux(U[..., 1, :], U[..., 2, :], GAS),
            euler_flux(U[..., 2, :], GAS),
        ),
        axis=-2,
    )

    assert ghosted.shape == U.shape[:-2] + (5, 3)
    assert interfaces.shape == U.shape[:-2] + (4, 3)
    assert residual.shape == U.shape
    np.testing.assert_allclose(interfaces, expected_fluxes, rtol=1e-12)
    np.testing.assert_allclose(residual, -np.diff(expected_fluxes, axis=-2) / dx, rtol=1e-12)
    np.testing.assert_allclose(
        np.sum(residual, axis=-2) * dx,
        expected_fluxes[..., 0, :] - expected_fluxes[..., -1, :],
        rtol=1e-12,
        atol=1e-8,
    )
    np.testing.assert_array_equal(U, original)


def test_uniform_flow_is_preserved_across_multiple_steps(uniform_state: np.ndarray) -> None:
    original = uniform_state.copy()
    dx = 0.01
    initial_dt = solver.cfl_timestep(uniform_state, dx, GAS, NUMERICAL)
    final_time = 3.25 * initial_dt

    result = solver.solve_euler_1d(uniform_state, dx, final_time, GAS, NUMERICAL)

    assert isinstance(result, solver.SolverResult)
    assert result.time == final_time
    assert result.steps == 4
    assert result.U.shape == uniform_state.shape
    np.testing.assert_allclose(result.U, original, rtol=1e-12, atol=1e-12)
    np.testing.assert_array_equal(uniform_state, original)
    assert not np.shares_memory(result.U, uniform_state)


def test_single_final_step_uses_remaining_time(uniform_state: np.ndarray) -> None:
    """A final time smaller than the CFL step is reached in exactly one step."""
    final_time = 0.25 * solver.cfl_timestep(uniform_state, 0.01, GAS, NUMERICAL)
    result = solver.solve_euler_1d(
        uniform_state.tolist(), 0.01, final_time, GAS, NUMERICAL, max_steps=np.int64(1)
    )

    assert result.time == final_time
    assert result.steps == 1
    np.testing.assert_allclose(result.U, uniform_state, rtol=1e-12)


def test_max_steps_rejects_unfinished_result(uniform_state: np.ndarray) -> None:
    with pytest.raises(RuntimeError, match="maximum solver step count"):
        solver.solve_euler_1d(uniform_state, 0.001, 0.001, GAS, NUMERICAL, max_steps=1)


@pytest.mark.parametrize(
    "U0",
    [
        np.ones(3),
        np.ones((1, 3)),
        np.ones((0, 3)),
        np.ones((3, 4)),
        np.ones((2, 3, 3)),
        np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 1.0]]),
        np.array([[-1.0, 0.0, 1.0], [1.0, 0.0, 1.0]]),
        np.array([[1.0, 10.0, 49.0], [1.0, 0.0, 1.0]]),
        np.array([[1.0, np.nan, 1.0], [1.0, 0.0, 1.0]]),
        np.array([[1.0, 0.0, np.inf], [1.0, 0.0, 1.0]]),
    ],
)
def test_solver_rejects_invalid_initial_states(U0: np.ndarray) -> None:
    with pytest.raises(ValueError):
        solver.solve_euler_1d(U0, 0.01, 0.001, GAS, NUMERICAL)


@pytest.mark.parametrize("name", ["dx", "t_final"])
@pytest.mark.parametrize("value", [0.0, -0.1, np.nan, np.inf, [0.1]])
def test_solver_rejects_invalid_scalar_inputs(
    uniform_state: np.ndarray, name: str, value: object
) -> None:
    arguments = {"dx": 0.01, "t_final": 0.001}
    arguments[name] = value
    with pytest.raises(ValueError, match=name):
        solver.solve_euler_1d(uniform_state, gas=GAS, numerical=NUMERICAL, **arguments)


@pytest.mark.parametrize("max_steps", [0, -1, True, np.bool_(True), 3.5, 3.0, "3", None])
def test_solver_rejects_invalid_max_steps(uniform_state: np.ndarray, max_steps: object) -> None:
    with pytest.raises(ValueError, match="max_steps"):
        solver.solve_euler_1d(uniform_state, 0.01, 0.001, GAS, NUMERICAL, max_steps=max_steps)


def test_nonuniform_flow_uses_rk3_stage_states_and_new_cfl_each_step(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Observe real assembled calls so a frozen RHS or extra CFL evaluation is detected."""
    U0 = primitive_to_conservative(
        [1.0, 0.8, 0.6], [0.0, 50.0, 0.0], [100_000.0, 90_000.0, 80_000.0], GAS
    )
    dx = 0.01
    original_cfl = solver.cfl_timestep
    original_rhs = solver.euler_rhs_transmissive
    cfl_states = []
    rhs_states = []

    def observed_cfl(U, dx, gas, numerical):
        cfl_states.append(np.array(U, copy=True))
        return original_cfl(U, dx, gas, numerical)

    def observed_rhs(U, dx, gas):
        rhs_states.append(np.array(U, copy=True))
        return original_rhs(U, dx, gas)

    first_dt = original_cfl(U0, dx, GAS, NUMERICAL)
    expected_first = ssp_rk3_step(U0, first_dt, lambda U: original_rhs(U, dx, GAS))
    monkeypatch.setattr(solver, "cfl_timestep", observed_cfl)
    monkeypatch.setattr(solver, "euler_rhs_transmissive", observed_rhs)

    result = solver.solve_euler_1d(U0, dx, 1.5 * first_dt, GAS, NUMERICAL)

    assert result.steps > 1
    assert len(cfl_states) == result.steps
    assert len(rhs_states) == 3 * result.steps
    np.testing.assert_array_equal(rhs_states[0], U0)
    assert not np.allclose(rhs_states[0], rhs_states[1])
    assert not np.allclose(rhs_states[1], rhs_states[2])
    np.testing.assert_allclose(cfl_states[1], expected_first, rtol=1e-12)
    np.testing.assert_array_equal(cfl_states[1], rhs_states[3])


def test_solver_rejects_nonphysical_completed_rk_step(
    uniform_state: np.ndarray, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A finite but nonphysical RK result must be rejected even on the final step."""
    def nonphysical_step(U, dt, rhs):
        result = np.array(U, copy=True)
        result[0] = [1.0, 10.0, 49.0]
        return result

    monkeypatch.setattr(solver, "ssp_rk3_step", nonphysical_step)
    with pytest.raises(ValueError, match="p"):
        solver.solve_euler_1d(uniform_state, 0.01, 1e-8, GAS, NUMERICAL)


def test_sod_shock_tube_reaches_final_time_with_positive_states() -> None:
    """100-cell dimensional Sod case is a CFD integration smoke test, not exact validation."""
    cell_count = 100
    dx = 1.0 / cell_count
    x = (np.arange(cell_count) + 0.5) * dx
    rho = np.where(x < 0.5, 1.0, 0.125)
    p = np.where(x < 0.5, 100_000.0, 10_000.0)
    U0 = primitive_to_conservative(rho, np.zeros(cell_count), p, GAS)
    original = U0.copy()

    result = solver.solve_euler_1d(U0, dx, 5e-4, GAS, NUMERICAL)
    primitive = conservative_to_primitive(result.U, GAS)

    assert result.time == 5e-4
    assert result.steps > 1
    assert np.isfinite(np.stack(primitive)).all()
    assert np.all(primitive.rho > 0.0)
    assert np.all(primitive.p > 0.0)
    assert np.all(primitive.T > 0.0)
    assert np.max(np.abs(primitive.u)) > 1.0
    initial_levels = np.isclose(primitive.rho, 1.0) | np.isclose(primitive.rho, 0.125)
    assert np.any(~initial_levels)
    np.testing.assert_array_equal(U0, original)
