"""P14 project-defined inlet-Mach sensitivity on the accepted H2 teacher path.

Scientific scope
----------------
This study varies prescribed inlet Mach only through the existing teacher static
p/T/u boundary parameterization. Static p, static T, dry-air composition,
geometry, equivalence ratio, injection settings, mixing closure and numerical
controls remain frozen.

At fixed T and composition:
    a = sqrt(gamma * R * T)
    u = M_target * a

At fixed p/T/composition/area, density is invariant, so air mass flow changes
linearly with target Mach. With phi frozen, fuel mass flow changes
proportionally so the fuel/air ratio remains fixed. This is therefore a
fixed-static-state inlet-Mach sensitivity, NOT a fixed-total-state flight-Mach
study and NOT a source reproduction or experimental validation.
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
from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.config import NumericalConfig
from scramjet1d.teacher_boundaries import (
    TeacherStaticInletState,
    teacher_static_inlet_conservative_state,
)
from scramjet1d.teacher_boundary_solver import teacher_boundary_source_rhs
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


CASE_CLASSIFICATION = "P14_PROJECT_DEFINED_INLET_MACH_SENSITIVITY"
NOT_A_SOURCE_REPRODUCTION = True
NOT_EXPERIMENTAL_VALIDATION = True
PROJECT_TARGET_MACH_VALUES = (2.0, 2.2, 2.4, 2.6)
PROJECT_CELL_COUNTS = (20, 40)

STATUS_CONVERGED = "CONVERGED"
STATUS_MAX_STEPS = "MAX_STEPS_REACHED"
STATUS_FORWARD_FLOW_GUARD = "FORWARD_FLOW_GUARD_TRIGGERED"
FORWARD_FLOW_GUARD_TEXT = (
    "teacher Eq.11.38 friction adapter currently supports forward axial flow u >= 0 only"
)


@dataclass(frozen=True)
class InletMachPoint:
    target_inlet_mach: float
    actual_inlet_mach: float
    inlet_velocity_m_per_s: float
    inlet_air_mass_flow_kg_per_s: float
    fuel_mass_source_kg_per_s: float
    cells: int
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
    min_pressure_Pa: float | None
    max_pressure_Pa: float | None
    min_temperature_K: float | None
    max_temperature_K: float | None
    note: str | None = None


def _validate_target_mach(value: float) -> float:
    mach = float(value)
    if not math.isfinite(mach) or mach <= 1.0:
        raise ValueError("target inlet Mach must be finite and strictly greater than one")
    return mach


def inlet_air_thermo(species):
    """Return frozen dry-air thermo at the project inlet static temperature."""

    dry_air = lean_reaction_mass_fractions("H2", 0.0, 0.0, species)
    thermo = mixture_thermo_state(baseline.INLET_TEMPERATURE_K, dry_air, species)
    return dry_air, thermo


def inlet_sound_speed_m_per_s(species) -> float:
    """Return a=sqrt(gamma*R*T) for the frozen inlet T/composition."""

    _, thermo = inlet_air_thermo(species)
    sound_speed = math.sqrt(
        thermo.gamma
        * thermo.gas_constant_J_per_kg_K
        * baseline.INLET_TEMPERATURE_K
    )
    if not math.isfinite(sound_speed) or sound_speed <= 0.0:
        raise ValueError("derived inlet sound speed must be finite and positive")
    return sound_speed


def inlet_velocity_for_target_mach(target_mach: float, species) -> float:
    """Map target Mach to the teacher static-inlet axial velocity [m/s]."""

    mach = _validate_target_mach(target_mach)
    return mach * inlet_sound_speed_m_per_s(species)


def build_case(cells: int, target_mach: float):
    """Build one P14 case without changing the accepted P11.4 baseline module."""

    if int(cells) not in PROJECT_CELL_COUNTS:
        raise ValueError(f"cells must be one of {PROJECT_CELL_COUNTS}")
    mach = _validate_target_mach(target_mach)

    species = build_species_database()
    dx = baseline.LENGTH_M / int(cells)
    x = (np.arange(int(cells), dtype=float) + 0.5) * dx
    injector_cell = int(np.argmin(np.abs(x - baseline.INJECTOR_X_M)))
    injector_cell = max(1, min(injector_cell, int(cells) - 1))

    dry_air, thermo = inlet_air_thermo(species)
    velocity = inlet_velocity_for_target_mach(mach, species)
    density = baseline.INLET_PRESSURE_PA / (
        thermo.gas_constant_J_per_kg_K * baseline.INLET_TEMPERATURE_K
    )
    air_mdot = float(density * velocity * baseline.INLET_AREA_M2)
    fuel_mdot = float(
        baseline.EQUIVALENCE_RATIO
        * fuel_stoichiometric_ratio("H2")
        * air_mdot
    )

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
    geometry, hydraulic_diameter = baseline.project_geometry(int(cells))
    inlet = TeacherStaticInletState(
        baseline.INLET_PRESSURE_PA,
        baseline.INLET_TEMPERATURE_K,
        velocity,
    )
    inlet_U = teacher_static_inlet_conservative_state(inlet, mapping, species)
    inlet_primitive = variable_conservative_to_primitive(
        inlet_U,
        mapping.composition.composition_at(0),
        species,
    )
    actual_mach = float(inlet_primitive.Mach)
    if not math.isclose(actual_mach, mach, rel_tol=2.0e-12, abs_tol=2.0e-12):
        raise RuntimeError(
            f"derived teacher inlet Mach {actual_mach:.16g} does not match target {mach:.16g}"
        )

    rows = []
    for i in range(int(cells)):
        composition = mapping.composition.composition_at(i)
        local_thermo = mixture_thermo_state(
            baseline.INLET_TEMPERATURE_K,
            composition,
            species,
        )
        local_density = baseline.INLET_PRESSURE_PA / (
            local_thermo.gas_constant_J_per_kg_K
            * baseline.INLET_TEMPERATURE_K
        )
        rows.append(
            variable_primitive_to_conservative(
                local_density,
                velocity,
                baseline.INLET_TEMPERATURE_K,
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
        actual_mach,
        velocity,
        air_mdot,
        fuel_mdot,
        dry_air,
    )


def _guarded_point(
    *,
    target_mach: float,
    actual_mach: float,
    velocity: float,
    air_mdot: float,
    fuel_mdot: float,
    cells: int,
    note: str,
) -> InletMachPoint:
    return InletMachPoint(
        target_inlet_mach=target_mach,
        actual_inlet_mach=actual_mach,
        inlet_velocity_m_per_s=velocity,
        inlet_air_mass_flow_kg_per_s=air_mdot,
        fuel_mass_source_kg_per_s=fuel_mdot,
        cells=int(cells),
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
        min_pressure_Pa=None,
        max_pressure_Pa=None,
        min_temperature_K=None,
        max_temperature_K=None,
        note=note,
    )


def run_point(target_mach: float, cells: int) -> InletMachPoint:
    (
        species,
        dx,
        mapping,
        geometry,
        hydraulic_diameter,
        inlet,
        U0,
        actual_mach,
        velocity,
        air_mdot,
        fuel_mdot,
        _,
    ) = build_case(int(cells), target_mach)

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
        return _guarded_point(
            target_mach=float(target_mach),
            actual_mach=actual_mach,
            velocity=velocity,
            air_mdot=air_mdot,
            fuel_mdot=fuel_mdot,
            cells=int(cells),
            note=str(exc),
        )

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
    p_in = float(inlet.pressure_Pa)
    mass_scale = abs(float(inlet_U[1]) * inlet_area)
    momentum_scale = abs((float(inlet_U[1]) * velocity + p_in) * inlet_area)
    energy_scale = abs((float(inlet_U[2]) + p_in) * velocity * inlet_area)
    if min(mass_scale, momentum_scale, energy_scale) <= 0.0:
        raise ValueError("inlet conservation scales must be positive")

    status = STATUS_CONVERGED if steady.converged else STATUS_MAX_STEPS
    return InletMachPoint(
        target_inlet_mach=float(target_mach),
        actual_inlet_mach=actual_mach,
        inlet_velocity_m_per_s=velocity,
        inlet_air_mass_flow_kg_per_s=air_mdot,
        fuel_mass_source_kg_per_s=fuel_mdot,
        cells=int(cells),
        status=status,
        converged=steady.converged,
        steps=steady.steps,
        density_change=steady.density_change,
        normalized_residual=steady.normalized_residual,
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
    return abs(float(fine) - float(coarse)) / max(abs(float(fine)), 1.0e-30)


def assemble_study(points: list[InletMachPoint]) -> dict[str, Any]:
    expected = {
        (mach, cells)
        for mach in PROJECT_TARGET_MACH_VALUES
        for cells in PROJECT_CELL_COUNTS
    }
    by_key = {(p.target_inlet_mach, p.cells): p for p in points}
    if set(by_key) != expected or len(points) != len(expected):
        raise ValueError("P14 point set does not match the frozen Mach-by-grid matrix")

    grid_changes: list[dict[str, Any]] = []
    for mach in PROJECT_TARGET_MACH_VALUES:
        coarse = by_key[(mach, PROJECT_CELL_COUNTS[0])]
        fine = by_key[(mach, PROJECT_CELL_COUNTS[1])]
        if coarse.status != STATUS_CONVERGED or fine.status != STATUS_CONVERGED:
            grid_changes.append(
                {
                    "target_inlet_mach": mach,
                    "available": False,
                    "reason": "both grid levels must converge before grid-change diagnostics are reported",
                }
            )
            continue
        grid_changes.append(
            {
                "target_inlet_mach": mach,
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
                "claim_boundary": "robustness diagnostic only; not formal grid independence/GCI",
            }
        )

    species = build_species_database()
    sound_speed = inlet_sound_speed_m_per_s(species)
    return {
        "schema_version": 1,
        "classification": CASE_CLASSIFICATION,
        "not_a_source_reproduction": NOT_A_SOURCE_REPRODUCTION,
        "not_experimental_validation": NOT_EXPERIMENTAL_VALIDATION,
        "varied_parameter": {
            "name": "target_inlet_Mach",
            "sample_values": list(PROJECT_TARGET_MACH_VALUES),
            "sample_policy": "project-defined even grid inside literature-anchored engineering context 2.0-2.6",
        },
        "boundary_parameterization": {
            "static_pressure_Pa": baseline.INLET_PRESSURE_PA,
            "static_temperature_K": baseline.INLET_TEMPERATURE_K,
            "inlet_sound_speed_m_per_s": sound_speed,
            "velocity_rule": "u = M_target * sqrt(gamma*R*T)",
            "equivalence_ratio": baseline.EQUIVALENCE_RATIO,
            "claim_boundary": "fixed-static-state sensitivity; not fixed-total-state flight-Mach performance",
        },
        "frozen_controls": {
            "mixing_C_m": baseline.MIXING_C_M,
            "cfl": baseline.PROJECT_CFL,
            "teacher_eq_11_46_metric_project_tolerance": (
                baseline.DEFAULT_DENSITY_CHANGE_TOLERANCE
            ),
            "max_steps": baseline.DEFAULT_MAX_STEPS,
            "cell_counts": list(PROJECT_CELL_COUNTS),
            "wall_heat_gradient_J_per_kg_per_m": (
                baseline.WALL_HEAT_GRADIENT_J_PER_KG_PER_M
            ),
        },
        "points": [asdict(p) for p in sorted(points, key=lambda p: (p.target_inlet_mach, p.cells))],
        "grid_changes": grid_changes,
        "claim_boundary": (
            "Project-defined fixed-static-state inlet-Mach sensitivity. "
            "No experimental validation, Cao Case 2 reproduction, universal optimum, "
            "flight-Mach performance law, mode classification, or formal grid independence is claimed."
        ),
    }


def run_study() -> dict[str, Any]:
    points = [
        run_point(mach, cells)
        for mach in PROJECT_TARGET_MACH_VALUES
        for cells in PROJECT_CELL_COUNTS
    ]
    return assemble_study(points)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-mach", type=float)
    parser.add_argument("--cells", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if (args.target_mach is None) != (args.cells is None):
        parser.error("--target-mach and --cells must be supplied together")

    if args.target_mach is None:
        payload: Any = run_study()
    else:
        payload = asdict(run_point(args.target_mach, args.cells))

    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
