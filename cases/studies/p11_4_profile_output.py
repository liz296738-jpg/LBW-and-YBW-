"""Profile export for the accepted P11.4 project-defined H2 baseline.

This module does not introduce new physics. It reruns the already accepted
project-defined H2 case and freezes full cell-centred flow/composition profiles
for downstream plotting and reporting. It is explicitly not a Cao Case 2
reproduction.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
import json
from pathlib import Path

import numpy as np

from cases.studies.p11_4_project_defined_h2_smoke import (
    WALL_HEAT_GRADIENT_J_PER_KG_PER_M,
    build_case,
)
from scramjet1d.config import NumericalConfig
from scramjet1d.teacher_steady_solver import solve_teacher_boundary_steady
from scramjet1d.variable_composition import variable_composition_conservative_to_primitive

CASE_CLASSIFICATION = "PROJECT_DEFINED_H2_FULL_PROFILE_EXPORT"
NOT_A_SOURCE_REPRODUCTION = True
DEFAULT_CELLS = 80
DEFAULT_TOLERANCE = 2.0e-5

BASE_PROFILE_COLUMNS = (
    "cell",
    "x_m",
    "area_m2",
    "hydraulic_diameter_m",
    "rho_kg_per_m3",
    "u_m_per_s",
    "p_Pa",
    "T_K",
    "Mach",
    "gamma",
    "R_J_per_kg_K",
    "cp_J_per_kg_K",
    "h_J_per_kg",
    "mass_flow_kg_per_s",
    "equivalence_ratio",
    "raw_mixing_efficiency",
    "combustion_efficiency",
    "residual_fuel_mass_flow_kg_per_s",
    "fuel_mass_source_gradient_kg_per_s_per_m",
)


@dataclass(frozen=True)
class ProfileSummary:
    classification: str
    not_a_source_reproduction: bool
    cells: int
    dx_m: float
    converged: bool
    steps: int
    density_change: float
    normalized_residual: float
    species_names: tuple[str, ...]
    min_mass_flow_kg_per_s: float
    max_mass_flow_kg_per_s: float
    min_pressure_Pa: float
    max_pressure_Pa: float
    min_temperature_K: float
    max_temperature_K: float
    min_mach: float
    max_mach: float


def solve_profile(
    cells: int = DEFAULT_CELLS,
    *,
    tolerance: float = DEFAULT_TOLERANCE,
    max_steps: int = 20_000,
) -> tuple[ProfileSummary, tuple[str, ...], list[dict[str, float | int]]]:
    """Solve the accepted baseline and return a full cell-centred profile table."""

    (
        species,
        dx,
        mapping,
        geometry,
        hydraulic_diameter,
        inlet,
        U0,
        _inlet_primitive,
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
    primitive = variable_composition_conservative_to_primitive(
        steady.U,
        mapping.composition,
        species,
    )

    species_columns = tuple(f"Y_{name}" for name in mapping.composition.species_names)
    columns = BASE_PROFILE_COLUMNS + species_columns
    mass_flow = primitive.rho * primitive.u * geometry.cell_area

    rows: list[dict[str, float | int]] = []
    for i in range(cells):
        row: dict[str, float | int] = {
            "cell": i,
            "x_m": float(mapping.x_cell_m[i]),
            "area_m2": float(geometry.cell_area[i]),
            "hydraulic_diameter_m": float(hydraulic_diameter[i]),
            "rho_kg_per_m3": float(primitive.rho[i]),
            "u_m_per_s": float(primitive.u[i]),
            "p_Pa": float(primitive.p[i]),
            "T_K": float(primitive.T[i]),
            "Mach": float(primitive.Mach[i]),
            "gamma": float(primitive.gamma[i]),
            "R_J_per_kg_K": float(primitive.R[i]),
            "cp_J_per_kg_K": float(primitive.cp[i]),
            "h_J_per_kg": float(primitive.h[i]),
            "mass_flow_kg_per_s": float(mass_flow[i]),
            "equivalence_ratio": float(mapping.equivalence_ratio[i]),
            "raw_mixing_efficiency": float(mapping.raw_mixing_efficiency[i]),
            "combustion_efficiency": float(mapping.combustion_efficiency[i]),
            "residual_fuel_mass_flow_kg_per_s": float(
                mapping.residual_fuel_mass_flow_rate_kg_per_s[i]
            ),
            "fuel_mass_source_gradient_kg_per_s_per_m": float(
                mapping.fuel_mass_flow_gradient_kg_per_s_per_m[i]
            ),
        }
        for j, name in enumerate(mapping.composition.species_names):
            row[f"Y_{name}"] = float(mapping.composition.mass_fractions[i, j])
        rows.append(row)

    summary = ProfileSummary(
        classification=CASE_CLASSIFICATION,
        not_a_source_reproduction=NOT_A_SOURCE_REPRODUCTION,
        cells=cells,
        dx_m=float(dx),
        converged=steady.converged,
        steps=steady.steps,
        density_change=steady.density_change,
        normalized_residual=steady.normalized_residual,
        species_names=mapping.composition.species_names,
        min_mass_flow_kg_per_s=float(np.min(mass_flow)),
        max_mass_flow_kg_per_s=float(np.max(mass_flow)),
        min_pressure_Pa=float(np.min(primitive.p)),
        max_pressure_Pa=float(np.max(primitive.p)),
        min_temperature_K=float(np.min(primitive.T)),
        max_temperature_K=float(np.max(primitive.T)),
        min_mach=float(np.min(primitive.Mach)),
        max_mach=float(np.max(primitive.Mach)),
    )
    return summary, columns, rows


def write_profile_artifacts(
    output_directory: str | Path,
    *,
    cells: int = DEFAULT_CELLS,
    tolerance: float = DEFAULT_TOLERANCE,
    max_steps: int = 20_000,
) -> tuple[Path, Path, ProfileSummary]:
    """Write CSV profile and JSON summary, returning both paths and summary."""

    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    summary, columns, rows = solve_profile(
        cells=cells,
        tolerance=tolerance,
        max_steps=max_steps,
    )
    csv_path = output / "p11_4_h2_profile.csv"
    json_path = output / "p11_4_h2_profile_summary.json"

    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(columns))
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(
        json.dumps(asdict(summary), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return csv_path, json_path, summary


if __name__ == "__main__":
    csv_path, json_path, summary = write_profile_artifacts("p11_4_profile_artifacts")
    print(json.dumps(asdict(summary), indent=2, sort_keys=True))
    print(csv_path)
    print(json_path)
