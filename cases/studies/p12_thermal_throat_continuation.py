"""Guarded continuation study toward Cao's thermal-throat transition boundary.

This is a project-defined numerical continuation experiment on the accepted H2
geometry/model.  Cao's Eq. (3-2) criterion is source-defined, but the operating
points, continuation step size and numerical sonic tolerance remain explicit
project choices.  Solver guards and nonconvergence are never converted into
physical mode labels.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json

import numpy as np

from cases.studies import p11_4_project_defined_h2_smoke as baseline
from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.cao_mode_criteria import classify_thermal_throat
from scramjet1d.config import NumericalConfig
from scramjet1d.teacher_boundaries import TeacherStaticInletState, teacher_static_inlet_conservative_state
from scramjet1d.teacher_boundary_solver import teacher_boundary_source_rhs
from scramjet1d.teacher_combustion import fuel_stoichiometric_ratio
from scramjet1d.teacher_single_injector import build_teacher_single_injector_mapping
from scramjet1d.teacher_steady_solver import solve_teacher_boundary_steady
from scramjet1d.thermochemistry import mixture_thermo_state
from scramjet1d.variable_composition import variable_composition_conservative_to_primitive
from scramjet1d.variable_state import variable_conservative_to_primitive, variable_primitive_to_conservative

CASE_CLASSIFICATION = "P12_PROJECT_DEFINED_WARM_START_CONTINUATION"
NOT_A_SOURCE_REPRODUCTION = True
PROJECT_EQUIVALENCE_RATIOS = (0.20, 0.22, 0.24, 0.26, 0.28, 0.30)
PROJECT_SONIC_TOLERANCE = 1.0e-3
STATUS_CONVERGED = "CONVERGED"
STATUS_MAX_STEPS = "MAX_STEPS_REACHED"
STATUS_FORWARD_FLOW_GUARD = "FORWARD_FLOW_GUARD_TRIGGERED"
FORWARD_FLOW_GUARD_TEXT = "teacher Eq.11.38 friction adapter currently supports forward axial flow u >= 0 only"


@dataclass(frozen=True)
class ContinuationPoint:
    equivalence_ratio: float
    initialization: str
    status: str
    converged: bool
    steps: int | None
    density_change: float | None
    normalized_residual: float | None
    mass_inventory_relative_to_inlet: float | None
    momentum_inventory_relative_to_inlet: float | None
    energy_inventory_relative_to_inlet: float | None
    min_mach: float | None
    max_mach: float | None
    sonic_margin: float | None
    cao_thermal_throat_state: str | None
    note: str | None = None


def _build_mapping(phi: float, cells: int, species: dict):
    dx = baseline.LENGTH_M / cells
    x = (np.arange(cells, dtype=float) + 0.5) * dx
    injector_cell = int(np.argmin(np.abs(x - baseline.INJECTOR_X_M)))
    injector_cell = max(1, min(injector_cell, cells - 1))
    air_mdot = baseline.project_inlet_air_mass_flow(species)
    fuel_mdot = float(phi) * fuel_stoichiometric_ratio("H2") * air_mdot
    mapping = build_teacher_single_injector_mapping(
        fuel="H2",
        injected_fuel_mass_flow_rate_kg_per_s=fuel_mdot,
        incoming_air_mass_flow_rate_kg_per_s=air_mdot,
        x_cell_m=x,
        dx_m=dx,
        injector_cell=injector_cell,
        combustor_height_m=baseline.COMBUSTOR_HEIGHT_M,
        C_m=baseline.MIXING_C_M,
        injection_mode=baseline.INJECTION_MODE,
        injected_fuel_temperature_K=baseline.FUEL_TEMPERATURE_K,
        injected_fuel_axial_velocity_m_per_s=baseline.FUEL_AXIAL_VELOCITY_M_PER_S,
        species=species,
    )
    return dx, mapping


def _cold_start(mapping, species: dict) -> np.ndarray:
    rows = []
    for i in range(mapping.composition.num_cells):
        composition = mapping.composition.composition_at(i)
        thermo = mixture_thermo_state(baseline.INLET_TEMPERATURE_K, composition, species)
        rho = baseline.INLET_PRESSURE_PA / (
            thermo.gas_constant_J_per_kg_K * baseline.INLET_TEMPERATURE_K
        )
        rows.append(
            variable_primitive_to_conservative(
                rho,
                baseline.INLET_VELOCITY_M_PER_S,
                baseline.INLET_TEMPERATURE_K,
                composition,
                species,
            )
        )
    return np.vstack(rows)


def composition_consistent_warm_start(
    previous_U: np.ndarray,
    previous_mapping,
    next_mapping,
    species: dict,
) -> np.ndarray:
    """Remap a converged profile to a new composition while preserving p/T/u.

    Preserving pressure, temperature and velocity avoids reusing conservative
    energy with a different absolute species-energy reference. Density is
    recomputed from the next mixture gas constant. This is only a numerical
    initial-guess strategy; it is not a physical source term or transition rule.
    """

    primitive = variable_composition_conservative_to_primitive(
        previous_U,
        previous_mapping.composition,
        species,
    )
    if primitive.rho.shape[0] != next_mapping.composition.num_cells:
        raise ValueError("previous and next continuation mappings must have equal cell counts")

    rows = []
    for i in range(next_mapping.composition.num_cells):
        composition = next_mapping.composition.composition_at(i)
        temperature = float(primitive.T[i])
        pressure = float(primitive.p[i])
        velocity = float(primitive.u[i])
        thermo = mixture_thermo_state(temperature, composition, species)
        rho = pressure / (thermo.gas_constant_J_per_kg_K * temperature)
        rows.append(
            variable_primitive_to_conservative(
                rho,
                velocity,
                temperature,
                composition,
                species,
            )
        )
    return np.vstack(rows)


def _inventory_diagnostics(U, mapping, geometry, dx, inlet, species, hydraulic_diameter):
    rhs = teacher_boundary_source_rhs(
        U,
        mapping,
        geometry,
        dx,
        inlet,
        species,
        hydraulic_diameter_m=hydraulic_diameter,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=baseline.WALL_HEAT_GRADIENT_J_PER_KG_PER_M,
    )
    inventory_rate = np.sum(rhs * geometry.cell_area[:, None] * dx, axis=0)
    inlet_U = teacher_static_inlet_conservative_state(inlet, mapping, species)
    inlet_area = float(geometry.face_area[0])
    u_in = float(inlet.axial_velocity_m_per_s)
    p_in = float(inlet.pressure_Pa)
    mass_scale = abs(float(inlet_U[1]) * inlet_area)
    momentum_scale = abs((float(inlet_U[1]) * u_in + p_in) * inlet_area)
    energy_scale = abs((float(inlet_U[2]) + p_in) * u_in * inlet_area)
    if min(mass_scale, momentum_scale, energy_scale) <= 0.0:
        raise ValueError("inlet continuation conservation scales must be positive")
    return (
        float(abs(inventory_rate[0]) / mass_scale),
        float(abs(inventory_rate[1]) / momentum_scale),
        float(abs(inventory_rate[2]) / energy_scale),
    )


def run_continuation(
    cells: int = 20,
    *,
    tolerance: float = 1.0e-4,
    max_steps: int = 8000,
) -> list[ContinuationPoint]:
    if cells < 4:
        raise ValueError("cells must be at least 4")
    species = build_species_database()
    geometry, hydraulic_diameter = baseline.project_geometry(cells)
    inlet = TeacherStaticInletState(
        baseline.INLET_PRESSURE_PA,
        baseline.INLET_TEMPERATURE_K,
        baseline.INLET_VELOCITY_M_PER_S,
    )

    points: list[ContinuationPoint] = []
    previous_U = None
    previous_mapping = None

    for index, phi in enumerate(PROJECT_EQUIVALENCE_RATIOS):
        dx, mapping = _build_mapping(phi, cells, species)
        if index == 0:
            U0 = _cold_start(mapping, species)
            initialization = "COLD_START"
        else:
            if previous_U is None or previous_mapping is None:
                break
            U0 = composition_consistent_warm_start(
                previous_U,
                previous_mapping,
                mapping,
                species,
            )
            initialization = "COMPOSITION_CONSISTENT_WARM_START"

        try:
            result = solve_teacher_boundary_steady(
                U0,
                mapping,
                geometry,
                dx,
                NumericalConfig(cfl=0.5, tolerance=tolerance),
                inlet,
                species,
                hydraulic_diameter_m=hydraulic_diameter,
                wall_specific_heat_gain_gradient_J_per_kg_per_m=baseline.WALL_HEAT_GRADIENT_J_PER_KG_PER_M,
                max_steps=max_steps,
            )
        except ValueError as exc:
            if FORWARD_FLOW_GUARD_TEXT not in str(exc):
                raise
            points.append(
                ContinuationPoint(
                    equivalence_ratio=float(phi),
                    initialization=initialization,
                    status=STATUS_FORWARD_FLOW_GUARD,
                    converged=False,
                    steps=None,
                    density_change=None,
                    normalized_residual=None,
                    mass_inventory_relative_to_inlet=None,
                    momentum_inventory_relative_to_inlet=None,
                    energy_inventory_relative_to_inlet=None,
                    min_mach=None,
                    max_mach=None,
                    sonic_margin=None,
                    cao_thermal_throat_state=None,
                    note=str(exc),
                )
            )
            break

        primitive = variable_composition_conservative_to_primitive(
            result.U,
            mapping.composition,
            species,
        )
        mass_diag, momentum_diag, energy_diag = _inventory_diagnostics(
            result.U,
            mapping,
            geometry,
            dx,
            inlet,
            species,
            hydraulic_diameter,
        )
        minimum_mach = float(np.min(primitive.Mach))
        mode_state = None
        if result.converged:
            mode_state = classify_thermal_throat(
                primitive.Mach,
                sonic_tolerance=PROJECT_SONIC_TOLERANCE,
            ).state.value
        status = STATUS_CONVERGED if result.converged else STATUS_MAX_STEPS
        points.append(
            ContinuationPoint(
                equivalence_ratio=float(phi),
                initialization=initialization,
                status=status,
                converged=result.converged,
                steps=result.steps,
                density_change=result.density_change,
                normalized_residual=result.normalized_residual,
                mass_inventory_relative_to_inlet=mass_diag,
                momentum_inventory_relative_to_inlet=momentum_diag,
                energy_inventory_relative_to_inlet=energy_diag,
                min_mach=minimum_mach,
                max_mach=float(np.max(primitive.Mach)),
                sonic_margin=minimum_mach - 1.0,
                cao_thermal_throat_state=mode_state,
                note=None,
            )
        )
        if not result.converged:
            break
        previous_U = result.U
        previous_mapping = mapping

    return points


if __name__ == "__main__":
    print(
        json.dumps(
            {
                "classification": CASE_CLASSIFICATION,
                "not_a_source_reproduction": NOT_A_SOURCE_REPRODUCTION,
                "project_sonic_tolerance": PROJECT_SONIC_TOLERANCE,
                "points": [asdict(point) for point in run_continuation()],
            },
            indent=2,
            sort_keys=True,
        )
    )
