"""Readiness gate for the public NASA Burrows-Kurkov P11.2B candidate.

This module intentionally separates three evidence classes:

1. experiment/source values exposed by NASA;
2. exact unit conversions derived from those values;
3. future reduced-order quantities derived from NASA computational assets.

Passing this module never implies finite-rate chemistry or species validation.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "cases" / "studies" / "data" / "p11_2b_nasa_bk_public_source.json"
EXPECTED_SCHEMA_VERSION = 1
EXPECTED_CASE_FAMILY = "P11_2B_NASA_BK_PUBLIC_VALIDATION"
PSI_TO_PA = 6894.757293168
RANKINE_TO_KELVIN = 5.0 / 9.0


def _finite_positive(name: str, value: object) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    scalar = float(value)
    if not math.isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"{name} must be finite and positive")
    return scalar


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
    """Load and validate the NASA public-source ledger."""

    source_path = Path(path)
    with source_path.open("r", encoding="utf-8") as stream:
        source = json.load(stream)

    if source.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        raise ValueError("unsupported NASA-BK source schema_version")
    if source.get("case_family") != EXPECTED_CASE_FAMILY:
        raise ValueError("unexpected NASA-BK case_family")

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
    required_asset_ids = {
        "NASA-BK-EXP-TAR",
        "NASA-BK-RUN-DAT",
        "NASA-BK-RUN-CGD",
        "NASA-BK-RUN-CFL",
    }
    declared_asset_ids = {item.get("asset_id") for item in assets if isinstance(item, dict)}
    if not required_asset_ids.issubset(declared_asset_ids):
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

    forbidden = policy.get("forbidden_claims")
    required = policy.get("required_before_formal_case")
    if not isinstance(forbidden, list) or not forbidden:
        raise ValueError("reduced-order policy must retain forbidden claims")
    if not isinstance(required, list) or not required:
        raise ValueError("reduced-order policy must retain formal-case prerequisites")

    return source


def assess_nasa_bk_readiness(source: dict[str, Any]) -> dict[str, Any]:
    """Return the current public-data and reduced-order readiness state.

    The current repository has a public NASA source route and a verified direct
    line-heat interface, but it does not yet have an admissible one-dimensional
    geometry/thermodynamic/heat-release reduction of the two-dimensional,
    finite-rate benchmark. The formal case must remain blocked until those
    transformations are explicit and independently testable.
    """

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
    ]

    blockers = [
        {
            "requirement": "quasi_1d_geometry_mapping",
            "status": "NOT_YET_DERIVED",
            "detail": "Derive and regression-test A(x) from the public NASA grid/geometry rather than hand-copying a plot.",
        },
        {
            "requirement": "effective_gas_thermodynamic_reduction",
            "status": "NOT_YET_FROZEN",
            "detail": "The present solver is calorically perfect gas while the NASA benchmark uses a reacting vitiated mixture; an explicit reduced-order gamma/R/cp policy is required.",
        },
        {
            "requirement": "non_circular_line_heat_release_closure",
            "status": "NOT_YET_DERIVED",
            "detail": "No experimentally measured Qdot-prime is claimed. A future profile may be derived from the NASA Wind-US reference solution only with provenance and must be independently checked against experimental observables.",
        },
        {
            "requirement": "experimental_archive_ingestion",
            "status": "PUBLIC_ASSET_DECLARED_NOT_YET_INGESTED",
            "detail": "Ingest exp.tar through a checksum-bearing manifest and preserve coordinates/units for the exit-profile data.",
        },
        {
            "requirement": "species_validation_scope",
            "status": "OUTSIDE_CURRENT_SOLVER_CAPABILITY",
            "detail": "H2/H2O exit profiles are useful benchmark context but cannot be claimed as validated without species transport and chemistry.",
        },
    ]

    return {
        "candidate_id": source["candidate_id"],
        "public_source_route_ready": True,
        "formal_case_ready": False,
        "formal_scope_if_promoted": source["reduced_order_promotion_policy"][
            "highest_permitted_target_scope"
        ],
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
        "source_ledger": Path(path).resolve().relative_to(ROOT.resolve()).as_posix(),
        **assess_nasa_bk_readiness(source),
    }


if __name__ == "__main__":
    print(json.dumps(build_readiness_record(), indent=2, sort_keys=True))
