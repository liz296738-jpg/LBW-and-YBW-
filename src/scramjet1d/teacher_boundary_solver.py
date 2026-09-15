"""Teacher-boundary source-enabled variable-composition compatibility solver.

This P11.3L layer replaces the earlier transmissive verification inlet with the
source-aligned prescribed static ``p/T/u`` air inlet and retains the teacher's
first-order/zero-gradient outlet semantics. The interior physics and source
accounting are unchanged from P11.3K.

Rusanov remains the internal compatibility flux. This is therefore a boundary-
complete compatibility path, not yet the final teacher Steger-Warming scheme.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import NamedTuple

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import NumericalConfig
from .geometry import AreaProfile
from .teacher_boundaries import TeacherStaticInletState, teacher_boundary_quasi_1d_euler_rhs
from .teacher_single_injector import TeacherSingleInjectorMapping
from .teacher_sources import teacher_eq_11_38_non_geometric_source
from .thermochemistry import SpeciesThermoModel
from .time_integration import ssp_rk3_step
from .variable_composition import variable_composition_conservative_to_primitive
from .variable_composition_solver import variable_composition_cfl_timestep


class TeacherBoundarySolverResult(NamedTuple):
    U: NDArray[np.float64]
    time: float
    steps: int


def _positive_scalar(name: str, value: object) -> float:
    scalar = np.asarray(value, dtype=float)
    if scalar.ndim != 0 or not np.isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"{name} must be a finite and strictly positive scalar")
    return float(scalar)


def teacher_boundary_source_rhs(
    U: ArrayLike,
    mapping: TeacherSingleInjectorMapping,
    geometry: AreaProfile,
    dx_m: object,
    inlet: TeacherStaticInletState,
    species: Mapping[str, SpeciesThermoModel],
    *,
    hydraulic_diameter_m: ArrayLike,
    wall_specific_heat_gain_gradient_J_per_kg_per_m: ArrayLike,
) -> NDArray[np.float64]:
    """Return teacher-boundary Euler/area RHS plus Eq. (11.38) sources."""

    spacing = _positive_scalar("dx_m", dx_m)
    euler = teacher_boundary_quasi_1d_euler_rhs(
        U, mapping, geometry, spacing, inlet, species
    )
    source = teacher_eq_11_38_non_geometric_source(
        U,
        mapping.composition,
        geometry,
        species,
        phi=mapping.equivalence_ratio,
        eta=mapping.combustion_efficiency,
        hydraulic_diameter_m=hydraulic_diameter_m,
        fuel_mass_flow_gradient_kg_per_s_per_m=mapping.fuel_mass_flow_gradient_kg_per_s_per_m,
        fuel_axial_velocity_m_per_s=mapping.fuel_axial_velocity_m_per_s,
        fuel_specific_total_enthalpy_J_per_kg=mapping.fuel_specific_total_enthalpy_J_per_kg,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=wall_specific_heat_gain_gradient_J_per_kg_per_m,
    )
    return euler + source


def teacher_boundary_ssp_rk3_step(
    U: ArrayLike,
    mapping: TeacherSingleInjectorMapping,
    geometry: AreaProfile,
    dx_m: object,
    dt_s: object,
    inlet: TeacherStaticInletState,
    species: Mapping[str, SpeciesThermoModel],
    *,
    hydraulic_diameter_m: ArrayLike,
    wall_specific_heat_gain_gradient_J_per_kg_per_m: ArrayLike,
) -> NDArray[np.float64]:
    """Advance one SSP-RK3 step with prescribed teacher boundary semantics."""

    state = np.asarray(U, dtype=float)
    if state.shape != (mapping.composition.num_cells, 3):
        raise ValueError(f"U must have shape ({mapping.composition.num_cells}, 3)")
    spacing = _positive_scalar("dx_m", dx_m)
    timestep = _positive_scalar("dt_s", dt_s)
    variable_composition_conservative_to_primitive(state, mapping.composition, species)

    def rhs(stage_state: NDArray[np.float64]) -> NDArray[np.float64]:
        return teacher_boundary_source_rhs(
            stage_state,
            mapping,
            geometry,
            spacing,
            inlet,
            species,
            hydraulic_diameter_m=hydraulic_diameter_m,
            wall_specific_heat_gain_gradient_J_per_kg_per_m=wall_specific_heat_gain_gradient_J_per_kg_per_m,
        )

    result = ssp_rk3_step(state, timestep, rhs)
    variable_composition_conservative_to_primitive(result, mapping.composition, species)
    return result


def solve_teacher_boundary_compatibility(
    U0: ArrayLike,
    mapping: TeacherSingleInjectorMapping,
    geometry: AreaProfile,
    dx_m: object,
    t_final_s: object,
    numerical: NumericalConfig,
    inlet: TeacherStaticInletState,
    species: Mapping[str, SpeciesThermoModel],
    *,
    hydraulic_diameter_m: ArrayLike,
    wall_specific_heat_gain_gradient_J_per_kg_per_m: ArrayLike,
    max_steps: int = 100_000,
) -> TeacherBoundarySolverResult:
    """Advance the source-enabled teacher boundary compatibility model."""

    state = np.asarray(U0, dtype=float)
    if state.shape != (mapping.composition.num_cells, 3):
        raise ValueError(f"U0 must have shape ({mapping.composition.num_cells}, 3)")
    if geometry.num_cells != mapping.composition.num_cells:
        raise ValueError("geometry.num_cells must match the teacher mapping")
    spacing = _positive_scalar("dx_m", dx_m)
    final_time = _positive_scalar("t_final_s", t_final_s)
    if (
        isinstance(max_steps, (bool, np.bool_))
        or not isinstance(max_steps, (int, np.integer))
        or max_steps <= 0
    ):
        raise ValueError("max_steps must be a positive integer")
    variable_composition_conservative_to_primitive(state, mapping.composition, species)
    state = np.array(state, dtype=float, copy=True)
    time = 0.0
    steps = 0

    def rhs(stage_state: NDArray[np.float64]) -> NDArray[np.float64]:
        return teacher_boundary_source_rhs(
            stage_state,
            mapping,
            geometry,
            spacing,
            inlet,
            species,
            hydraulic_diameter_m=hydraulic_diameter_m,
            wall_specific_heat_gain_gradient_J_per_kg_per_m=wall_specific_heat_gain_gradient_J_per_kg_per_m,
        )

    while time < final_time:
        if steps >= max_steps:
            raise RuntimeError("maximum solver step count reached before t_final_s")
        dt_cfl = variable_composition_cfl_timestep(
            state, spacing, numerical, mapping.composition, species
        )
        remaining = final_time - time
        final_step = dt_cfl >= remaining
        dt = remaining if final_step else dt_cfl
        state = ssp_rk3_step(state, dt, rhs)
        variable_composition_conservative_to_primitive(state, mapping.composition, species)
        steps += 1
        if final_step:
            time = final_time
        else:
            time += dt

    return TeacherBoundarySolverResult(U=state, time=time, steps=steps)
