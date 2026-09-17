"""P12 project-defined H2 response sweep.

This is a numerical/application study built on the accepted P11.4 integrated
H2 path. It is NOT a Cao Case 2 reproduction and it does NOT assign ramjet,
scramjet, or dual-mode labels. The equivalence-ratio values below are explicit
project choices used only to observe continuous solver responses.

A sweep point that trips the existing forward-flow guard is recorded as outside
the currently admissible solver path. The guard is not weakened, and such a
point is excluded from continuous-response inference rather than being relabelled
as a physical combustion mode.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json

import numpy as np

from cases.studies import p11_4_project_defined_h2_smoke as baseline
from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.config import NumericalConfig
from scramjet1d.teacher_boundaries import TeacherStaticInletState, teacher_static_inlet_conservative_state
from scramjet1d.teacher_boundary_solver import teacher_boundary_source_rhs
from scramjet1d.teacher_combustion import fuel_stoichiometric_ratio
from scramjet1d.teacher_single_injector import build_teacher_single_injector_mapping
from scramjet1d.teacher_steady_solver import solve_teacher_boundary_steady
from scramjet1d.thermochemistry import mixture_thermo_state
from scramjet1d.variable_composition import variable_composition_conservative_to_primitive
from scramjet1d.variable_state import variable_conservative_to_primitive, variable_primitive_to_conservative

CASE_CLASSIFICATION = "P12_PROJECT_DEFINED_RESPONSE_SWEEP"
NOT_A_SOURCE_REPRODUCTION = True
NO_MODE_LABEL_CLAIM = True
PROJECT_EQUIVALENCE_RATIOS = (0.10, 0.20, 0.30)
TEACHER_EQ_11_46_STEADY_TOLERANCE = 2.0e-5
STATUS_CONVERGED = "CONVERGED"
STATUS_MAX_STEPS = "MAX_STEPS_REACHED"
STATUS_FORWARD_FLOW_GUARD = "FORWARD_FLOW_GUARD_TRIGGERED"
FORWARD_FLOW_GUARD_TEXT = "teacher Eq.11.38 friction adapter currently supports forward axial flow u >= 0 only"


@dataclass(frozen=True)
class ResponsePoint:
    equivalence_ratio: float
    status: str
    converged: bool
    steps: int | None
    density_change: float | None
    normalized_residual: float | None
    fuel_mass_source_kg_per_s: float
    mass_inventory_relative_to_inlet: float | None
    momentum_inventory_relative_to_inlet: float | None
    energy_inventory_relative_to_inlet: float | None
    min_mach: float | None
    max_mach: float | None
    min_pressure_Pa: float | None
    max_pressure_Pa: float | None
    min_temperature_K: float | None
    max_temperature_K: float | None
    note: str | None = None


def _guarded_point(phi: float, fuel_mdot: float, note: str) -> ResponsePoint:
    return ResponsePoint(
        equivalence_ratio=float(phi),
        status=STATUS_FORWARD_FLOW_GUARD,
        converged=False,
        steps=None,
        density_change=None,
        normalized_residual=None,
        fuel_mass_source_kg_per_s=float(fuel_mdot),
        mass_inventory_relative_to_inlet=None,
        momentum_inventory_relative_to_inlet=None,
        energy_inventory_relative_to_inlet=None,
        min_mach=None,
        max_mach=None,
        min_pressure_Pa=None,
        max_pressure_Pa=None,
        min_temperature_K=None,
        max_temperature_K=None,
        note=note,
    )


def run_response_point(
    phi: float,
    cells: int = 20,
    *,
    tolerance: float = TEACHER_EQ_11_46_STEADY_TOLERANCE,
    max_steps: int = 8000,
) -> ResponsePoint:
    if not np.isfinite(phi) or phi <= 0.0:
        raise ValueError("phi must be finite and positive")
    if cells < 4:
        raise ValueError("cells must be at least 4")
    species = build_species_database()
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
    geometry, hydraulic_diameter = baseline.project_geometry(cells)
    inlet = TeacherStaticInletState(
        baseline.INLET_PRESSURE_PA,
        baseline.INLET_TEMPERATURE_K,
        baseline.INLET_VELOCITY_M_PER_S,
    )
    inlet_U = teacher_static_inlet_conservative_state(inlet, mapping, species)
    rows = []
    for i in range(cells):
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

    try:
        result = solve_teacher_boundary_steady(
            np.vstack(rows),
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
        return _guarded_point(phi, fuel_mdot, str(exc))

    primitive = variable_composition_conservative_to_primitive(
        result.U,
        mapping.composition,
        species,
    )
    rhs = teacher_boundary_source_rhs(
        result.U,
        mapping,
        geometry,
        dx,
        inlet,
        species,
        hydraulic_diameter_m=hydraulic_diameter,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=baseline.WALL_HEAT_GRADIENT_J_PER_KG_PER_M,
    )
    inventory_rate = np.sum(rhs * geometry.cell_area[:, None] * dx, axis=0)
    inlet_area = float(geometry.face_area[0])
    u_in = float(inlet.axial_velocity_m_per_s)
    p_in = float(inlet.pressure_Pa)
    mass_scale = abs(float(inlet_U[1]) * inlet_area)
    momentum_scale = abs((float(inlet_U[1]) * u_in + p_in) * inlet_area)
    energy_scale = abs((float(inlet_U[2]) + p_in) * u_in * inlet_area)
    if min(mass_scale, momentum_scale, energy_scale) <= 0.0:
        raise ValueError("inlet conservation scales must be positive")

    status = STATUS_CONVERGED if result.converged else STATUS_MAX_STEPS
    return ResponsePoint(
        equivalence_ratio=float(phi),
        status=status,
        converged=result.converged,
        steps=result.steps,
        density_change=result.density_change,
        normalized_residual=result.normalized_residual,
        fuel_mass_source_kg_per_s=float(np.sum(mapping.fuel_mass_flow_gradient_kg_per_s_per_m) * dx),
        mass_inventory_relative_to_inlet=float(abs(inventory_rate[0]) / mass_scale),
        momentum_inventory_relative_to_inlet=float(abs(inventory_rate[1]) / momentum_scale),
        energy_inventory_relative_to_inlet=float(abs(inventory_rate[2]) / energy_scale),
        min_mach=float(np.min(primitive.Mach)),
        max_mach=float(np.max(primitive.Mach)),
        min_pressure_Pa=float(np.min(primitive.p)),
        max_pressure_Pa=float(np.max(primitive.p)),
        min_temperature_K=float(np.min(primitive.T)),
        max_temperature_K=float(np.max(primitive.T)),
        note=None,
    )


def run_sweep() -> list[ResponsePoint]:
    return [run_response_point(phi) for phi in PROJECT_EQUIVALENCE_RATIOS]


if __name__ == "__main__":
    print(
        json.dumps(
            {
                "classification": CASE_CLASSIFICATION,
                "mode_label_claim": False,
                "points": [asdict(point) for point in run_sweep()],
            },
            indent=2,
            sort_keys=True,
        )
    )