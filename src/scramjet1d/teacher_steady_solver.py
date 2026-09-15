"""Steady pseudo-time wrapper for the teacher-reference integrated Rusanov path.

This module closes the remaining Chapter 11 time-marching compatibility gap
without changing the already accepted boundary/source physics:

* internal interfaces remain the verified variable-composition Rusanov flux;
* the inlet remains prescribed static ``p/T/u`` and the outlet first-order
  extrapolated through :mod:`scramjet1d.teacher_boundary_solver`;
* Eq. (11.38) non-geometric source accounting is unchanged;
* the primary steady stopping diagnostic is the teacher Eq. (11.46) maximum
  relative density change;
* a variable-thermochemistry normalized residual is reported independently as
  a robustness diagnostic and is not substituted for Eq. (11.46).

Teacher Eq. (11.45) contains ``min(dt0, 0.5*dx/max(|u|+c))``.  The repository's
``NumericalConfig(cfl=0.5)`` reproduces the spectral factor.  Because the
photographed source does not freeze a numerical ``dt0``, this wrapper accepts an
optional explicit ``dt_cap_s`` but deliberately introduces no guessed default.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Mapping

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import NumericalConfig
from .geometry import AreaProfile
from .teacher_boundaries import TeacherStaticInletState
from .teacher_boundary_solver import teacher_boundary_source_rhs
from .teacher_single_injector import TeacherSingleInjectorMapping
from .thermochemistry import SpeciesThermoModel
from .time_integration import ssp_rk3_step
from .variable_composition import variable_composition_conservative_to_primitive
from .variable_composition_solver import variable_composition_cfl_timestep


@dataclass(frozen=True)
class TeacherVariableResidualReference:
    """Fixed scales for a dimensionless variable-thermochemistry steady residual."""

    time_scale_s: float
    conservative_scales: NDArray[np.float64]


@dataclass(frozen=True)
class TeacherSteadySolverResult:
    """Final state and auditable steady-termination diagnostics."""

    U: NDArray[np.float64]
    pseudo_time_s: float
    steps: int
    converged: bool
    termination_reason: Literal["converged", "max-steps"]
    density_change: float
    normalized_residual: float
    density_change_history: NDArray[np.float64]
    residual_history: NDArray[np.float64]
    time_history_s: NDArray[np.float64]


def _positive_scalar(name: str, value: object) -> float:
    scalar = np.asarray(value, dtype=float)
    if scalar.ndim != 0 or not np.isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"{name} must be a finite and strictly positive scalar")
    return float(scalar)


def teacher_max_relative_density_change(
    U_previous: ArrayLike,
    U_current: ArrayLike,
) -> float:
    """Return the Chapter 11 Eq. (11.46) density-change diagnostic.

    Density is the first conservative variable, so this definition is valid for
    both constant-property and variable-thermochemistry states and requires no
    calorically-perfect ``GasProperties`` object.
    """

    previous = np.asarray(U_previous, dtype=float)
    current = np.asarray(U_current, dtype=float)
    if previous.ndim != 2 or previous.shape[-1] != 3 or previous.shape[0] < 1:
        raise ValueError("U_previous must have shape (N, 3)")
    if current.shape != previous.shape:
        raise ValueError("U_current must have the same shape as U_previous")
    if not np.all(np.isfinite(previous)) or not np.all(np.isfinite(current)):
        raise ValueError("conservative states must be finite")
    rho_previous = previous[:, 0]
    rho_current = current[:, 0]
    if np.any(rho_previous <= 0.0) or np.any(rho_current <= 0.0):
        raise ValueError("density must remain strictly positive")
    return float(np.max(np.abs((rho_current - rho_previous) / rho_previous)))


def teacher_variable_residual_reference(
    U0: ArrayLike,
    dx_m: object,
    mapping: TeacherSingleInjectorMapping,
    species: Mapping[str, SpeciesThermoModel],
) -> TeacherVariableResidualReference:
    """Build fixed variable-property scales analogous to the legacy steady gate."""

    state = np.asarray(U0, dtype=float)
    n = mapping.composition.num_cells
    if state.shape != (n, 3):
        raise ValueError(f"U0 must have shape ({n}, 3)")
    spacing = _positive_scalar("dx_m", dx_m)
    primitive = variable_composition_conservative_to_primitive(
        state, mapping.composition, species
    )
    sound_speed = np.sqrt(primitive.gamma * primitive.R * primitive.T)
    maximum_wave_speed = float(np.max(np.abs(primitive.u) + sound_speed))
    density_scale = float(np.max(primitive.rho))
    energy_scale = float(np.max(np.abs(state[:, 2])))
    scales = np.array(
        (density_scale, density_scale * maximum_wave_speed, energy_scale),
        dtype=float,
    )
    if (
        not np.isfinite(maximum_wave_speed)
        or maximum_wave_speed <= 0.0
        or not np.all(np.isfinite(scales) & (scales > 0.0))
    ):
        raise ValueError("initial state cannot establish finite positive steady scales")
    return TeacherVariableResidualReference(
        time_scale_s=float(n * spacing / maximum_wave_speed),
        conservative_scales=scales,
    )


def normalized_teacher_variable_residual(
    rhs: ArrayLike,
    reference: TeacherVariableResidualReference,
) -> float:
    """Return a dimensionless max-norm residual using fixed initial-state scales."""

    residual = np.asarray(rhs, dtype=float)
    if residual.ndim != 2 or residual.shape[-1] != 3 or residual.shape[0] < 1:
        raise ValueError("rhs must have shape (N, 3)")
    if not np.all(np.isfinite(residual)):
        raise ValueError("rhs must be finite")
    return float(
        np.max(
            reference.time_scale_s
            * np.max(np.abs(residual), axis=0)
            / reference.conservative_scales
        )
    )


def teacher_eq_11_45_timestep(
    U: ArrayLike,
    dx_m: object,
    numerical: NumericalConfig,
    mapping: TeacherSingleInjectorMapping,
    species: Mapping[str, SpeciesThermoModel],
    *,
    dt_cap_s: object | None = None,
) -> float:
    """Return the teacher-compatible spectral timestep with optional explicit ``dt0``.

    ``NumericalConfig.cfl`` is kept explicit.  A production compatibility case
    should use ``cfl=0.5`` for the photographed Eq. (11.45) spectral factor.
    ``dt_cap_s=None`` means that no source-backed numerical ``dt0`` is available;
    it does not imply an infinite teacher-prescribed cap.
    """

    spectral = variable_composition_cfl_timestep(
        U, dx_m, numerical, mapping.composition, species
    )
    if dt_cap_s is None:
        return spectral
    cap = _positive_scalar("dt_cap_s", dt_cap_s)
    return min(spectral, cap)


def solve_teacher_boundary_steady(
    U0: ArrayLike,
    mapping: TeacherSingleInjectorMapping,
    geometry: AreaProfile,
    dx_m: object,
    numerical: NumericalConfig,
    inlet: TeacherStaticInletState,
    species: Mapping[str, SpeciesThermoModel],
    *,
    hydraulic_diameter_m: ArrayLike,
    wall_specific_heat_gain_gradient_J_per_kg_per_m: ArrayLike,
    dt_cap_s: object | None = None,
    max_steps: int = 100_000,
) -> TeacherSteadySolverResult:
    """March the boundary-complete teacher compatibility model to Eq. (11.46).

    The primary convergence condition is exactly

    ``max_i |(rho_i^(n+1)-rho_i^n)/rho_i^n| <= numerical.tolerance``.

    The normalized semi-discrete residual is computed and returned for auditing
    but is not silently substituted as the teacher stopping condition.
    """

    if not isinstance(mapping, TeacherSingleInjectorMapping):
        raise TypeError("mapping must be a TeacherSingleInjectorMapping")
    if not isinstance(geometry, AreaProfile):
        raise TypeError("geometry must be an AreaProfile")
    n = mapping.composition.num_cells
    state = np.asarray(U0, dtype=float)
    if state.shape != (n, 3):
        raise ValueError(f"U0 must have shape ({n}, 3)")
    if geometry.num_cells != n:
        raise ValueError("geometry.num_cells must match the teacher mapping")
    spacing = _positive_scalar("dx_m", dx_m)
    if (
        isinstance(max_steps, (bool, np.bool_))
        or not isinstance(max_steps, (int, np.integer))
        or max_steps <= 0
    ):
        raise ValueError("max_steps must be a positive integer")

    variable_composition_conservative_to_primitive(
        state, mapping.composition, species
    )
    state = np.array(state, dtype=float, copy=True)
    reference = teacher_variable_residual_reference(
        state, spacing, mapping, species
    )

    density_history: list[float] = []
    residual_history: list[float] = []
    time_history: list[float] = []
    pseudo_time = 0.0
    final_density_change = float("inf")
    final_residual = float("inf")

    def rhs(stage_state: NDArray[np.float64]) -> NDArray[np.float64]:
        return teacher_boundary_source_rhs(
            stage_state,
            mapping,
            geometry,
            spacing,
            inlet,
            species,
            hydraulic_diameter_m=hydraulic_diameter_m,
            wall_specific_heat_gain_gradient_J_per_kg_per_m=(
                wall_specific_heat_gain_gradient_J_per_kg_per_m
            ),
        )

    for step in range(1, int(max_steps) + 1):
        previous = state
        dt = teacher_eq_11_45_timestep(
            previous,
            spacing,
            numerical,
            mapping,
            species,
            dt_cap_s=dt_cap_s,
        )
        state = ssp_rk3_step(previous, dt, rhs)
        variable_composition_conservative_to_primitive(
            state, mapping.composition, species
        )
        pseudo_time += dt
        final_density_change = teacher_max_relative_density_change(previous, state)
        final_residual = normalized_teacher_variable_residual(rhs(state), reference)
        density_history.append(final_density_change)
        residual_history.append(final_residual)
        time_history.append(pseudo_time)

        if final_density_change <= numerical.tolerance:
            return TeacherSteadySolverResult(
                U=state,
                pseudo_time_s=pseudo_time,
                steps=step,
                converged=True,
                termination_reason="converged",
                density_change=final_density_change,
                normalized_residual=final_residual,
                density_change_history=np.asarray(density_history, dtype=float),
                residual_history=np.asarray(residual_history, dtype=float),
                time_history_s=np.asarray(time_history, dtype=float),
            )

    return TeacherSteadySolverResult(
        U=state,
        pseudo_time_s=pseudo_time,
        steps=int(max_steps),
        converged=False,
        termination_reason="max-steps",
        density_change=final_density_change,
        normalized_residual=final_residual,
        density_change_history=np.asarray(density_history, dtype=float),
        residual_history=np.asarray(residual_history, dtype=float),
        time_history_s=np.asarray(time_history, dtype=float),
    )
