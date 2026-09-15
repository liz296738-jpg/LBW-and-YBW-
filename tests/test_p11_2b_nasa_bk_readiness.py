from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "cases" / "studies" / "p11_2b_nasa_bk_readiness.py"
SOURCE_PATH = ROOT / "cases" / "studies" / "data" / "p11_2b_nasa_bk_public_source.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("p11_2b_nasa_bk_readiness", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_ledger_loads_and_preserves_exact_si_conversions():
    module = _load_module()
    source = module.load_nasa_bk_source()

    raw = source["source_conditions_raw"]
    si = source["source_conditions_si"]

    assert math.isclose(
        si["freestream"]["pressure_Pa"],
        raw["freestream"]["pressure_psi"] * module.PSI_TO_PA,
        rel_tol=0.0,
        abs_tol=1.0e-9,
    )
    assert math.isclose(
        si["freestream"]["temperature_K"],
        raw["freestream"]["temperature_R"] * module.RANKINE_TO_KELVIN,
        rel_tol=0.0,
        abs_tol=1.0e-9,
    )
    assert si["freestream"]["temperature_K"] == 1270.0
    assert si["hydrogen"]["temperature_K"] == 254.0
    assert si["wall_temperature_K"] == 298.0


def test_nasa_assets_are_official_public_routes():
    module = _load_module()
    source = module.load_nasa_bk_source()

    assert source["primary_experiment"]["distribution_limits"] == "Public"
    assert source["primary_experiment"]["ntrs_url"].startswith("https://ntrs.nasa.gov/")

    assets = {item["asset_id"]: item for item in source["nasa_validation_archive"]["public_assets"]}
    for required in {
        "NASA-BK-EXP-TAR",
        "NASA-BK-RUN-DAT",
        "NASA-BK-RUN-CGD",
        "NASA-BK-RUN-CFL",
    }:
        assert required in assets
        assert assets[required]["url"].startswith("https://www.grc.nasa.gov/")


def test_current_nasa_candidate_stays_formally_blocked_and_scoped():
    module = _load_module()
    source = module.load_nasa_bk_source()
    readiness = module.assess_nasa_bk_readiness(source)

    assert readiness["public_source_route_ready"] is True
    assert readiness["formal_case_ready"] is False
    assert readiness["lbw_ybw_classification_authorized"] is False
    assert readiness["finite_rate_chemistry_validation_authorized"] is False
    assert readiness["species_validation_authorized"] is False

    open_requirements = {item["requirement"] for item in readiness["open_requirements"]}
    assert open_requirements == {
        "quasi_1d_geometry_mapping",
        "effective_gas_thermodynamic_reduction",
        "non_circular_line_heat_release_closure",
        "experimental_archive_ingestion",
        "species_validation_scope",
    }


def test_experimental_targets_separate_thermal_flow_from_species_scope():
    module = _load_module()
    source = module.load_nasa_bk_source()
    targets = source["experimental_targets"]

    assert targets["exit_plane_x_m"] == pytest.approx(0.356)
    assert targets["ignition_onset_m_for_2286_R_case"] == pytest.approx(0.18)
    assert "Mach" in targets["exit_profile_quantities"]
    assert "total_temperature" in targets["exit_profile_quantities"]
    assert "H2O_mole_fraction" in targets["exit_profile_quantities"]
    assert "H2_mole_fraction" in targets["exit_profile_quantities"]

    readiness = module.assess_nasa_bk_readiness(source)
    species_block = next(
        item for item in readiness["open_requirements"] if item["requirement"] == "species_validation_scope"
    )
    assert species_block["status"] == "OUTSIDE_CURRENT_SOLVER_CAPABILITY"


def test_tampered_si_conversion_is_rejected(tmp_path: Path):
    module = _load_module()
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    source["source_conditions_si"]["freestream"]["pressure_Pa"] += 1.0
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(ValueError, match="exact conversion"):
        module.load_nasa_bk_source(tampered)


def test_source_mass_fraction_drift_is_rejected(tmp_path: Path):
    module = _load_module()
    source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    source["source_conditions_raw"]["freestream"]["mass_fractions"]["N2"] = 0.40
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(ValueError, match="sum to 1"):
        module.load_nasa_bk_source(tampered)


def test_readiness_record_uses_repository_relative_posix_source_path():
    module = _load_module()
    record = module.build_readiness_record()

    assert record["source_ledger"] == "cases/studies/data/p11_2b_nasa_bk_public_source.json"
    assert "\\" not in record["source_ledger"]
    assert record["formal_case_ready"] is False
