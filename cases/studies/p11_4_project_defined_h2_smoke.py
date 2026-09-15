"""P11.4 project-defined integrated H2 smoke case.

This is deliberately NOT a Cao Case 2 reproduction. It exercises the accepted
teacher Chapter 11 H2 path with every non-source case input frozen below as a
project choice. The unresolved Eq.11.26 dimensional wall-heat mapping is kept
at zero explicitly.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json

import numpy as np

from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.config import NumericalConfig
from scramjet1d.geometry import AreaProfile
from scramjet1d.teacher_boundaries import (
    TeacherStaticInletState,
    teacher_static_inlet_conservative_state,
)
from scramjet1d.teacher_combustion import (
    fuel_stoichiometric_ratio,
    lean_reaction_mass_fractions,
)
from scramjet1d.teacher_single_injector import build_teacher_single_injector_mapping
from scramjet1d.teacher_steady_solver import solve_teacher_boundary_steady
from scramjet1d.thermochemistry import mixture_thermo_state
from scramjet1d.variable_composition import variable_composition_conservative_to_primitive
from scramjet1d.variable_state import (
    variable_conservative_to_primitive,
    variable_primitive_to_conservative,
)

CASE_CLASSIFICATION = "PROJECT_DEFINED_INTEGRATED_SMOKE_CASE"
NOT_A_SOURCE_REPRODUCTION = True

# PROJECT-DEFINED controls, not Cao Case 2 inputs.
LENGTH_M = 0.40
INLET_AREA_M2 = 0.0040
EXIT_AREA_M2 = 0.0050
COMBUSTOR_HEIGHT_M = 0.040
INLET_PRESSURE_PA = 55_000.0
INLET_TEMPERATURE_K = 800.0
INLET_VELOCITY_M_PER_S = 1250.0
EQUIVALENCE_RATIO = 0.20
INJECTOR_X_M = 0.08
MIXING_C_M = 30.0
INJECTION_MODE = "parallel"
FUEL_TEMPERATURE_K = 450.0
FUEL_AXIAL_VELOCITY_M_PER_S = 120.0
WALL_HEAT_GRADIENT_J_PER_KG_PER_M = 0.0  # Eq.11.26 dimensional mapping unresolved.


@dataclass(frozen=True)
class SmokeResult:
    cells: int
    dx_m: float
    converged: bool
    steps: int
    density_change: float
    normalized_residual: float
    inlet_air_mass_flow_kg_per_s: float
    fuel_mass_source_kg_per_s: float
    min_temperature_K: float
    max_temperature_K: float
    min_pressure_Pa: float
    max_pressure_Pa: float
    min_mach: float
    max_mach: float


def project_geometry(cells: int) -> tuple[AreaProfile, np.ndarray]:
    """Return a mild linear-divergence rectangular project geometry.

    The fixed 40 mm height and linearly increasing area imply a cell-wise width
    and therefore a self-consistent rectangular hydraulic diameter. These are
    project-defined smoke controls, not source-reproduced dimensions.
    """

    if cells < 1:
        raise ValueError("cells must be positive")
    face_area = np.linspace(INLET_AREA_M2, EXIT_AREA_M2, cells + 1)
    cell_area = 0.5 * (face_area[:-1] + face_area[1:])
    geometry = AreaProfile(cell_area=cell_area, face_area=face_area)
    width = cell_area / COMBUSTOR_HEIGHT_M
    hydraulic_diameter = (
        2.0 * COMBUSTOR_HEIGHT_M * width / (COMBUSTOR_HEIGHT_M + width)
    )
    return geometry, np.asarray(hydraulic_diameter, dtype=float)


def project_inlet_air_mass_flow(species) -> float:
    """Derive inlet air mass flow from the frozen p/T/u/inlet-area controls."""

    dry_air = lean_reaction_mass_fractions("H2", 0.0, 0.0, species)
    thermo = mixture_thermo_state(INLET_TEMPERATURE_K, dry_air, species)
    rho = INLET_PRESSURE_PA / (
        thermo.gas_constant_J_per_kg_K * INLET_TEMPERATURE_K
    )
    return float(rho * INLET_VELOCITY_M_PER_S * INLET_AREA_M2)


def build_case(cells: int):
    if cells < 20:
        raise ValueError("smoke case requires at least 20 cells")
    species = build_species_database()
    dx = LENGTH_M / cells
    x = (np.arange(cells, dtype=float) + 0.5) * dx
    injector_cell = int(np.argmin(np.abs(x - INJECTOR_X_M)))
    injector_cell = max(1, min(injector_cell, cells - 1))

    air_mdot = project_inlet_air_mass_flow(species)
    fuel_mdot = EQUIVALENCE_RATIO * fuel_stoichiometric_ratio("H2") * air_mdot
    mapping = build_teacher_single_injector_mapping(
        fuel="H2",
        injected_fuel_mass_flow_rate_kg_per_s=fuel_mdot,
        incoming_air_mass_flow_rate_kg_per_s=air_mdot,
        x_cell_m=x,
        dx_m=dx,
        injector_cell=injector_cell,
        combustor_height_m=COMBUSTOR_HEIGHT_M,
        C_m=MIXING_C_M,
        injection_mode=INJECTION_MODE,
        injected_fuel_temperature_K=FUEL_TEMPERATURE_K,
        injected_fuel_axial_velocity_m_per_s=FUEL_AXIAL_VELOCITY_M_PER_S,
        species=species,
    )
    geometry, hydraulic_diameter = project_geometry(cells)
    inlet = TeacherStaticInletState(
        INLET_PRESSURE_PA,
        INLET_TEMPERATURE_K,
        INLET_VELOCITY_M_PER_S,
    )
    inlet_U = teacher_static_inlet_conservative_state(inlet, mapping, species)
    inlet_primitive = variable_conservative_to_primitive(
        inlet_U, mapping.composition.composition_at(0), species
    )

    # Uniform p/T/u initial field with each cell's prescribed algebraic composition.
    rows = []
    for i in range(cells):
        composition = mapping.composition.composition_at(i)
        thermo = mixture_thermo_state(INLET_TEMPERATURE_K, composition, species)
        rho = INLET_PRESSURE_PA / (
            thermo.gas_constant_J_per_kg_K * INLET_TEMPERATURE_K
        )
        rows.append(
            variable_primitive_to_conservative(
                rho,
                INLET_VELOCITY_M_PER_S,
                INLET_TEMPERATURE_K,
                composition,
                species,
            )
        )
    U0 = np.vstack(rows)
    return (
        species,
        dx,
        mapping,
        geometry,
        hydraulic_diameter,
        inlet,
        U0,
        inlet_primitive,
    )


def run_smoke(
    cells: int = 40,
    *,
    tolerance: float = 2.0e-5,
    max_steps: int = 20_000,
) -> SmokeResult:
    (
        species,
        dx,
        mapping,
        geometry,
        hydraulic_diameter,
        inlet,
        U0,
        inlet_primitive,
    ) = build_case(cells)
    result = solve_teacher_boundary_steady(
        U0,
        mapping,
        geometry,
        dx,
        NumericalConfig(cfl=0.5, tolerance=tolerance),
        inlet,
        species,
        hydraulic_diameter_m=hydraulic_diameter,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=(
            WALL_HEAT_GRADIENT_J_PER_KG_PER_M
        ),
        max_steps=max_steps,
    )
    primitive = variable_composition_conservative_to_primitive(
        result.U, mapping.composition, species
    )
    fuel_integral = float(
        np.sum(mapping.fuel_mass_flow_gradient_kg_per_s_per_m) * dx
    )
    inlet_air_mdot = float(
        inlet_primitive.rho * INLET_VELOCITY_M_PER_S * INLET_AREA_M2
    )
    return SmokeResult(
        cells=cells,
        dx_m=dx,
        converged=result.converged,
        steps=result.steps,
        density_change=result.density_change,
        normalized_residual=result.normalized_residual,
        inlet_air_mass_flow_kg_per_s=inlet_air_mdot,
        fuel_mass_source_kg_per_s=fuel_integral,
        min_temperature_K=float(np.min(primitive.T)),
        max_temperature_K=float(np.max(primitive.T)),
        min_pressure_Pa=float(np.min(primitive.p)),
        max_pressure_Pa=float(np.max(primitive.p)),
        min_mach=float(np.min(primitive.Mach)),
        max_mach=float(np.max(primitive.Mach)),
    )


if __name__ == "__main__":
    print(json.dumps(asdict(run_smoke()), indent=2, sort_keys=True))
