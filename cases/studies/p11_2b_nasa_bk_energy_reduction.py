"""Conservative NASA Burrows-Kurkov reference-solution energy reduction.

The frozen curve in ``p11_2b_nasa_bk_reference_delta_h0.csv`` is derived from
the public Wind-US reference solution, not from the experimental exit profiles.
This module maps that source-backed *specific* total-enthalpy change onto an
arbitrary one-dimensional mesh using the one-dimensional inlet mass flow.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "cases" / "studies" / "data" / "p11_2b_nasa_bk_reference_delta_h0.csv"
PROVENANCE_PATH = ROOT / "cases" / "studies" / "data" / "p11_2b_nasa_bk_reference_energy_reduction.json"
EXPECTED_CANDIDATE_ID = "NASA-BURROWS-KURKOV-REACTING-VALIDATION"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_energy_reduction(
    data_path: Path | str = DATA_PATH,
    provenance_path: Path | str = PROVENANCE_PATH,
) -> dict[str, Any]:
    """Load and validate the frozen Delta-h0 curve and provenance ledger."""

    data_path = Path(data_path)
    provenance_path = Path(provenance_path)
    with provenance_path.open("r", encoding="utf-8") as stream:
        provenance = json.load(stream)
    if provenance.get("schema_version") != 1:
        raise ValueError("unsupported NASA-BK energy-reduction schema")
    if provenance.get("candidate_id") != EXPECTED_CANDIDATE_ID:
        raise ValueError("NASA-BK energy-reduction candidate_id mismatch")
    if provenance.get("status") != "FROZEN_NON_CIRCULAR_REFERENCE_DERIVATION":
        raise ValueError("NASA-BK reference energy reduction is not frozen")
    if provenance.get("source_class") != "NASA_REFERENCE_SOLUTION_DERIVED":
        raise ValueError("NASA-BK source class drifted")

    expected_hash = provenance["normalization"]["frozen_curve_sha256"]
    if _sha256(data_path) != expected_hash:
        raise ValueError("NASA-BK frozen Delta-h0 curve checksum mismatch")

    x_values: list[float] = []
    delta_values: list[float] = []
    with data_path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["x_mid_m", "delta_h0_eff_J_per_kg"]:
            raise ValueError("NASA-BK Delta-h0 CSV header drifted")
        for row in reader:
            x_values.append(float(row["x_mid_m"]))
            delta_values.append(float(row["delta_h0_eff_J_per_kg"]))

    x = np.asarray(x_values, dtype=float)
    delta = np.asarray(delta_values, dtype=float)
    expected_count = int(provenance["source_assets"]["unique_axial_station_count"])
    if x.size != expected_count or x.size < 2:
        raise ValueError("NASA-BK Delta-h0 station count mismatch")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(delta)):
        raise ValueError("NASA-BK Delta-h0 curve must be finite")
    if not np.all(np.diff(x) > 0.0):
        raise ValueError("NASA-BK Delta-h0 axial coordinates must be strictly increasing")
    if not math.isclose(float(x[0]), 0.0, rel_tol=0.0, abs_tol=1.0e-15):
        raise ValueError("NASA-BK Delta-h0 curve must start at x=0")
    if not math.isclose(float(x[-1]), 0.356, rel_tol=0.0, abs_tol=1.0e-15):
        raise ValueError("NASA-BK Delta-h0 curve must end at x=0.356 m")
    if not math.isclose(float(delta[0]), 0.0, rel_tol=0.0, abs_tol=1.0e-12):
        raise ValueError("NASA-BK Delta-h0 curve must be referenced to zero at the inlet")

    x.setflags(write=False)
    delta.setflags(write=False)
    return {"provenance": provenance, "x_m": x, "delta_h0_J_per_kg": delta}


def interpolate_delta_h0(
    x_m: ArrayLike,
    data_path: Path | str = DATA_PATH,
    provenance_path: Path | str = PROVENANCE_PATH,
) -> NDArray[np.float64]:
    """Piecewise-linearly interpolate the frozen reference Delta-h0 curve."""

    record = load_energy_reduction(data_path, provenance_path)
    x_query = np.asarray(x_m, dtype=float)
    if not np.all(np.isfinite(x_query)):
        raise ValueError("x_m must be finite")
    x = record["x_m"]
    tolerance = 1.0e-12
    if np.any(x_query < x[0] - tolerance) or np.any(x_query > x[-1] + tolerance):
        raise ValueError("x_m lies outside the frozen NASA-BK reference domain")
    x_query = np.clip(x_query, x[0], x[-1])
    return np.interp(x_query, x, record["delta_h0_J_per_kg"])


def cell_net_energy_rate_per_length(
    x_face_m: ArrayLike,
    mass_flow_kg_s: object,
    data_path: Path | str = DATA_PATH,
    provenance_path: Path | str = PROVENANCE_PATH,
) -> NDArray[np.float64]:
    """Return conservative signed cell-average ``Qdot'_net`` [W/m].

    Face values of the frozen Delta-h0 curve are interpolated first; each cell
    then receives ``mdot * Delta(Delta h0) / Delta x``.  This guarantees that
    integrating the returned line source over the mesh reproduces the frozen
    inlet-to-exit specific-energy change exactly up to floating-point roundoff.
    """

    faces = np.asarray(x_face_m, dtype=float)
    if faces.ndim != 1 or faces.size < 3 or not np.all(np.isfinite(faces)):
        raise ValueError("x_face_m must be a finite one-dimensional array with at least 3 faces")
    dx = np.diff(faces)
    if not np.all(dx > 0.0):
        raise ValueError("x_face_m must be strictly increasing")
    mass_flow_array = np.asarray(mass_flow_kg_s, dtype=float)
    if mass_flow_array.ndim != 0 or not np.isfinite(mass_flow_array) or mass_flow_array <= 0.0:
        raise ValueError("mass_flow_kg_s must be a finite strictly positive scalar")
    mass_flow = float(mass_flow_array)

    delta_face = interpolate_delta_h0(faces, data_path, provenance_path)
    line_rate = mass_flow * np.diff(delta_face) / dx
    line_rate.setflags(write=False)
    return line_rate


def conservation_diagnostic(
    x_face_m: ArrayLike,
    mass_flow_kg_s: object,
    data_path: Path | str = DATA_PATH,
    provenance_path: Path | str = PROVENANCE_PATH,
) -> dict[str, float]:
    """Return the discrete/global energy-closure mismatch for one mesh."""

    faces = np.asarray(x_face_m, dtype=float)
    line_rate = cell_net_energy_rate_per_length(
        faces, mass_flow_kg_s, data_path, provenance_path
    )
    delta_face = interpolate_delta_h0(faces, data_path, provenance_path)
    discrete = float(np.sum(line_rate * np.diff(faces)))
    expected = float(mass_flow_kg_s) * float(delta_face[-1] - delta_face[0])
    return {
        "discrete_net_power_W": discrete,
        "expected_net_power_W": expected,
        "absolute_mismatch_W": abs(discrete - expected),
    }
