"""Source-enabled teacher variable-composition SSP-RK3 compatibility solver.

P11.3K combines three independently verified pieces without changing their
scientific scope:

* the prescribed H2/C2H4 single-injector composition/source mapping;
* the variable-composition quasi-one-dimensional Euler/Rusanov operator;
* the non-geometric Chapter 11 Eq. (11.38) source vector.

The mapping is fixed for one prescribed operating condition during pseudo-time.
State-dependent terms, especially wall friction, are recomputed from every
Runge-Kutta stage state.  Transmissive boundaries and Rusanov fluxes remain
compatibility choices; this module is not yet the final teacher case adapter.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import NamedTuple

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .config import NumericalConfig
from .geometry import AreaProfile
from .teacher_single_injector import TeacherSingleInjectorMapping
from .teacher_sources import teacher_eq_11_38_non_geometric_source
from .thermochemistry import SpeciesThermoModel
from .time_integration import ssp_rk3_step
from .variable_composition import variable_composition_conservative_to_primitive
from .variable_composition_euler import variable_composition_quasi_1d_rhs_transmissive
from .variable_composition_solver import variable_composition_cfl_timestep


class TeacherIntegratedCompatibilityResult(NamedTuple):
    """Final conservative state, pseudo-time [s], and completed RK3 steps."""

    U: NDArray[np.float64]
    time: float
    steps: int


def _positive_scalar(name: str, value: object) -> float:
    scalar = np.asarray(value, dtype=float)
    if scalar.ndim != 0 or not np.isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"{name} must be a finite and strictly positive scalar")
    return float(scalar)


def _validate_mapping_geometry_state(
    U: ArrayLike,
    mapping: TeacherSingleInjectorMapping,
    geometry: AreaProfile,
) -> NDArray[np.float64]:
    if not isinstance(mapping, TeacherSingleInjectorMapping):
        raise TypeError("mapping must be a TeacherSingleInjectorMapping")
    if not isinstance(geometry, AreaProfile):
        raise TypeError("geometry must be an AreaProfile")
    state = np.asarray(U, dtype=float)
    n = mapping.composition.num_cells
    if state.shape != (n, 3):
        raise ValueError(f"U must have shape ({n}, 3)")
    if geometry.num_cells != n:
        raise ValueError("geometry.num_cells must match the single-injector mapping")
    if not np.all(np.isfinite(state)):
        raise ValueError("U must be finite")
    return state


def teacher_single_injector_rhs_transmissive(
    U: ArrayLike,
    mapping: TeacherSingleInjectorMapping,
    geometry: AreaProfile,
    dx_m: object,
    species: Mapping[str, SpeciesThermoModel],
    *,
    hydraulic_diameter_m: ArrayLike,
    wall_specific_heat_gain_gradient_J_per_kg_per_m: ArrayLike,
) -> NDArray[np.float64]:
    """Return Euler/area plus Eq. (11.38) sources for one fixed mapping.

    The geometric ``p*dA/dx`` term comes only from the quasi-1D Euler operator.
    The Eq. (11.38) adapter contributes fuel mass, injected momentum/enthalpy,
    friction and an explicitly supplied dimensional wall-heat gradient.  The
    empirical Eq. (11.26) coefficient is not converted here.
    """

    states = _validate_mapping_geometry_state(U, mapping, geometry)
    spacing = _positive_scalar("dx_m", dx_m)
    # Guard the mapping/solver grid contract even if callers construct the
    # mapping elsewhere and later pass a different dx.
    if not np.allclose(
        np.diff(mapping.x_cell_m),
        spacing,
        rtol=2.0e-12,
        atol=2.0e-14 * max(1.0, spacing),
    ):
        raise ValueError("dx_m must match the grid spacing frozen in the single-injector mapping")

    euler_and_geometry = variable_composition_quasi_1d_rhs_transmissive(
        states,
        mapping.composition,
        geometry,
        spacing,
        species,
    )
    non_geometric = teacher_eq_11_38_non_geometric_source(
        states,
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
    return euler_and_geometry + non_geometric


def teacher_single_injector_ssp_rk3_step(
    U: ArrayLike,
    mapping: TeacherSingleInjectorMapping,
    geometry: AreaProfile,
    dx_m: object,
    dt_s: object,
    species: Mapping[str, SpeciesThermoModel],
    *,
    hydraulic_diameter_m: ArrayLike,
    wall_specific_heat_gain_gradient_J_per_kg_per_m: ArrayLike,
) -> NDArray[np.float64]:
    """Advance one source-enabled SSP-RK3 pseudo-time step.

    The complete RHS is reevaluated for every SSP-RK3 stage, so friction uses
    the stage-local ``rho`` and ``u`` rather than a value frozen from the start
    of the step.
    """

    states = _validate_mapping_geometry_state(U, mapping, geometry)
    spacing = _positive_scalar("dx_m", dx_m)
    timestep = _positive_scalar("dt_s", dt_s)
    variable_composition_conservative_to_primitive(states, mapping.composition, species)

    def rhs(stage_state: NDArray[np.float64]) -> NDArray[np.float64]:
        return teacher_single_injector_rhs_transmissive(
            stage_state,
            mapping,
            geometry,
            spacing,
            species,
            hydraulic_diameter_m=hydraulic_diameter_m,
            wall_specific_heat_gain_gradient_J_per_kg_per_m=wall_specific_heat_gain_gradient_J_per_kg_per_m,
        )

    result = ssp_rk3_step(states, timestep, rhs)
    variable_composition_conservative_to_primitive(result, mapping.composition, species)
    return result


def solve_teacher_single_injector_compatibility(
    U0: ArrayLike,
    mapping: TeacherSingleInjectorMapping,
    geometry: AreaProfile,
    dx_m: object,
    t_final_s: object,
    numerical: NumericalConfig,
    species: Mapping[str, SpeciesThermoModel],
    *,
    hydraulic_diameter_m: ArrayLike,
    wall_specific_heat_gain_gradient_J_per_kg_per_m: ArrayLike,
    max_steps: int = 100_000,
) -> TeacherIntegratedCompatibilityResult:
    """Advance the source-enabled fixed-mapping teacher compatibility model.

    A CFL timestep is recomputed from the variable-composition flow state at the
    start of every accepted pseudo-time step.  The same prescribed operating-
    point mapping is used at all RK stages; no species PDE or dynamic update of
    ``phi``, ``eta`` or ``Y_i`` is introduced.
    """

    state = _validate_mapping_geometry_state(U0, mapping, geometry)
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
        return teacher_single_injector_rhs_transmissive(
            stage_state,
            mapping,
            geometry,
            spacing,
            species,
            hydraulic_diameter_m=hydraulic_diameter_m,
            wall_specific_heat_gain_gradient_J_per_kg_per_m=wall_specific_heat_gain_gradient_J_per_kg_per_m,
        )

    while time < final_time:
        if steps >= max_steps:
            raise RuntimeError("maximum solver step count reached before t_final_s")
        dt_cfl = variable_composition_cfl_timestep(
            state,
            spacing,
            numerical,
            mapping.composition,
            species,
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

    return TeacherIntegratedCompatibilityResult(U=state, time=time, steps=steps)
