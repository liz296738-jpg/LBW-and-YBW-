"""Prescribed-composition variable-thermochemistry SSP-RK3 compatibility solver.

This P11.3G module time-advances the three quasi-one-dimensional conservative
flow equations while a verified :class:`TeacherCompositionField` is held fixed
in space and time during the complete run.  It is a numerical compatibility
step only: no species-transport PDE, reaction-rate evolution, fuel source, wall
source, or independent chemical heat-release source is introduced here.
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
from .variable_composition import (
    TeacherCompositionField,
    variable_composition_conservative_to_primitive,
)
from .variable_composition_euler import variable_composition_quasi_1d_rhs_transmissive


class VariableCompositionSolverResult(NamedTuple):
    """Final three-equation state, elapsed time [s], and completed RK3 steps."""

    U: NDArray[np.float64]
    time: float
    steps: int


def _positive_scalar(name: str, value: object) -> float:
    scalar = np.asarray(value, dtype=float)
    if scalar.ndim != 0 or not np.isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"{name} must be a finite and strictly positive scalar")
    return float(scalar)


def _validate_state_field_geometry(
    U: ArrayLike,
    field: TeacherCompositionField,
    geometry: AreaProfile,
) -> NDArray[np.float64]:
    if not isinstance(field, TeacherCompositionField):
        raise TypeError("field must be a TeacherCompositionField")
    if not isinstance(geometry, AreaProfile):
        raise TypeError("geometry must be an AreaProfile")
    state = np.asarray(U, dtype=float)
    if state.shape != (field.num_cells, 3) or field.num_cells < 2:
        raise ValueError(
            f"U must have shape ({field.num_cells}, 3) and the field must contain at least two cells"
        )
    if geometry.num_cells != field.num_cells:
        raise ValueError("geometry.num_cells must match the composition field cell count")
    if not np.all(np.isfinite(state)):
        raise ValueError("U must be finite")
    return state


def variable_composition_cfl_timestep(
    U: ArrayLike,
    dx: object,
    numerical: NumericalConfig,
    field: TeacherCompositionField,
    species: Mapping[str, SpeciesThermoModel],
) -> float:
    """Return local-property ``CFL*dx/max(|u|+a)`` for a composition field."""

    if not isinstance(field, TeacherCompositionField):
        raise TypeError("field must be a TeacherCompositionField")
    spacing = _positive_scalar("dx", dx)
    state = np.asarray(U, dtype=float)
    if state.shape != (field.num_cells, 3):
        raise ValueError(f"U must have shape ({field.num_cells}, 3)")
    primitive = variable_composition_conservative_to_primitive(
        state, field, species
    )
    sound_speed = np.sqrt(primitive.gamma * primitive.R * primitive.T)
    maximum_speed = float(np.max(np.abs(primitive.u) + sound_speed))
    if not np.isfinite(maximum_speed) or maximum_speed <= 0.0:
        raise ValueError("maximum wave speed must be finite and strictly positive")
    return float(numerical.cfl * spacing / maximum_speed)


def variable_composition_quasi_1d_ssp_rk3_step(
    U: ArrayLike,
    field: TeacherCompositionField,
    geometry: AreaProfile,
    dx: object,
    dt: object,
    species: Mapping[str, SpeciesThermoModel],
) -> NDArray[np.float64]:
    """Advance one source-free SSP-RK3 step with a fixed composition field."""

    states = _validate_state_field_geometry(U, field, geometry)
    spacing = _positive_scalar("dx", dx)
    timestep = _positive_scalar("dt", dt)
    variable_composition_conservative_to_primitive(states, field, species)

    def rhs(stage_state: NDArray[np.float64]) -> NDArray[np.float64]:
        return variable_composition_quasi_1d_rhs_transmissive(
            stage_state, field, geometry, spacing, species
        )

    result = ssp_rk3_step(states, timestep, rhs)
    variable_composition_conservative_to_primitive(result, field, species)
    return result


def solve_prescribed_composition_quasi_1d(
    U0: ArrayLike,
    field: TeacherCompositionField,
    geometry: AreaProfile,
    dx: object,
    t_final: object,
    numerical: NumericalConfig,
    species: Mapping[str, SpeciesThermoModel],
    max_steps: int = 100_000,
) -> VariableCompositionSolverResult:
    """Advance a source-free quasi-1D flow with prescribed cell composition.

    The same immutable ``field`` is used at every Runge-Kutta stage and every
    timestep.  This deliberately verifies the variable-composition numerical
    path *before* a later teacher closure is allowed to update ``phi``, ``eta``
    or ``Y_i`` from the evolving flow/fuel state.
    """

    state = _validate_state_field_geometry(U0, field, geometry)
    spacing = _positive_scalar("dx", dx)
    final_time = _positive_scalar("t_final", t_final)
    if (
        isinstance(max_steps, (bool, np.bool_))
        or not isinstance(max_steps, (int, np.integer))
        or max_steps <= 0
    ):
        raise ValueError("max_steps must be a positive integer")

    variable_composition_conservative_to_primitive(state, field, species)
    state = np.array(state, dtype=float, copy=True)
    time = 0.0
    steps = 0

    def rhs(stage_state: NDArray[np.float64]) -> NDArray[np.float64]:
        return variable_composition_quasi_1d_rhs_transmissive(
            stage_state, field, geometry, spacing, species
        )

    while time < final_time:
        if steps >= max_steps:
            raise RuntimeError("maximum solver step count reached before t_final")
        dt_cfl = variable_composition_cfl_timestep(
            state, spacing, numerical, field, species
        )
        remaining = final_time - time
        final_step = dt_cfl >= remaining
        dt = remaining if final_step else dt_cfl
        state = ssp_rk3_step(state, dt, rhs)
        variable_composition_conservative_to_primitive(state, field, species)
        steps += 1
        if final_step:
            time = final_time
        else:
            time += dt

    return VariableCompositionSolverResult(U=state, time=time, steps=steps)
