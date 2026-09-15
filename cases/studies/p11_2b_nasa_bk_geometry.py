"""Source-backed quasi-one-dimensional geometry for NASA Burrows-Kurkov.

The source geometry is a rectangular duct of constant width with linear height
expansion from the hydrogen-injection step to the 35.6 cm exit station. No
boundary-layer effective-area correction or injection-plenum area is added.
"""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "cases" / "studies" / "data" / "p11_2b_nasa_bk_geometry_source.json"
EXPECTED_CANDIDATE_ID = "NASA-BURROWS-KURKOV-REACTING-VALIDATION"


@dataclass(frozen=True)
class NasaBKGeometry:
    """Rectangular linear-expansion duct geometry in SI units."""

    x_start_m: float
    x_exit_m: float
    width_m: float
    height_start_m: float
    height_exit_m: float

    @property
    def length_m(self) -> float:
        return self.x_exit_m - self.x_start_m

    @property
    def area_start_m2(self) -> float:
        return self.width_m * self.height_start_m

    @property
    def area_exit_m2(self) -> float:
        return self.width_m * self.height_exit_m

    @property
    def area_ratio(self) -> float:
        return self.area_exit_m2 / self.area_start_m2

    def height(self, x_m: object) -> np.ndarray:
        x = np.asarray(x_m, dtype=float)
        if not np.all(np.isfinite(x)):
            raise ValueError("x_m must be finite")
        tolerance = 1.0e-12
        if np.any(x < self.x_start_m - tolerance) or np.any(x > self.x_exit_m + tolerance):
            raise ValueError("x_m lies outside the source-backed NASA-BK combustor domain")
        xi = (x - self.x_start_m) / self.length_m
        return self.height_start_m + (self.height_exit_m - self.height_start_m) * xi

    def area(self, x_m: object) -> np.ndarray:
        return self.width_m * self.height(x_m)


def _positive(name: str, value: object) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    scalar = float(value)
    if not math.isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return scalar


def load_nasa_bk_geometry_source(path: Path | str = SOURCE_PATH) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as stream:
        record = json.load(stream)

    if record.get("schema_version") != 1:
        raise ValueError("unsupported NASA-BK geometry schema_version")
    if record.get("record_kind") != "validation-geometry-source":
        raise ValueError("unexpected NASA-BK geometry record_kind")
    if record.get("candidate_id") != EXPECTED_CANDIDATE_ID:
        raise ValueError("unexpected NASA-BK geometry candidate_id")
    if record.get("status") != "GEOMETRY_FROZEN_SOURCE_BACKED":
        raise ValueError("NASA-BK geometry source is not frozen")

    source = record.get("source_geometry_si")
    derived = record.get("derived_geometry")
    if not isinstance(source, dict) or not isinstance(derived, dict):
        raise ValueError("NASA-BK geometry record is incomplete")

    x_start = float(source.get("x_start_m"))
    x_exit = _positive("x_exit_m", source.get("x_exit_m"))
    width = _positive("width_m", source.get("width_m"))
    h0 = _positive("height_start_m", source.get("height_start_m"))
    h1 = _positive("height_exit_m", source.get("height_exit_m"))
    if not math.isfinite(x_start) or x_start != 0.0:
        raise ValueError("NASA-BK source origin must remain at the hydrogen injection step")
    if x_exit <= x_start:
        raise ValueError("NASA-BK exit must be downstream of the source origin")
    if source.get("expansion_type") != "linear-height rectangular duct":
        raise ValueError("NASA-BK geometry expansion type drifted")

    geometry = NasaBKGeometry(x_start, x_exit, width, h0, h1)
    expected = {
        "area_start_m2": geometry.area_start_m2,
        "area_exit_m2": geometry.area_exit_m2,
        "area_ratio_exit_over_start": geometry.area_ratio,
    }
    for key, value in expected.items():
        if not math.isclose(float(derived.get(key)), value, rel_tol=0.0, abs_tol=1.0e-14):
            raise ValueError(f"{key} is inconsistent with the frozen source dimensions")
    if derived.get("derivation_class") != "DERIVED_EXACTLY_FROM_SOURCE_DIMENSIONS":
        raise ValueError("NASA-BK geometry derivation class drifted")

    return record


def nasa_bk_geometry(path: Path | str = SOURCE_PATH) -> NasaBKGeometry:
    record = load_nasa_bk_geometry_source(path)
    source = record["source_geometry_si"]
    return NasaBKGeometry(
        x_start_m=float(source["x_start_m"]),
        x_exit_m=float(source["x_exit_m"]),
        width_m=float(source["width_m"]),
        height_start_m=float(source["height_start_m"]),
        height_exit_m=float(source["height_exit_m"]),
    )


def sample_cell_and_face_areas(num_cells: int) -> dict[str, np.ndarray]:
    """Return source-backed cell-centre and face areas for a uniform axial mesh."""

    if not isinstance(num_cells, int) or isinstance(num_cells, bool) or num_cells < 2:
        raise ValueError("num_cells must be an integer >= 2")
    geometry = nasa_bk_geometry()
    x_face = np.linspace(geometry.x_start_m, geometry.x_exit_m, num_cells + 1)
    x_cell = 0.5 * (x_face[:-1] + x_face[1:])
    return {
        "x_face_m": x_face,
        "x_cell_m": x_cell,
        "area_face_m2": geometry.area(x_face),
        "area_cell_m2": geometry.area(x_cell),
    }
