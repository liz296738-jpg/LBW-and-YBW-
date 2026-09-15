from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "cases" / "studies" / "p11_2b_nasa_bk_readiness.py"
SOURCE_PATH = ROOT / "cases" / "studies" / "data" / "p11_2b_nasa_bk_public_source.json"
MANIFEST_PATH = ROOT / "cases" / "studies" / "data" / "p11_2b_nasa_bk_asset_manifest.json"
PROFILES_PATH = ROOT / "cases" / "studies" / "data" / "p11_2b_nasa_bk_exp_exit_profiles.csv"
GEOMETRY_PATH = ROOT / "cases" / "studies" / "data" / "p11_2b_nasa_bk_geometry_source.json"
THERMO_PATH = ROOT / "cases" / "studies" / "data" / "p11_2b_nasa_bk_thermo_reduction.json"


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


def test_checksum_tracked_experimental_archive_is_ingested():
    module = _load_module()
    ingestion = module.load_experimental_ingestion()

    assert ingestion["archive_sha256"] == "8e3a60293b4a16aa821ac839bee8c890871ef415040029c4f573c743f6b9dc89"
    assert ingestion["row_count"] == 85
    assert ingestion["profile_counts"] == {
        "H2O_mole_fraction": 28,
        "H2_mole_fraction": 27,
        "Mach": 14,
        "total_temperature_K": 16,
    }
    assert ingestion["manifest_path"] == "cases/studies/data/p11_2b_nasa_bk_asset_manifest.json"
    assert ingestion["profiles_path"] == "cases/studies/data/p11_2b_nasa_bk_exp_exit_profiles.csv"


def test_source_backed_geometry_is_resolved_in_readiness():
    module = _load_module()
    geometry = module.load_geometry_evidence()

    assert geometry["geometry_path"] == "cases/studies/data/p11_2b_nasa_bk_geometry_source.json"
    assert geometry["x_start_m"] == pytest.approx(0.0)
    assert geometry["x_exit_m"] == pytest.approx(0.356)
    assert geometry["width_m"] == pytest.approx(0.051)
    assert geometry["height_start_m"] == pytest.approx(0.0938)
    assert geometry["height_exit_m"] == pytest.approx(0.1048)
    assert geometry["area_start_m2"] == pytest.approx(0.0047838)
    assert geometry["area_exit_m2"] == pytest.approx(0.0053448)


def test_effective_gas_reduction_is_resolved_but_keeps_required_sensitivity():
    module = _load_module()
    thermo = module.load_thermo_evidence()

    assert thermo["thermo_path"] == "cases/studies/data/p11_2b_nasa_bk_thermo_reduction.json"
    assert thermo["temperature_reference_K"] == pytest.approx(1270.0)
    assert thermo["R_J_per_kg_K"] == pytest.approx(329.4821420180208)
    assert thermo["cp_J_per_kg_K"] == pytest.approx(1514.961402157982)
    assert thermo["gamma"] == pytest.approx(1.2779315953440815)
    assert thermo["classification"] == "MODEL_REDUCTION_WITH_SOURCE_BACKED_REFERENCE_PROPERTIES"
    assert thermo["sensitivity_gamma_min"] < thermo["gamma"]
    assert "formal NASA-BK reduced-order result" in thermo["required_sensitivity"]


def test_current_nasa_candidate_has_only_line_energy_as_active_formal_blocker():
    module = _load_module()
    source = module.load_nasa_bk_source()
    readiness = module.assess_nasa_bk_readiness(source)

    assert readiness["public_source_route_ready"] is True
    assert readiness["experimental_archive_ingested"] is True
    assert readiness["source_backed_geometry_ready"] is True
    assert readiness["thermodynamic_reduction_ready"] is True
    assert readiness["formal_case_ready"] is False
    assert readiness["lbw_ybw_classification_authorized"] is False
    assert readiness["finite_rate_chemistry_validation_authorized"] is False
    assert readiness["species_validation_authorized"] is False

    open_requirements = {item["requirement"] for item in readiness["open_requirements"]}
    assert open_requirements == {"non_circular_line_heat_release_closure"}

    resolved_requirements = {item["requirement"] for item in readiness["resolved_requirements"]}
    assert "experimental_archive_ingestion" in resolved_requirements
    assert "quasi_1d_geometry_mapping" in resolved_requirements
    assert "effective_gas_thermodynamic_reduction" in resolved_requirements

    exclusions = {item["requirement"]: item["status"] for item in readiness["scope_exclusions"]}
    assert exclusions["species_validation_scope"] == "EXPLICITLY_EXCLUDED_FROM_FORMAL_THERMAL_FLOW_CLAIM"
    assert exclusions["lbw_ybw_classification"] == "NOT_AUTHORIZED_BY_NASA_BK"


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


def test_manifest_checksum_drift_is_rejected(tmp_path: Path):
    module = _load_module()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    exp = next(item for item in manifest["assets"] if item["filename"] == "exp.tar")
    exp["sha256"] = "0" * 64
    tampered = tmp_path / "manifest.json"
    tampered.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected exp.tar checksum"):
        module.load_experimental_ingestion(manifest_path=tampered, profiles_path=PROFILES_PATH)


def test_experimental_profile_point_count_drift_is_rejected(tmp_path: Path):
    module = _load_module()
    lines = PROFILES_PATH.read_text(encoding="utf-8").splitlines()
    tampered = tmp_path / "profiles.csv"
    tampered.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="point count"):
        module.load_experimental_ingestion(manifest_path=MANIFEST_PATH, profiles_path=tampered)


def test_geometry_derived_value_drift_is_rejected(tmp_path: Path):
    module = _load_module()
    geometry = json.loads(GEOMETRY_PATH.read_text(encoding="utf-8"))
    geometry["derived_geometry"]["area_start_m2"] += 1.0e-5
    tampered = tmp_path / "geometry.json"
    tampered.write_text(json.dumps(geometry), encoding="utf-8")
    with pytest.raises(ValueError, match="area_start_m2"):
        module.load_geometry_evidence(tampered)


def test_thermo_policy_drift_is_rejected(tmp_path: Path):
    module = _load_module()
    thermo = json.loads(THERMO_PATH.read_text(encoding="utf-8"))
    thermo["formal_case_policy"]["classification"] = "UNTRACKED_ASSUMPTION"
    tampered = tmp_path / "thermo.json"
    tampered.write_text(json.dumps(thermo), encoding="utf-8")
    with pytest.raises(ValueError, match="classification"):
        module.load_thermo_evidence(tampered)


def test_readiness_record_uses_repository_relative_posix_source_path():
    module = _load_module()
    record = module.build_readiness_record()

    assert record["source_ledger"] == "cases/studies/data/p11_2b_nasa_bk_public_source.json"
    assert "\\" not in record["source_ledger"]
    assert record["experimental_archive_ingested"] is True
    assert record["source_backed_geometry_ready"] is True
    assert record["thermodynamic_reduction_ready"] is True
    assert record["formal_case_ready"] is False
