"""Baseline constant-area, source-free one-dimensional Euler solver."""

from typing import NamedTuple

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .boundary import transmissive_ghost_cells
from .config import GasProperties, NumericalConfig
from .gas import speed_of_sound
from .spatial import finite_volume_residual, internal_rusanov_fluxes
from .state import conservative_to_primitive
from .time_integration import ssp_rk3_step


class SolverResult(NamedTuple):
    """Final conservative state, final time [s], and completed step count."""

    U: NDArray[np.float64]
    time: float
    steps: int


def _positive_scalar(name: str, value: object) -> float:
    """Return a finite strictly positive scalar."""
    scalar = np.asarray(value, dtype=float)
    if scalar.ndim != 0 or not np.isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"{name} must be a finite and strictly positive scalar")
    return float(scalar)


def cfl_timestep(U: ArrayLike, dx: object, gas: GasProperties, numerical: NumericalConfig) -> float:
    """Return CFL*dx/max(|u|+a) [s] for valid conservative states on a uniform grid."""
    spacing = _positive_scalar("dx", dx)
    primitive = conservative_to_primitive(U, gas)
    maximum_speed = np.max(np.abs(primitive.u) + speed_of_sound(primitive.T, gas))
    if not np.isfinite(maximum_speed) or maximum_speed <= 0.0:
        raise ValueError("maximum wave speed must be finite and strictly positive")
    return float(numerical.cfl * spacing / maximum_speed)


def euler_rhs_transmissive(U: ArrayLike, dx: object, gas: GasProperties) -> NDArray[np.float64]:
    """Return the complete source-free Euler RHS with transmissive edge states."""
    spacing = _positive_scalar("dx", dx)
    ghosted = transmissive_ghost_cells(U)
    interface_fluxes = internal_rusanov_fluxes(ghosted, gas)
    return finite_volume_residual(interface_fluxes, spacing)


def solve_euler_1d(
    U0: ArrayLike,
    dx: object,
    t_final: object,
    gas: GasProperties,
    numerical: NumericalConfig,
    max_steps: int = 100_000,
) -> SolverResult:
    """Advance a uniform-grid baseline Euler state from time zero to t_final [s]."""
    state = np.asarray(U0, dtype=float)
    if state.ndim != 2 or state.shape[-1] != 3 or state.shape[0] < 2:
        raise ValueError("U0 must have shape (N, 3) with N >= 2")
    conservative_to_primitive(state, gas)
    spacing = _positive_scalar("dx", dx)
    final_time = _positive_scalar("t_final", t_final)
    if isinstance(max_steps, (bool, np.bool_)) or not isinstance(max_steps, (int, np.integer)) or max_steps <= 0:
        raise ValueError("max_steps must be a positive integer")

    state = np.array(state, dtype=float, copy=True)
    time = 0.0
    steps = 0

    def rhs(stage_state: NDArray[np.float64]) -> NDArray[np.float64]:
        return euler_rhs_transmissive(stage_state, spacing, gas)

    while time < final_time:
        if steps >= max_steps:
            raise RuntimeError("maximum solver step count reached before t_final")
        dt_cfl = cfl_timestep(state, spacing, gas, numerical)
        remaining = final_time - time
        final_step = dt_cfl >= remaining
        dt = remaining if final_step else dt_cfl
        state = ssp_rk3_step(state, dt, rhs)
        conservative_to_primitive(state, gas)
        steps += 1
        if final_step:
            time = final_time
        else:
            time += dt

    return SolverResult(U=state, time=time, steps=steps)
