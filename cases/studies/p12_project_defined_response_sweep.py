"""P12 project-defined H2 response sweep.

This is a numerical/application study built on the accepted P11.4 integrated
H2 path. It is NOT a Cao Case 2 reproduction and it does NOT assign ramjet,
scramjet, or dual-mode labels. The equivalence-ratio values below are explicit
project choices used only to observe continuous solver responses.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json

import numpy as np

from cases.studies import p11_4_project_defined_h2_smoke as baseline
from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.config import NumericalConfig
from scramjet1d.teacher_boundaries import TeacherStaticInletState, teacher_static_inlet_conservative_state
from scramjet1d.teacher_combustion import fuel_stoichiometric_ratio, lean_reaction_mass_fractions
from scramjet1d.teacher_single_injector import build_teacher_single_injector_mapping
from scramjet1d.teacher_steady_solver import solve_teacher_boundary_steady
from scramjet1d.thermochemistry import mixture_thermo_state
from scramjet1d.variable_composition import variable_composition_conservative_to_primitive
from scramjet1d.variable_state import variable_conservative_to_primitive, variable_primitive_to_conservative

CASE_CLASSIFICATION = "P12_PROJECT_DEFINED_RESPONSE_SWEEP"
NOT_A_SOURCE_REPRODUCTION = True
NO_MODE_LABEL_CLAIM = True
PROJECT_EQUIVALENCE_RATIOS = (0.10, 0.20, 0.30)


@dataclass(frozen=True)
class ResponsePoint:
    equivalence_ratio: float
    converged: bool
    steps: int
    density_change: float
    normalized_residual: float
    fuel_mass_source_kg_per_s: float
    min_mach: float
    max_mach: float
    min_pressure_Pa: float
    max_pressure_Pa: float
    min_temperature_K: float
    max_temperature_K: float


def run_response_point(phi: float, cells: int = 20, *, tolerance: float = 1.0e-4, max_steps: int = 8000) -> ResponsePoint:
    if not np.isfinite(phi) or phi <= 0.0:
        raise ValueError("phi must be finite and positive")
    species = build_species_database()
    dx = baseline.LENGTH_M / cells
    x = (np.arange(cells, dtype=float) + 0.5) * dx
    injector_cell = int(np.argmin(np.abs(x - baseline.INJECTOR_X_M)))
    injector_cell = max(1, min(injector_cell, cells - 1))
    air_mdot = baseline.project_inlet_air_mass_flow(species)
    fuel_mdot = float(phi) * fuel_stoichiometric_ratio("H2") * air_mdot
    mapping = build_teacher_single_injector_mapping(
        fuel="H2", injected_fuel_mass_flow_rate_kg_per_s=fuel_mdot,
        incoming_air_mass_flow_rate_kg_per_s=air_mdot, x_cell_m=x, dx_m=dx,
        injector_cell=injector_cell, combustor_height_m=baseline.COMBUSTOR_HEIGHT_M,
        C_m=baseline.MIXING_C_M, injection_mode=baseline.INJECTION_MODE,
        injected_fuel_temperature_K=baseline.FUEL_TEMPERATURE_K,
        injected_fuel_axial_velocity_m_per_s=baseline.FUEL_AXIAL_VELOCITY_M_PER_S,
        species=species,
    )
    geometry, hydraulic_diameter = baseline.project_geometry(cells)
    inlet = TeacherStaticInletState(baseline.INLET_PRESSURE_PA, baseline.INLET_TEMPERATURE_K, baseline.INLET_VELOCITY_M_PER_S)
    inlet_U = teacher_static_inlet_conservative_state(inlet, mapping, species)
    _ = variable_conservative_to_primitive(inlet_U, mapping.composition.composition_at(0), species)
    rows = []
    for i in range(cells):
        composition = mapping.composition.composition_at(i)
        thermo = mixture_thermo_state(baseline.INLET_TEMPERATURE_K, composition, species)
        rho = baseline.INLET_PRESSURE_PA / (thermo.gas_constant_J_per_kg_K * baseline.INLET_TEMPERATURE_K)
        rows.append(variable_primitive_to_conservative(rho, baseline.INLET_VELOCITY_M_PER_S, baseline.INLET_TEMPERATURE_K, composition, species))
    result = solve_teacher_boundary_steady(
        np.vstack(rows), mapping, geometry, dx, NumericalConfig(cfl=0.5, tolerance=tolerance),
        inlet, species, hydraulic_diameter_m=hydraulic_diameter,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=baseline.WALL_HEAT_GRADIENT_J_PER_KG_PER_M,
        max_steps=max_steps,
    )
    primitive = variable_composition_conservative_to_primitive(result.U, mapping.composition, species)
    return ResponsePoint(
        equivalence_ratio=float(phi), converged=result.converged, steps=result.steps,
        density_change=result.density_change, normalized_residual=result.normalized_residual,
        fuel_mass_source_kg_per_s=float(np.sum(mapping.fuel_mass_flow_gradient_kg_per_s_per_m) * dx),
        min_mach=float(np.min(primitive.Mach)), max_mach=float(np.max(primitive.Mach)),
        min_pressure_Pa=float(np.min(primitive.p)), max_pressure_Pa=float(np.max(primitive.p)),
        min_temperature_K=float(np.min(primitive.T)), max_temperature_K=float(np.max(primitive.T)),
    )


def run_sweep() -> list[ResponsePoint]:
    return [run_response_point(phi) for phi in PROJECT_EQUIVALENCE_RATIOS]


if __name__ == "__main__":
    print(json.dumps({"classification": CASE_CLASSIFICATION, "mode_label_claim": False,
                      "points": [asdict(point) for point in run_sweep()]}, indent=2, sort_keys=True))
