"""Readiness gate for the public NASA Burrows-Kurkov P11.2B candidate.

The gate separates source values, exact conversions, checksum-tracked public
experimental data, source-backed geometry, and future reduced-order quantities
derived from NASA computational assets. Passing it never implies finite-rate
chemistry, species, or LBW/YBW validation.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "cases" / "studies" / "data"
SOURCE_PATH = DATA_DIR / "p11_2b_nasa_bk_public_source.json"
ASSET_MANIFEST_PATH = DATA_DIR / "p11_2b_nasa_bk_asset_manifest.json"
EXPERIMENTAL_PROFILES_PATH = DATA_DIR / "p11_2b_nasa_bk_exp_exit_profiles.csv"
GEOMETRY_SOURCE_PATH = DATA_DIR / "p11_2b_nasa_bk_geometry_source.json"
EXPECTED_SCHEMA_VERSION = 1
EXPECTED_CASE_FAMILY = "P11_2B_NASA_BK_PUBLIC_VALIDATION"
EXPECTED_CANDIDATE_ID = "NASA-BURROWS-KURKOV-REACTING-VALIDATION"
PSI_TO_PA = 6894.757293168
RANKINE_TO_KELVIN = 5.0 / 9.0


def _finite_positive(name: str, value: object) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    scalar = float(value)
    if not math.isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return scalar


def _repo_relative(path: Path | str) -> str:
    return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()


def _validate_mass_fractions(name: str, fractions: object) -> None:
    if not isinstance(fractions, dict) or not fractions:
        raise ValueError(f"{name} mass_fractions must be a nonempty mapping")
    total = 0.0
    for species, value in fractions.items():
        if not isinstance(species, str) or not species:
            raise ValueError(f"{name} contains an invalid species key")
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{name}.{species} must be numeric")
        fraction = float(value)
        if not math.isfinite(fraction) or fraction < 0.0:
            raise ValueError(f"{name}.{species} must be finite and nonnegative")
        total += fraction
    if not math.isclose(total, 1.0, rel_tol=0.0, abs_tol=1.0e-9):
        raise ValueError(f"{name} mass fractions must sum to 1; got {total}")


def load_nasa_bk_source(path: Path | str = SOURCE_PATH) -> dict[str, Any]:
    """Load and validate the public NASA source ledger."""

    with Path(path).open("r", encoding="utf-8") as stream:
        source = json.load(stream)
    if source.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        raise ValueError("unsupported NASA-BK source schema_version")
    if source.get("case_family") != EXPECTED_CASE_FAMILY:
        raise ValueError("unexpected NASA-BK case_family")
    if source.get("candidate_id") != EXPECTED_CANDIDATE_ID:
        raise ValueError("unexpected NASA-BK candidate_id")

    primary = source.get("primary_experiment")
    archive = source.get("nasa_validation_archive")
    raw = source.get("source_conditions_raw")
    si = source.get("source_conditions_si")
    targets = source.get("experimental_targets")
    policy = source.get("reduced_order_promotion_policy")
    if not all(isinstance(item, dict) for item in (primary, archive, raw, si, targets, policy)):
        raise ValueError("NASA-BK ledger is missing required mappings")
    if primary.get("distribution_limits") != "Public":
        raise ValueError("primary experiment must retain NASA public-distribution status")
    if not str(primary.get("ntrs_url", "")).startswith("https://ntrs.nasa.gov/"):
        raise ValueError("primary experiment must point to NTRS")

    assets = archive.get("public_assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("NASA validation archive must declare public assets")
    required_ids = {
        "NASA-BK-EXP-TAR",
        "NASA-BK-RUN-DAT",
        "NASA-BK-RUN-CGD",
        "NASA-BK-RUN-CFL",
    }
    declared_ids = {item.get("asset_id") for item in assets if isinstance(item, dict)}
    if not required_ids.issubset(declared_ids):
        raise ValueError("NASA validation archive is missing required public assets")
    for item in assets:
        if not isinstance(item, dict):
            raise ValueError("public_assets entries must be mappings")
        url = item.get("url")
        if not isinstance(url, str) or not url.startswith("https://www.grc.nasa.gov/"):
            raise ValueError("NASA validation assets must use the official NASA Glenn host")

    raw_free = raw.get("freestream")
    raw_h2 = raw.get("hydrogen")
    si_free = si.get("freestream")
    si_h2 = si.get("hydrogen")
    if not all(isinstance(item, dict) for item in (raw_free, raw_h2, si_free, si_h2)):
        raise ValueError("NASA-BK inlet condition records are incomplete")
    _validate_mass_fractions("raw.freestream", raw_free.get("mass_fractions"))
    _validate_mass_fractions("raw.hydrogen", raw_h2.get("mass_fractions"))
    _validate_mass_fractions("si.freestream", si_free.get("mass_fractions"))
    _validate_mass_fractions("si.hydrogen", si_h2.get("mass_fractions"))

    for name, state in (("raw.freestream", raw_free), ("raw.hydrogen", raw_h2)):
        _finite_positive(f"{name}.Mach", state.get("Mach"))
        _finite_positive(f"{name}.pressure_psi", state.get("pressure_psi"))
        _finite_positive(f"{name}.temperature_R", state.get("temperature_R"))
    for name, state in (("si.freestream", si_free), ("si.hydrogen", si_h2)):
        _finite_positive(f"{name}.Mach", state.get("Mach"))
        _finite_positive(f"{name}.pressure_Pa", state.get("pressure_Pa"))
        _finite_positive(f"{name}.temperature_K", state.get("temperature_K"))

    expected_si = {
        "freestream_pressure_Pa": raw_free["pressure_psi"] * PSI_TO_PA,
        "freestream_temperature_K": raw_free["temperature_R"] * RANKINE_TO_KELVIN,
        "hydrogen_pressure_Pa": raw_h2["pressure_psi"] * PSI_TO_PA,
        "hydrogen_temperature_K": raw_h2["temperature_R"] * RANKINE_TO_KELVIN,
        "wall_temperature_K": raw["wall_temperature_R"] * RANKINE_TO_KELVIN,
        "downstream_pressure_Pa": raw["downstream_pressure_psi"] * PSI_TO_PA,
    }
    actual_si = {
        "freestream_pressure_Pa": si_free["pressure_Pa"],
        "freestream_temperature_K": si_free["temperature_K"],
        "hydrogen_pressure_Pa": si_h2["pressure_Pa"],
        "hydrogen_temperature_K": si_h2["temperature_K"],
        "wall_temperature_K": si["wall_temperature_K"],
        "downstream_pressure_Pa": si["downstream_pressure_Pa"],
    }
    for key, expected in expected_si.items():
        if not math.isclose(float(actual_si[key]), float(expected), rel_tol=0.0, abs_tol=1.0e-9):
            raise ValueError(f"{key} is not an exact conversion of the tracked raw NASA value")

    _finite_positive("experimental_targets.exit_plane_x_m", targets.get("exit_plane_x_m"))
    _finite_positive(
        "experimental_targets.ignition_onset_m_for_2286_R_case",
        targets.get("ignition_onset_m_for_2286_R_case"),
    )
    quantities = targets.get("exit_profile_quantities")
    if not isinstance(quantities, list) or "Mach" not in quantities or "total_temperature" not in quantities:
        raise ValueError("experimental targets must retain Mach and total-temperature profiles")
    if not isinstance(policy.get("forbidden_claims"), list) or not policy["forbidden_claims"]:
        raise ValueError("reduced-order policy must retain forbidden claims")
    if not isinstance(policy.get("required_before_formal_case"), list) or not policy["required_before_formal_case"]:
        raise ValueError("reduced-order policy must retain formal-case prerequisites")
    return source


def load_experimental_ingestion(
    manifest_path: Path | str = ASSET_MANIFEST_PATH,
    profiles_path: Path | str = EXPERIMENTAL_PROFILES_PATH,
) -> dict[str, Any]:
    """Validate the checksum manifest and normalized NASA experimental profiles."""

    with Path(manifest_path).open("r", encoding="utf-8") as stream:
        manifest = json.load(stream)
    if manifest.get("schema_version") != 1:
        raise ValueError("unsupported NASA-BK asset manifest schema")
    if manifest.get("candidate_id") != EXPECTED_CANDIDATE_ID:
        raise ValueError("asset manifest candidate_id mismatch")
    if manifest.get("record_kind") != "public-asset-acquisition-manifest":
        raise ValueError("unexpected NASA-BK asset manifest kind")

    assets = {item.get("filename"): item for item in manifest.get("assets", []) if isinstance(item, dict)}
    exp_tar = assets.get("exp.tar")
    if not isinstance(exp_tar, dict):
        raise ValueError("asset manifest must contain exp.tar")
    expected_archive_sha = "8e3a60293b4a16aa821ac839bee8c890871ef415040029c4f573c743f6b9dc89"
    if exp_tar.get("sha256") != expected_archive_sha:
        raise ValueError("unexpected exp.tar checksum")

    records = manifest.get("extracted_experimental_members")
    if not isinstance(records, list) or len(records) != 4:
        raise ValueError("asset manifest must retain four experimental members")
    by_quantity = {item.get("quantity"): item for item in records if isinstance(item, dict)}
    expected_quantities = {"Mach", "total_temperature_K", "H2_mole_fraction", "H2O_mole_fraction"}
    if set(by_quantity) != expected_quantities:
        raise ValueError("experimental member quantity set drifted")

    rows: list[dict[str, Any]] = []
    with Path(profiles_path).open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        required_columns = {"profile", "y_m", "value", "units", "source_file"}
        if set(reader.fieldnames or []) != required_columns:
            raise ValueError("normalized experimental CSV columns drifted")
        for row in reader:
            profile = row["profile"]
            if profile not in expected_quantities:
                raise ValueError(f"unknown experimental profile {profile!r}")
            y_m = _finite_positive(f"{profile}.y_m", float(row["y_m"]))
            value = float(row["value"])
            if not math.isfinite(value):
                raise ValueError(f"{profile}.value must be finite")
            if profile in {"H2_mole_fraction", "H2O_mole_fraction"} and not 0.0 <= value <= 1.0:
                raise ValueError(f"{profile} must remain within [0, 1]")
            if profile in {"Mach", "total_temperature_K"} and value <= 0.0:
                raise ValueError(f"{profile} values must be positive")
            if row["source_file"] != by_quantity[profile].get("filename"):
                raise ValueError(f"{profile} source_file does not match checksum manifest")
            rows.append({"profile": profile, "y_m": y_m, "value": value})

    counts = Counter(row["profile"] for row in rows)
    for profile, record in by_quantity.items():
        if counts[profile] != record.get("point_count"):
            raise ValueError(f"{profile} point count does not match checksum manifest")
    return {
        "archive_sha256": expected_archive_sha,
        "workflow_run_id": manifest.get("workflow_run_id"),
        "workflow_artifact_id": manifest.get("workflow_artifact_id"),
        "profile_counts": dict(sorted(counts.items())),
        "row_count": len(rows),
        "profiles_path": _repo_relative(profiles_path),
        "manifest_path": _repo_relative(manifest_path),
    }


def load_geometry_evidence(path: Path | str = GEOMETRY_SOURCE_PATH) -> dict[str, Any]:
    """Validate the source-backed rectangular linear-expansion area mapping."""

    with Path(path).open("r", encoding="utf-8") as stream:
        record = json.load(stream)
    if record.get("schema_version") != 1:
        raise ValueError("unsupported NASA-BK geometry schema")
    if record.get("record_kind") != "validation-geometry-source":
        raise ValueError("unexpected NASA-BK geometry record_kind")
    if record.get("candidate_id") != EXPECTED_CANDIDATE_ID:
        raise ValueError("NASA-BK geometry candidate_id mismatch")
    if record.get("status") != "GEOMETRY_FROZEN_SOURCE_BACKED":
        raise ValueError("NASA-BK geometry is not frozen")

    source = record.get("source_geometry_si")
    derived = record.get("derived_geometry")
    if not isinstance(source, dict) or not isinstance(derived, dict):
        raise ValueError("NASA-BK geometry record is incomplete")
    x0 = float(source.get("x_start_m"))
    x1 = _finite_positive("geometry.x_exit_m", source.get("x_exit_m"))
    width = _finite_positive("geometry.width_m", source.get("width_m"))
    h0 = _finite_positive("geometry.height_start_m", source.get("height_start_m"))
    h1 = _finite_positive("geometry.height_exit_m", source.get("height_exit_m"))
    if x0 != 0.0 or x1 <= x0:
        raise ValueError("NASA-BK geometry origin/domain drifted")
    if source.get("expansion_type") != "linear-height rectangular duct":
        raise ValueError("NASA-BK expansion type drifted")

    area0 = width * h0
    area1 = width * h1
    ratio = area1 / area0
    expected = {
        "area_start_m2": area0,
        "area_exit_m2": area1,
        "area_ratio_exit_over_start": ratio,
    }
    for key, value in expected.items():
        if not math.isclose(float(derived.get(key)), value, rel_tol=0.0, abs_tol=1.0e-14):
            raise ValueError(f"{key} is inconsistent with source geometry")
    if derived.get("derivation_class") != "DERIVED_EXACTLY_FROM_SOURCE_DIMENSIONS":
        raise ValueError("NASA-BK geometry derivation class drifted")
    return {
        "geometry_path": _repo_relative(path),
        "x_start_m": x0,
        "x_exit_m": x1,
        "width_m": width,
        "height_start_m": h0,
        "height_exit_m": h1,
        "area_start_m2": area0,
        "area_exit_m2": area1,
        "area_ratio_exit_over_start": ratio,
    }


def assess_nasa_bk_readiness(
    source: dict[str, Any],
    ingestion: dict[str, Any] | None = None,
    geometry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the current public-data and reduced-order readiness state."""

    ingestion = ingestion or load_experimental_ingestion()
    geometry = geometry or load_geometry_evidence()
    archive = source["nasa_validation_archive"]
    targets = source["experimental_targets"]
    assets = {item["asset_id"]: item for item in archive["public_assets"]}

    resolved = [
        {
            "requirement": "public_primary_experiment_identity",
            "status": "RESOLVED_NASA_PUBLIC",
            "source_id": source["primary_experiment"]["source_id"],
        },
        {
            "requirement": "public_validation_archive",
            "status": "RESOLVED_NASA_PUBLIC",
            "asset_ids": sorted(assets),
        },
        {
            "requirement": "source_inlet_and_wall_conditions",
            "status": "RESOLVED_SOURCE_PLUS_EXACT_UNIT_CONVERSION",
        },
        {
            "requirement": "experimental_validation_targets",
            "status": "RESOLVED_TARGET_TYPES",
            "exit_plane_x_m": targets["exit_plane_x_m"],
            "targets": list(targets["exit_profile_quantities"]),
            "ignition_onset_m": targets["ignition_onset_m_for_2286_R_case"],
        },
        {
            "requirement": "experimental_archive_ingestion",
            "status": "RESOLVED_CHECKSUM_TRACKED_PUBLIC_NASA_DATA",
            "archive_sha256": ingestion["archive_sha256"],
            "profile_counts": ingestion["profile_counts"],
            "manifest_path": ingestion["manifest_path"],
            "profiles_path": ingestion["profiles_path"],
        },
        {
            "requirement": "quasi_1d_geometry_mapping",
            "status": "RESOLVED_SOURCE_BACKED_LINEAR_RECTANGULAR_DUCT",
            **geometry,
        },
    ]

    blockers = [
        {
            "requirement": "effective_gas_thermodynamic_reduction",
            "status": "NOT_YET_FROZEN",
            "detail": "The solver is calorically perfect gas while the NASA benchmark uses a reacting vitiated mixture; an explicit reduced-order gamma/R/cp policy is required.",
        },
        {
            "requirement": "non_circular_line_heat_release_closure",
            "status": "NOT_YET_DERIVED",
            "detail": "The experiment supplies exit profiles, not measured axial Qdot-prime. Any effective line-energy profile derived from the NASA Wind-US reference solution must retain computational provenance and independent experimental validation targets.",
        },
        {
            "requirement": "species_validation_scope",
            "status": "OUTSIDE_CURRENT_SOLVER_CAPABILITY",
            "detail": "H2/H2O profiles are public benchmark context but cannot be claimed as validated without species transport and chemistry.",
        },
    ]

    return {
        "candidate_id": source["candidate_id"],
        "public_source_route_ready": True,
        "experimental_archive_ingested": True,
        "source_backed_geometry_ready": True,
        "formal_case_ready": False,
        "formal_scope_if_promoted": source["reduced_order_promotion_policy"]["highest_permitted_target_scope"],
        "resolved_requirements": resolved,
        "open_requirements": blockers,
        "resolved_count": len(resolved),
        "open_count": len(blockers),
        "lbw_ybw_classification_authorized": False,
        "finite_rate_chemistry_validation_authorized": False,
        "species_validation_authorized": False,
    }


def build_readiness_record(path: Path | str = SOURCE_PATH) -> dict[str, Any]:
    source = load_nasa_bk_source(path)
    return {
        "schema_version": 1,
        "stage": "P11.2B",
        "artifact_kind": "nasa-bk-public-validation-readiness",
        "source_ledger": _repo_relative(path),
        **assess_nasa_bk_readiness(source),
    }


if __name__ == "__main__":
    print(json.dumps(build_readiness_record(), indent=2, sort_keys=True))
