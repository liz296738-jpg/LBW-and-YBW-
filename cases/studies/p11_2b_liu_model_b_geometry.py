"""Source-traceable Liu model-B quasi-one-dimensional area geometry.

This study-layer module converts the evidence records for the Jin-Liu
validation candidate into an ``AreaProfile``.  It deliberately does not define
inlet thermodynamic state, heat release, or a formal validation case.

Evidence classification:
- raw dimensions: SOURCE / source-backed geometric closure;
- 2 deg as wall divergence angle: SOURCE_CORROBORATED_INTERPRETATION;
- radius and area arrays: DERIVED.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from scramjet1d.geometry import AreaProfile


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "cases" / "studies" / "data"
GEOMETRY_RECORD = DATA_DIR / "p11_2b_liu_model_b_geometry_source.json"
ANGLE_RECORD = DATA_DIR / "p11_2b_liu_angle_convention_source.json"


@dataclass(frozen=True)
class LiuModelBAreaGeometry:
    """Uniform-grid geometry and provenance for Liu model B."""

    x_cell_m: NDArray[np.float64]
    x_face_m: NDArray[np.float64]
    profile: AreaProfile
    metadata: dict[str, object]


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        data = json.load(stream)
    if data.get("schema_version") != 1:
        raise ValueError(f"unsupported evidence schema in {path.name}")
    return data


def load_model_b_geometry_evidence(
    geometry_path: Path = GEOMETRY_RECORD,
    angle_path: Path = ANGLE_RECORD,
) -> dict[str, object]:
    """Load and cross-check the two geometry evidence records.

    The angle record is not allowed to silently override the primary geometry
    record.  Shared dimensions and coordinates must agree to roundoff.
    """

    geometry = _load_json(geometry_path)
    angle = _load_json(angle_path)
    candidate = "JIN-LIU-MODEL-B-VALIDATION"
    if geometry.get("candidate_id") != candidate or angle.get("candidate_id") != candidate:
        raise ValueError("geometry evidence records must refer to the Jin-Liu model-B candidate")

    decision = angle.get("interpretation_decision", {})
    if decision.get("classification") != "SOURCE_CORROBORATED_INTERPRETATION":
        raise ValueError("2 deg angle must remain explicitly source-corroborated")
    if decision.get("status") != "READY_FOR_STUDY_LAYER_AREA_PROFILE":
        raise ValueError("angle evidence is not approved for study-layer area geometry")
    if decision.get("primary_source_direct_definition") is not False:
        raise ValueError("primary-source half-angle ambiguity must remain documented")

    geometry_source = geometry["confirmed_geometry_records"]
    coordinate = geometry["coordinate_records"]
    angle_inputs = angle["source_backed_geometry_inputs"]

    checks = {
        "diameter": (
            float(geometry_source["isolator_diameter_m"]),
            float(angle_inputs["constant_section_diameter_m"]),
        ),
        "diverging length": (
            float(geometry_source["downstream_diverging_combustor_length_m_from_SRC10"]),
            float(angle_inputs["diverging_section_length_m"]),
        ),
        "divergence start": (
            float(coordinate["divergence_start_in_solver_coordinates_m"]),
            float(angle_inputs["divergence_start_in_solver_coordinates_m"]),
        ),
        "combustor exit": (
            float(coordinate["combustor_exit_in_solver_coordinates_m"]),
            float(angle_inputs["combustor_exit_in_solver_coordinates_m"]),
        ),
    }
    for name, (primary_value, angle_value) in checks.items():
        if not math.isclose(primary_value, angle_value, rel_tol=0.0, abs_tol=1.0e-15):
            raise ValueError(f"inconsistent {name} between geometry evidence records")

    return {"geometry": geometry, "angle": angle}


def _radius_from_solver_coordinate(
    x_m: NDArray[np.float64],
    *,
    inlet_radius_m: float,
    divergence_start_m: float,
    wall_angle_deg: float,
) -> NDArray[np.float64]:
    if np.any(~np.isfinite(x_m)):
        raise ValueError("coordinates must be finite")
    downstream_distance = np.maximum(x_m - divergence_start_m, 0.0)
    radius = inlet_radius_m + downstream_distance * math.tan(math.radians(wall_angle_deg))
    return np.asarray(radius, dtype=float)


def build_liu_model_b_area_geometry(
    num_cells: int,
    *,
    geometry_path: Path = GEOMETRY_RECORD,
    angle_path: Path = ANGLE_RECORD,
) -> LiuModelBAreaGeometry:
    """Build the source-traceable model-B area profile on a uniform grid.

    Solver coordinate ``x=0`` is station 3 / the injector plane.  The 35 mm
    diameter remains constant through the source-backed replacement tube, then
    the radius grows with the source-corroborated 2 deg wall divergence angle.
    """

    if isinstance(num_cells, (bool, np.bool_)) or not isinstance(num_cells, (int, np.integer)):
        raise ValueError("num_cells must be a positive integer")
    if int(num_cells) <= 0:
        raise ValueError("num_cells must be a positive integer")

    evidence = load_model_b_geometry_evidence(geometry_path, angle_path)
    geometry = evidence["geometry"]
    angle = evidence["angle"]

    source = geometry["confirmed_geometry_records"]
    coordinate = geometry["coordinate_records"]
    decision = angle["interpretation_decision"]

    diameter_m = float(source["isolator_diameter_m"])
    inlet_radius_m = 0.5 * diameter_m
    x_start_m = 0.0
    x_div_m = float(coordinate["divergence_start_in_solver_coordinates_m"])
    x_exit_m = float(coordinate["combustor_exit_in_solver_coordinates_m"])
    wall_angle_deg = float(decision["wall_divergence_angle_deg"])

    if not (0.0 < x_div_m < x_exit_m):
        raise ValueError("evidence must define 0 < divergence start < combustor exit")
    if not (0.0 < wall_angle_deg < 90.0):
        raise ValueError("wall divergence angle must be between 0 and 90 degrees")

    count = int(num_cells)
    x_face = np.linspace(x_start_m, x_exit_m, count + 1, dtype=float)
    x_cell = 0.5 * (x_face[:-1] + x_face[1:])

    face_radius = _radius_from_solver_coordinate(
        x_face,
        inlet_radius_m=inlet_radius_m,
        divergence_start_m=x_div_m,
        wall_angle_deg=wall_angle_deg,
    )
    cell_radius = _radius_from_solver_coordinate(
        x_cell,
        inlet_radius_m=inlet_radius_m,
        divergence_start_m=x_div_m,
        wall_angle_deg=wall_angle_deg,
    )

    face_area = math.pi * face_radius**2
    cell_area = math.pi * cell_radius**2
    profile = AreaProfile(cell_area=cell_area, face_area=face_area)

    x_face.setflags(write=False)
    x_cell.setflags(write=False)

    exit_to_inlet_ratio = float(profile.face_area[-1] / profile.face_area[0])
    expected_ratio = float(angle["derived_area_profile_metrics"]["exit_to_inlet_area_ratio"])
    if not math.isclose(exit_to_inlet_ratio, expected_ratio, rel_tol=2.0e-14, abs_tol=0.0):
        raise ValueError("derived area ratio does not reproduce the tracked evidence record")

    metadata: dict[str, object] = {
        "candidate_id": "JIN-LIU-MODEL-B-VALIDATION",
        "geometry_classification": "DERIVED_FROM_SOURCE_BACKED_GEOMETRY",
        "angle_classification": decision["classification"],
        "primary_source_directly_defines_half_angle": decision["primary_source_direct_definition"],
        "solver_origin": coordinate["preferred_solver_origin"],
        "constant_section_diameter_m": diameter_m,
        "divergence_start_m": x_div_m,
        "combustor_exit_m": x_exit_m,
        "wall_divergence_angle_deg": wall_angle_deg,
        "exit_to_inlet_area_ratio": exit_to_inlet_ratio,
        "formal_case_ready": False,
        "formal_case_blocker_note": (
            "Geometry readiness does not supply the missing same-condition heat-release shape, "
            "absolute energy scale, or Jin/Liu operating-condition identity."
        ),
    }
    return LiuModelBAreaGeometry(
        x_cell_m=x_cell,
        x_face_m=x_face,
        profile=profile,
        metadata=metadata,
    )
