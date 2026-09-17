"""Grid-refined continuation around the project-defined H2 thermal-throat candidate.

The accepted 20-cell continuation placed ``phi=0.26`` inside a project numerical
sonic band while ``phi=0.24`` remained clearly supersonic.  This study repeats
the same composition-consistent continuation path on 20/40/80 cells using a
tighter teacher Eq. 11.46 stopping tolerance before any transition-equivalence-
ratio value is quoted.

The geometry and operating controls remain project-defined.  Cao Eq. (3-2)
provides the physical thermal-throat criterion; this study is not Cao Case 2
reproduction and a solver guard is never converted into a physical mode label.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json

import numpy as np

from cases.studies import p11_4_project_defined_h2_smoke as baseline
from cases.studies import p12_thermal_throat_continuation as continuation
from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.cao_mode_criteria import classify_thermal_throat
from scramjet1d.config import NumericalConfig
from scramjet1d.teacher_boundaries import TeacherStaticInletState
from scramjet1d.teacher_steady_solver import solve_teacher_boundary_steady
from scramjet1d.variable_composition import variable_composition_conservative_to_primitive

CASE_CLASSIFICATION = "P12_PROJECT_DEFINED_THERMAL_THROAT_GRID_SENSITIVITY"
NOT_A_SOURCE_REPRODUCTION = True
GRID_LEVELS = (20, 40, 80)
CONTINUATION_EQUIVALENCE_RATIOS = (0.20, 0.22, 0.24, 0.26)
TARGET_EQUIVALENCE_RATIOS = (0.24, 0.26)
PROJECT_SONIC_TOLERANCE = 1.0e-3
TEACHER_STEADY_TOLERANCE = 2.0e-5


@dataclass(frozen=True)
class GridSensitivityPoint:
    cells: int
    dx_m: float
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


def run_grid_level(
    cells: int,
    *,
    tolerance: float = TEACHER_STEADY_TOLERANCE,
    max_steps: int = 25_000,
) -> list[GridSensitivityPoint]:
    """Run one grid level along the accepted warm-start continuation branch."""

    if cells not in GRID_LEVELS:
        raise ValueError(f"cells must be one of {GRID_LEVELS}")
    if not np.isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("tolerance must be finite and positive")

    species = build_species_database()
    geometry, hydraulic_diameter = baseline.project_geometry(cells)
    inlet = TeacherStaticInletState(
        baseline.INLET_PRESSURE_PA,
        baseline.INLET_TEMPERATURE_K,
        baseline.INLET_VELOCITY_M_PER_S,
    )

    points: list[GridSensitivityPoint] = []
    previous_U = None
    previous_mapping = None

    for index, phi in enumerate(CONTINUATION_EQUIVALENCE_RATIOS):
        dx, mapping = continuation._build_mapping(phi, cells, species)
        if index == 0:
            U0 = continuation._cold_start(mapping, species)
            initialization = "COLD_START"
        else:
            if previous_U is None or previous_mapping is None:
                break
            U0 = continuation.composition_consistent_warm_start(
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
            if continuation.FORWARD_FLOW_GUARD_TEXT not in str(exc):
                raise
            points.append(
                GridSensitivityPoint(
                    cells=cells,
                    dx_m=dx,
                    equivalence_ratio=float(phi),
                    initialization=initialization,
                    status=continuation.STATUS_FORWARD_FLOW_GUARD,
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
        mass_diag, momentum_diag, energy_diag = continuation._inventory_diagnostics(
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
        status = continuation.STATUS_CONVERGED if result.converged else continuation.STATUS_MAX_STEPS
        points.append(
            GridSensitivityPoint(
                cells=cells,
                dx_m=dx,
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


def target_points(points: list[GridSensitivityPoint]) -> list[GridSensitivityPoint]:
    """Return the near-sonic phi points used for cross-grid comparison."""

    return [
        point
        for point in points
        if point.equivalence_ratio in TARGET_EQUIVALENCE_RATIOS
    ]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--cells", type=int, required=True, choices=GRID_LEVELS)
    parser.add_argument("--tolerance", type=float, default=TEACHER_STEADY_TOLERANCE)
    parser.add_argument("--max-steps", type=int, default=25_000)
    args = parser.parse_args()
    points = run_grid_level(args.cells, tolerance=args.tolerance, max_steps=args.max_steps)
    print(
        json.dumps(
            {
                "classification": CASE_CLASSIFICATION,
                "not_a_source_reproduction": NOT_A_SOURCE_REPRODUCTION,
                "cells": args.cells,
                "teacher_steady_tolerance": args.tolerance,
                "project_sonic_tolerance": PROJECT_SONIC_TOLERANCE,
                "points": [asdict(point) for point in points],
            },
            indent=2,
            sort_keys=True,
        )
    )
