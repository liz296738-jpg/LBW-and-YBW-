"""Load and validate the source-backed P11.3B GRI-Mech thermochemistry subset."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from scramjet1d.thermochemistry import (
    PiecewiseSpeciesThermo,
    SpeciesThermoPolynomial,
)

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "cases" / "studies" / "data" / "teacher_thermochemistry_gri30_core.json"
EXPECTED_STATUS = "H2_C2H4_CORE_SPECIES_DATABASE_FROZEN_KEROSENE_PENDING"
CAL_PER_J = 1.0 / 4.184


def load_source_record(path: Path | str = DATA_PATH) -> dict[str, Any]:
    """Load and validate the machine-readable source/provenance record."""

    with Path(path).open("r", encoding="utf-8") as stream:
        record = json.load(stream)
    if record.get("schema_version") != 1:
        raise ValueError("unsupported teacher thermochemistry database schema")
    if record.get("stage") != "P11.3B":
        raise ValueError("teacher thermochemistry database stage drifted")
    if record.get("status") != EXPECTED_STATUS:
        raise ValueError("teacher thermochemistry database status drifted")

    source = record.get("coefficient_source", {})
    if "GRI-Mech Version 3.0" not in source.get("identity", ""):
        raise ValueError("GRI-Mech 3.0 coefficient source identity is missing")
    if "NASA Polynomial format for CHEMKIN-II" not in source.get("mirror_header", ""):
        raise ValueError("CHEMKIN/NASA coefficient convention is not frozen")

    species = record.get("species")
    required = {"H2", "O2", "N2", "AR", "H2O", "C2H4", "CO2"}
    if not isinstance(species, dict) or set(species) != required:
        raise ValueError("teacher thermochemistry core species set drifted")

    coverage = record.get("teacher_fuel_branch_coverage", {})
    if coverage.get("H2") != "READY_FOR_THERMO_PROPERTY_EVALUATION_ONLY":
        raise ValueError("H2 thermo coverage drifted")
    if coverage.get("C2H4") != "READY_FOR_THERMO_PROPERTY_EVALUATION_ONLY":
        raise ValueError("C2H4 thermo coverage drifted")
    if not str(coverage.get("C10H22", "")).startswith("BLOCKED"):
        raise ValueError("C10H22 must remain explicitly blocked")
    if record.get("production_policy", {}).get("solver_integration_ready") is not False:
        raise ValueError("database must not silently promote production solver integration")
    return record


def build_species_database(
    path: Path | str = DATA_PATH,
) -> dict[str, PiecewiseSpeciesThermo]:
    """Instantiate the frozen two-interval species database."""

    record = load_source_record(path)
    database: dict[str, PiecewiseSpeciesThermo] = {}
    for name, entry in record["species"].items():
        molecular_weight = float(entry["molecular_weight_kg_per_kmol"])
        low_min = float(entry["temperature_min_K"])
        switch = float(entry["switch_temperature_K"])
        high_max = float(entry["temperature_max_K"])
        low_coefficients = tuple(float(value) for value in entry["low_coefficients_a1_to_a6"])
        high_coefficients = tuple(float(value) for value in entry["high_coefficients_a1_to_a6"])
        if len(low_coefficients) != 6 or len(high_coefficients) != 6:
            raise ValueError(f"{name} must provide six low/high cp-h coefficients")

        low = SpeciesThermoPolynomial(
            name=name,
            molecular_weight_kg_per_kmol=molecular_weight,
            temperature_min_K=low_min,
            temperature_max_K=switch,
            coefficients=low_coefficients,  # type: ignore[arg-type]
        )
        high = SpeciesThermoPolynomial(
            name=name,
            molecular_weight_kg_per_kmol=molecular_weight,
            temperature_min_K=switch,
            temperature_max_K=high_max,
            coefficients=high_coefficients,  # type: ignore[arg-type]
        )
        database[name] = PiecewiseSpeciesThermo(
            low=low,
            high=high,
            switch_temperature_K=switch,
        )
    return database


def validate_switch_continuity(
    database: dict[str, PiecewiseSpeciesThermo] | None = None,
    *,
    relative_tolerance: float = 1.0e-5,
) -> dict[str, dict[str, float]]:
    """Check source low/high interval continuity for ``cp`` and absolute ``h``."""

    models = build_species_database() if database is None else database
    if not math.isfinite(relative_tolerance) or relative_tolerance <= 0.0:
        raise ValueError("relative_tolerance must be finite and positive")
    diagnostics: dict[str, dict[str, float]] = {}
    for name, model in models.items():
        T = model.switch_temperature_K
        cp_low = model.low.cp(T)
        cp_high = model.high.cp(T)
        h_low = model.low.h(T)
        h_high = model.high.h(T)
        cp_relative_jump = abs(cp_high - cp_low) / max(abs(cp_low), 1.0)
        h_relative_jump = abs(h_high - h_low) / max(abs(h_low), 1.0)
        if cp_relative_jump > relative_tolerance:
            raise ValueError(f"{name} cp interval jump exceeds tolerance")
        if h_relative_jump > relative_tolerance:
            raise ValueError(f"{name} h interval jump exceeds tolerance")
        diagnostics[name] = {
            "switch_temperature_K": T,
            "cp_relative_jump": cp_relative_jump,
            "h_relative_jump": h_relative_jump,
        }
    return diagnostics


def validate_berkeley_cp_298(
    database: dict[str, PiecewiseSpeciesThermo] | None = None,
    path: Path | str = DATA_PATH,
    *,
    absolute_tolerance_cal_per_mol_K: float = 0.03,
) -> dict[str, dict[str, float]]:
    """Cross-check source polynomials against Berkeley's rounded 298 K cp table."""

    models = build_species_database(path) if database is None else database
    record = load_source_record(path)
    tolerance = float(absolute_tolerance_cal_per_mol_K)
    if not math.isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("absolute_tolerance_cal_per_mol_K must be finite and positive")

    diagnostics: dict[str, dict[str, float]] = {}
    for name, model in models.items():
        expected = float(record["species"][name]["berkeley_cp_298_cal_per_mol_K"])
        cp_specific = model.cp(298.15)
        cp_molar_cal = (
            cp_specific * model.molecular_weight_kg_per_kmol / 1000.0 * CAL_PER_J
        )
        error = cp_molar_cal - expected
        if abs(error) > tolerance:
            raise ValueError(f"{name} 298 K cp sanity check exceeds source rounding tolerance")
        diagnostics[name] = {
            "computed_cp_cal_per_mol_K": cp_molar_cal,
            "source_cp_cal_per_mol_K": expected,
            "difference_cal_per_mol_K": error,
        }
    return diagnostics


def build_readiness(path: Path | str = DATA_PATH) -> dict[str, Any]:
    """Return a compact P11.3B data-readiness report."""

    record = load_source_record(path)
    database = build_species_database(path)
    switch = validate_switch_continuity(database)
    cp298 = validate_berkeley_cp_298(database, path)
    return {
        "stage": "P11.3B",
        "core_species_database_ready": True,
        "supported_thermo_fuel_branches": ["H2", "C2H4"],
        "kerosene_C10H22_thermo_ready": False,
        "piecewise_interval_selection_ready": True,
        "switch_continuity_ready": True,
        "independent_298K_cp_sanity_ready": True,
        "solver_integration_ready": bool(record["production_policy"]["solver_integration_ready"]),
        "species_count": len(database),
        "switch_diagnostics": switch,
        "cp298_diagnostics": cp298,
    }


if __name__ == "__main__":
    print(json.dumps(build_readiness(), indent=2, sort_keys=True))
