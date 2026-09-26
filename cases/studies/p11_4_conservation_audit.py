"""Discrete conservation audit for the accepted P11.4 project-defined H2 case.

This is a numerical audit, not source reproduction. For a converged finite-volume
state it checks the domain-integrated semi-discrete balance directly from the
same RHS used by the solver. Inventory-rate residuals are also normalized by
physically meaningful inlet mass, momentum, and total-energy flux scales so the
three equations can be interpreted on comparable dimensionless scales.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json

import numpy as np

from cases.studies.p11_4_project_defined_h2_smoke import (
    DEFAULT_DENSITY_CHANGE_TOLERANCE,
    DEFAULT_MAX_STEPS,
    PROJECT_CFL,
    WALL_HEAT_GRADIENT_J_PER_KG_PER_M,
    build_case,
)
from scramjet1d.config import NumericalConfig
from scramjet1d.teacher_boundaries import teacher_static_inlet_conservative_state
from scramjet1d.teacher_boundary_solver import teacher_boundary_source_rhs
from scramjet1d.teacher_steady_solver import solve_teacher_boundary_steady

CASE_CLASSIFICATION = "PROJECT_DEFINED_DISCRETE_CONSERVATION_AUDIT"
NOT_A_SOURCE_REPRODUCTION = True


@dataclass(frozen=True)
class ConservationAuditResult:
    cells: int
    converged: bool
    density_change: float
    normalized_residual: float
    mass_inventory_rate_kg_per_s: float
    momentum_inventory_rate_N: float
    energy_inventory_rate_W: float
    mass_rate_relative_to_inlet: float
    momentum_rate_relative_to_inlet: float
    energy_rate_relative_to_inlet: float


def run_conservation_audit(
    cells: int = 80,
    *,
    tolerance: float = DEFAULT_DENSITY_CHANGE_TOLERANCE,
    max_steps: int = DEFAULT_MAX_STEPS,
) -> ConservationAuditResult:
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
    steady = solve_teacher_boundary_steady(
        U0,
        mapping,
        geometry,
        dx,
        NumericalConfig(cfl=PROJECT_CFL, tolerance=tolerance),
        inlet,
        species,
        hydraulic_diameter_m=hydraulic_diameter,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=WALL_HEAT_GRADIENT_J_PER_KG_PER_M,
        max_steps=max_steps,
    )
    rhs = teacher_boundary_source_rhs(
        steady.U,
        mapping,
        geometry,
        dx,
        inlet,
        species,
        hydraulic_diameter_m=hydraulic_diameter,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=WALL_HEAT_GRADIENT_J_PER_KG_PER_M,
    )

    # U stores per-volume conservative variables; A*dx is the cell volume.
    # At an exact steady discrete solution the domain-integrated *full* RHS tends
    # to zero because boundary-flux changes and all internal source terms balance.
    inventory_rate = np.sum(rhs * geometry.cell_area[:, None] * dx, axis=0)

    inlet_U = teacher_static_inlet_conservative_state(inlet, mapping, species)
    inlet_area = float(geometry.face_area[0])
    u_in = float(inlet.axial_velocity_m_per_s)
    p_in = float(inlet.pressure_Pa)

    mass_scale = abs(float(inlet_U[1]) * inlet_area)
    momentum_scale = abs((float(inlet_U[1]) * u_in + p_in) * inlet_area)
    energy_scale = abs((float(inlet_U[2]) + p_in) * u_in * inlet_area)
    if min(mass_scale, momentum_scale, energy_scale) <= 0.0:
        raise ValueError("inlet conservation scales must be positive")

    # Keep the independently returned primitive inlet state exercised as part of
    # the accepted case builder contract. Its density must be consistent with the
    # conservative mass flux scale used above.
    inlet_mdot_from_primitive = (
        inlet_primitive.rho * u_in * inlet_area
    )
    if not np.isclose(inlet_mdot_from_primitive, mass_scale, rtol=1.0e-10, atol=1.0e-12):
        raise ValueError("primitive and conservative inlet mass-flow scales disagree")

    return ConservationAuditResult(
        cells=cells,
        converged=steady.converged,
        density_change=steady.density_change,
        normalized_residual=steady.normalized_residual,
        mass_inventory_rate_kg_per_s=float(inventory_rate[0]),
        momentum_inventory_rate_N=float(inventory_rate[1]),
        energy_inventory_rate_W=float(inventory_rate[2]),
        mass_rate_relative_to_inlet=float(abs(inventory_rate[0]) / mass_scale),
        momentum_rate_relative_to_inlet=float(abs(inventory_rate[1]) / momentum_scale),
        energy_rate_relative_to_inlet=float(abs(inventory_rate[2]) / energy_scale),
    )


if __name__ == "__main__":
    print(json.dumps(asdict(run_conservation_audit()), indent=2, sort_keys=True))
