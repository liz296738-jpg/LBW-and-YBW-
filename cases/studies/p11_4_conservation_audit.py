"""Discrete conservation audit for the accepted P11.4 project-defined H2 case.

This is a numerical audit, not source reproduction.  For a converged finite-volume
state it checks the domain-integrated semi-discrete balance directly from the
same RHS used by the solver.  The diagnostic deliberately does not invent a
separate analytical boundary-flux convention.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json

import numpy as np

from cases.studies.p11_4_project_defined_h2_smoke import (
    WALL_HEAT_GRADIENT_J_PER_KG_PER_M,
    build_case,
)
from scramjet1d.config import NumericalConfig
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


def run_conservation_audit(
    cells: int = 80,
    *,
    tolerance: float = 2.0e-5,
    max_steps: int = 20_000,
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
        NumericalConfig(cfl=0.5, tolerance=tolerance),
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
    inventory_rate = np.sum(rhs * geometry.cell_area[:, None] * dx, axis=0)
    inlet_mdot = inlet_primitive.rho * inlet.velocity_m_per_s * geometry.face_area[0]
    return ConservationAuditResult(
        cells=cells,
        converged=steady.converged,
        density_change=steady.density_change,
        normalized_residual=steady.normalized_residual,
        mass_inventory_rate_kg_per_s=float(inventory_rate[0]),
        momentum_inventory_rate_N=float(inventory_rate[1]),
        energy_inventory_rate_W=float(inventory_rate[2]),
        mass_rate_relative_to_inlet=float(abs(inventory_rate[0]) / inlet_mdot),
    )


if __name__ == "__main__":
    print(json.dumps(asdict(run_conservation_audit()), indent=2, sort_keys=True))
