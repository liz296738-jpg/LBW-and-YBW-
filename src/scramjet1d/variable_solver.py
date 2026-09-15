"""Fixed-composition variable-thermochemistry time-marching compatibility solver.

This P11.3B module reuses the project's generic SSP-RK3 integrator with the
isolated variable-thermo quasi-one-dimensional Rusanov operator. It is a
verification bridge toward the teacher-reference second scheme, not yet the
production reacting solver.

Scientific scope
----------------
* composition is fixed in every cell and for all time;
* no fuel injection, reaction, wall heat, or friction source is enabled here;
* transmissive boundaries are a verification boundary path, not the final
  teacher p/T/u inlet and first-order-extrapolation outlet adapter;
* the accepted constant-gamma production solver is untouched.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import NamedTuple

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import NumericalConfig
from .geometry import AreaProfile
from .thermochemistry import SpeciesThermoModel
from .time_integration import ssp_rk3_step
from .variable_euler import variable_quasi_1d_rhs_transmissive
from .variable_state import variable_conservative_to_primitive


class VariableSolverResult(NamedTuple):
    """Final fixed-composition state, time [s], and number of completed RK3 steps."""

    U: NDArray[np.float64]
    time: float
    steps: int


def _positive_scalar(name: str, value: object) -> float:
    scalar = np.asarray(value, dtype=float)
    if scalar.ndim != 0 or not np.isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"{name} must be a finite and strictly positive scalar")
    return float(scalar)


def variable_cfl_timestep(
    U: ArrayLike,
    dx: object,
    numerical: NumericalConfig,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
) -> float:
    """Return ``CFL*dx/max(|u|+sqrt(gamma*R*T))`` for valid variable-thermo states."""

    spacing = _positive_scalar("dx", dx)
    primitive = variable_conservative_to_primitive(U, mass_fractions, species)
    sound_speed = np.sqrt(primitive.gamma * primitive.R * primitive.T)
    maximum_speed = np.max(np.abs(primitive.u) + sound_speed)
    if not np.isfinite(maximum_speed) or maximum_speed <= 0.0:
        raise ValueError("maximum wave speed must be finite and strictly positive")
    return float(numerical.cfl * spacing / maximum_speed)


def variable_quasi_1d_ssp_rk3_step(
    U: ArrayLike,
    geometry: AreaProfile,
    dx: object,
    dt: object,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Advance one source-free quasi-1D fixed-composition SSP-RK3 step."""

    if not isinstance(geometry, AreaProfile):
        raise TypeError("geometry must be an AreaProfile")
    states = np.asarray(U, dtype=float)
    if states.ndim != 2 or states.shape[-1] != 3 or states.shape[0] < 2:
        raise ValueError("U must have shape (N, 3) with N >= 2")
    if geometry.num_cells != states.shape[0]:
        raise ValueError("geometry.num_cells must match U cell count")
    spacing = _positive_scalar("dx", dx)
    timestep = _positive_scalar("dt", dt)
    variable_conservative_to_primitive(states, mass_fractions, species)

    def rhs(stage_state: NDArray[np.float64]) -> NDArray[np.float64]:
        return variable_quasi_1d_rhs_transmissive(
            stage_state,
            geometry,
            spacing,
            mass_fractions,
            species,
        )

    result = ssp_rk3_step(states, timestep, rhs)
    variable_conservative_to_primitive(result, mass_fractions, species)
    return result


def solve_variable_quasi_1d(
    U0: ArrayLike,
    geometry: AreaProfile,
    dx: object,
    t_final: object,
    numerical: NumericalConfig,
    mass_fractions: Mapping[str, float],
    species: Mapping[str, SpeciesThermoModel],
    max_steps: int = 100_000,
) -> VariableSolverResult:
    """Advance the source-free fixed-composition variable-thermo quasi-1D model.

    Each accepted pseudo-time step uses the local variable-property CFL estimate
    computed from the state at the start of that step. SSP-RK3 then advances all
    three conservative variables. Every completed step is revalidated by the
    variable-thermo conservative-to-primitive recovery.
    """

    state = np.asarray(U0, dtype=float)
    if state.ndim != 2 or state.shape[-1] != 3 or state.shape[0] < 2:
        raise ValueError("U0 must have shape (N, 3) with N >= 2")
    if not isinstance(geometry, AreaProfile):
        raise TypeError("geometry must be an AreaProfile")
    if geometry.num_cells != state.shape[0]:
        raise ValueError("geometry.num_cells must match U0 cell count")
    spacing = _positive_scalar("dx", dx)
    final_time = _positive_scalar("t_final", t_final)
    if (
        isinstance(max_steps, (bool, np.bool_))
        or not isinstance(max_steps, (int, np.integer))
        or max_steps <= 0
    ):
        raise ValueError("max_steps must be a positive integer")

    variable_conservative_to_primitive(state, mass_fractions, species)
    state = np.array(state, dtype=float, copy=True)
    time = 0.0
    steps = 0

    def rhs(stage_state: NDArray[np.float64]) -> NDArray[np.float64]:
        return variable_quasi_1d_rhs_transmissive(
            stage_state,
            geometry,
            spacing,
            mass_fractions,
            species,
        )

    while time < final_time:
        if steps >= max_steps:
            raise RuntimeError("maximum solver step count reached before t_final")
        dt_cfl = variable_cfl_timestep(
            state, spacing, numerical, mass_fractions, species
        )
        remaining = final_time - time
        final_step = dt_cfl >= remaining
        dt = remaining if final_step else dt_cfl
        state = ssp_rk3_step(state, dt, rhs)
        variable_conservative_to_primitive(state, mass_fractions, species)
        steps += 1
        if final_step:
            time = final_time
        else:
            time += dt

    return VariableSolverResult(U=state, time=time, steps=steps)
