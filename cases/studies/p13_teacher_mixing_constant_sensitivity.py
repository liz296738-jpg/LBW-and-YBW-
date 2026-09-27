"""P13 teacher-source-range sensitivity study for Eq.11.20 mixing constant C_m.

The teacher source supplies the admissible C_m range [25, 60].  This study
changes only C_m on the already accepted PROJECT_DEFINED H2 teacher path.
It is a sensitivity/application study, not a Cao Case 2 reproduction and not
experimental validation.

Sampling policy:
- 25.0: teacher-source range lower bound
- 30.0: current project baseline
- 42.5: project-defined arithmetic midpoint of the source range
- 60.0: teacher-source range upper bound

The 20/40-cell pair is a project-defined robustness check.  It is not a formal
asymptotic grid-independence or GCI claim.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from cases.studies import p11_4_project_defined_h2_smoke as baseline
from scramjet1d.config import NumericalConfig
from scramjet1d.teacher_boundaries import teacher_static_inlet_conservative_state
from scramjet1d.teacher_boundary_solver import teacher_boundary_source_rhs
from scramjet1d.teacher_combustion import MIXING_LENGTH_C_M_RANGE
from scramjet1d.teacher_steady_solver import solve_teacher_boundary_steady
from scramjet1d.variable_composition import variable_composition_conservative_to_primitive


CASE_CLASSIFICATION = "PROJECT_DEFINED_TEACHER_SOURCE_RANGE_CM_SENSITIVITY"
NOT_A_SOURCE_REPRODUCTION = True
SOURCE_RANGE = tuple(float(v) for v in MIXING_LENGTH_C_M_RANGE)
PROJECT_SAMPLE_VALUES = (25.0, baseline.MIXING_C_M, 42.5, 60.0)
PROJECT_CELL_COUNTS = (20, 40)
STATUS_CONVERGED = "CONVERGED"
STATUS_MAX_STEPS = "MAX_STEPS_REACHED"
STATUS_FORWARD_FLOW_GUARD = "FORWARD_FLOW_GUARD_TRIGGERED"
FORWARD_FLOW_GUARD_TEXT = (
    "teacher Eq.11.38 friction adapter currently supports forward axial flow u >= 0 only"
)


@dataclass(frozen=True)
class MixingConstantPoint:
    mixing_C_m: float
    cells: int
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


def _validate_C_m(value: float) -> float:
    C_m = float(value)
    lower, upper = SOURCE_RANGE
    if not math.isfinite(C_m) or C_m < lower or C_m > upper:
        raise ValueError(
            f"C_m must be finite and lie in the teacher-source range [{lower:g}, {upper:g}]"
        )
    return C_m


def _guarded_point(C_m: float, cells: int, fuel_mdot: float, note: str) -> MixingConstantPoint:
    return MixingConstantPoint(
        mixing_C_m=C_m,
        cells=int(cells),
        status=STATUS_FORWARD_FLOW_GUARD,
        converged=False,
        steps=None,
        density_change=None,
        normalized_residual=None,
        fuel_mass_source_kg_per_s=fuel_mdot,
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


def run_point(C_m: float, cells: int) -> MixingConstantPoint:
    C_m = _validate_C_m(C_m)
    if int(cells) not in PROJECT_CELL_COUNTS:
        raise ValueError(f"cells must be one of {PROJECT_CELL_COUNTS}")

    (
        species,
        dx,
        mapping,
        geometry,
        hydraulic_diameter,
        inlet,
        U0,
        _,
    ) = baseline.build_case(int(cells), mixing_C_m=C_m)

    fuel_mdot = float(
        np.sum(mapping.fuel_mass_flow_gradient_kg_per_s_per_m) * dx
    )

    try:
        steady = solve_teacher_boundary_steady(
            U0,
            mapping,
            geometry,
            dx,
            NumericalConfig(
                cfl=baseline.PROJECT_CFL,
                tolerance=baseline.DEFAULT_DENSITY_CHANGE_TOLERANCE,
            ),
            inlet,
            species,
            hydraulic_diameter_m=hydraulic_diameter,
            wall_specific_heat_gain_gradient_J_per_kg_per_m=(
                baseline.WALL_HEAT_GRADIENT_J_PER_KG_PER_M
            ),
            max_steps=baseline.DEFAULT_MAX_STEPS,
        )
    except ValueError as exc:
        if FORWARD_FLOW_GUARD_TEXT not in str(exc):
            raise
        return _guarded_point(C_m, int(cells), fuel_mdot, str(exc))

    primitive = variable_composition_conservative_to_primitive(
        steady.U,
        mapping.composition,
        species,
    )
    rhs = teacher_boundary_source_rhs(
        steady.U,
        mapping,
        geometry,
        dx,
        inlet,
        species,
        hydraulic_diameter_m=hydraulic_diameter,
        wall_specific_heat_gain_gradient_J_per_kg_per_m=(
            baseline.WALL_HEAT_GRADIENT_J_PER_KG_PER_M
        ),
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
        raise ValueError("inlet conservation scales must be positive")

    status = STATUS_CONVERGED if steady.converged else STATUS_MAX_STEPS
    return MixingConstantPoint(
        mixing_C_m=C_m,
        cells=int(cells),
        status=status,
        converged=steady.converged,
        steps=steady.steps,
        density_change=steady.density_change,
        normalized_residual=steady.normalized_residual,
        fuel_mass_source_kg_per_s=fuel_mdot,
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


def _relative_change(coarse: float, fine: float) -> float:
    scale = max(abs(float(fine)), 1.0e-30)
    return abs(float(fine) - float(coarse)) / scale


def run_study() -> dict[str, Any]:
    points = [
        run_point(C_m, cells)
        for C_m in PROJECT_SAMPLE_VALUES
        for cells in PROJECT_CELL_COUNTS
    ]
    by_key = {(point.mixing_C_m, point.cells): point for point in points}

    grid_changes: list[dict[str, Any]] = []
    for C_m in PROJECT_SAMPLE_VALUES:
        coarse = by_key[(C_m, PROJECT_CELL_COUNTS[0])]
        fine = by_key[(C_m, PROJECT_CELL_COUNTS[1])]
        if coarse.status != STATUS_CONVERGED or fine.status != STATUS_CONVERGED:
            grid_changes.append(
                {
                    "mixing_C_m": C_m,
                    "available": False,
                    "reason": "both grid levels must converge before a grid-change diagnostic is reported",
                }
            )
            continue
        grid_changes.append(
            {
                "mixing_C_m": C_m,
                "available": True,
                "coarse_cells": coarse.cells,
                "fine_cells": fine.cells,
                "min_mach_relative_change": _relative_change(coarse.min_mach, fine.min_mach),
                "max_pressure_relative_change": _relative_change(
                    coarse.max_pressure_Pa, fine.max_pressure_Pa
                ),
                "max_temperature_relative_change": _relative_change(
                    coarse.max_temperature_K, fine.max_temperature_K
                ),
                "claim_boundary": "sensitivity robustness diagnostic only; not formal grid independence/GCI",
            }
        )

    return {
        "schema_version": 1,
        "classification": CASE_CLASSIFICATION,
        "not_a_source_reproduction": NOT_A_SOURCE_REPRODUCTION,
        "varied_parameter": {
            "name": "C_m",
            "teacher_equation": "Eq.11.20",
            "source_range": list(SOURCE_RANGE),
            "sample_values": list(PROJECT_SAMPLE_VALUES),
            "sample_policy": (
                "source lower bound, existing project baseline, arithmetic source-range midpoint, source upper bound"
            ),
        },
        "frozen_baseline_controls": {
            "case": baseline.CASE_CLASSIFICATION,
            "cfl": baseline.PROJECT_CFL,
            "teacher_eq_11_46_metric_project_tolerance": baseline.DEFAULT_DENSITY_CHANGE_TOLERANCE,
            "max_steps": baseline.DEFAULT_MAX_STEPS,
            "wall_heat_gradient_J_per_kg_per_m": baseline.WALL_HEAT_GRADIENT_J_PER_KG_PER_M,
        },
        "points": [asdict(point) for point in points],
        "grid_changes": grid_changes,
        "claim_boundary": (
            "Project-defined sensitivity over a teacher-source-backed C_m range. "
            "No optimum, experimental validation, Cao Case 2 reproduction, or grid-independent result is claimed."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload = run_study()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
