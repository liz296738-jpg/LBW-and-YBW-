"""P11.3 definition-first readiness gate for dual-mode combustion classification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "cases" / "studies" / "data" / "p11_3_mode_definition_source.json"
OBSERVABLE_PATH = ROOT / "cases" / "studies" / "data" / "p11_3_solver_observable_mapping.json"
EXPECTED_STATUS = "GENERAL_MODE_TAXONOMY_FROZEN_PROJECT_LABEL_MAPPING_PENDING"
EXPECTED_OBSERVABLE_STATUS = "CAPABILITY_AUDIT_COMPLETE_CLASSIFIER_MAPPING_PENDING"


def load_mode_definition_source(path: Path | str = SOURCE_PATH) -> dict[str, Any]:
    """Load the P11.3 evidence ledger and enforce its scientific boundary."""

    with Path(path).open("r", encoding="utf-8") as stream:
        record = json.load(stream)
    if record.get("schema_version") != 1:
        raise ValueError("unsupported P11.3 mode-definition schema")
    if record.get("stage") != "P11.3":
        raise ValueError("P11.3 stage identity drifted")
    if record.get("status") != EXPECTED_STATUS:
        raise ValueError("P11.3 definition status drifted")

    sources = {entry["source_id"]: entry for entry in record.get("evidence_sources", [])}
    required_sources = {
        "TIAN-ET-AL-2014-Q1D-MULTIMODES",
        "ZHANG-ET-AL-2014-MODE-TRANSITION",
        "LIU-ET-AL-2019-AXISYMMETRIC-TRANSITION",
        "FOTIA-DRISCOLL-2013-RAM-SCRAM",
        "CAO-ET-AL-2020-1D-BOUNDARY",
    }
    if not required_sources.issubset(sources):
        raise ValueError("P11.3 authoritative source set is incomplete")

    if sources["TIAN-ET-AL-2014-Q1D-MULTIMODES"].get("doi") != "10.2514/1.B35177":
        raise ValueError("Tian et al. DOI drifted")
    if sources["ZHANG-ET-AL-2014-MODE-TRANSITION"].get("doi") != "10.1016/j.actaastro.2014.06.006":
        raise ValueError("Zhang et al. DOI drifted")
    if sources["LIU-ET-AL-2019-AXISYMMETRIC-TRANSITION"].get("doi") != "10.2514/1.J058391":
        raise ValueError("Liu et al. DOI drifted")
    if sources["FOTIA-DRISCOLL-2013-RAM-SCRAM"].get("doi") != "10.2514/1.B34486":
        raise ValueError("Fotia and Driscoll DOI drifted")
    if sources["CAO-ET-AL-2020-1D-BOUNDARY"].get("doi") != "10.1016/j.ast.2019.105590":
        raise ValueError("Cao et al. DOI drifted")

    tian_modes = sources["TIAN-ET-AL-2014-Q1D-MULTIMODES"]["mode_taxonomy"]
    if set(tian_modes) != {
        "supersonic_combustion_mode",
        "dual_mode_supersonic_combustion_mode",
        "dual_mode_subsonic_combustion_mode",
        "subsonic_combustion_mode",
        "inlet_unstart",
    }:
        raise ValueError("Tian et al. frozen mode taxonomy drifted")

    labels = record.get("project_label_resolution", {})
    if labels.get("labels") != ["LBW", "YBW"]:
        raise ValueError("project labels drifted")
    if labels.get("status") != "UNRESOLVED_PROJECT_SPECIFIC_SEMANTICS":
        raise ValueError("LBW/YBW mapping must remain unresolved until sourced")

    readiness = record.get("classifier_readiness", {})
    expected = {
        "general_mode_taxonomy_ready": True,
        "transition_mechanism_evidence_ready": True,
        "condition_specific_threshold_evidence_ready": True,
        "lbw_ybw_label_mapping_ready": False,
        "solver_observable_mapping_ready": False,
        "universal_threshold_ready": False,
        "classifier_ready": False,
        "regime_map_ready": False,
    }
    for key, value in expected.items():
        if readiness.get(key) is not value:
            raise ValueError(f"P11.3 readiness field {key} drifted")

    rules = {entry["rule_id"]: entry["rule"] for entry in record.get("frozen_general_rules", [])}
    if set(rules) != {f"MODE-DEF-00{i}" for i in range(1, 6)}:
        raise ValueError("P11.3 frozen rule set is incomplete")
    if "solely" not in rules["MODE-DEF-001"].lower():
        raise ValueError("Mach-only classification prohibition drifted")
    if "reacceleration" not in rules["MODE-DEF-003"].lower():
        raise ValueError("downstream reacceleration boundary drifted")

    return record


def load_observable_capability(path: Path | str = OBSERVABLE_PATH) -> dict[str, Any]:
    """Load and validate the current solver-observable capability audit."""

    with Path(path).open("r", encoding="utf-8") as stream:
        record = json.load(stream)
    if record.get("schema_version") != 1 or record.get("stage") != "P11.3":
        raise ValueError("unsupported P11.3 observable-mapping schema")
    if record.get("status") != EXPECTED_OBSERVABLE_STATUS:
        raise ValueError("P11.3 observable capability status drifted")

    native = {entry["observable_id"]: entry for entry in record.get("native_solver_observables", [])}
    required_native = {
        "AXIAL_MACH_PROFILE",
        "AXIAL_STATIC_PRESSURE_PROFILE",
        "AXIAL_TEMPERATURE_PROFILE",
        "AREA_PROFILE",
        "PRESCRIBED_SOURCE_HISTORY",
        "STEADY_CONVERGENCE_AND_TERMINATION",
    }
    if not required_native.issubset(native):
        raise ValueError("P11.3 native observable audit is incomplete")

    missing = {entry["observable_id"]: entry for entry in record.get("not_natively_resolved", [])}
    required_missing = {
        "PRECOMBUSTION_SHOCK_TRAIN_PRESENCE",
        "SHOCK_TRAIN_LENGTH",
        "BOUNDARY_LAYER_SEPARATION_REATTACHMENT",
        "FLAME_POSITION_OR_OPTICAL_STRUCTURE",
        "SPECIES_PROFILE",
    }
    if not required_missing.issubset(missing):
        raise ValueError("P11.3 missing-observable audit is incomplete")

    policy = record.get("classification_policy", {})
    for key in (
        "can_implement_general_literature_classifier_now",
        "can_implement_lbw_ybw_classifier_now",
        "can_generate_lbw_ybw_regime_map_now",
    ):
        if policy.get(key) is not False:
            raise ValueError(f"P11.3 capability policy {key} must remain false")
    return record


def build_readiness(
    path: Path | str = SOURCE_PATH,
    observable_path: Path | str = OBSERVABLE_PATH,
) -> dict[str, Any]:
    """Return compact machine-readable P11.3 promotion readiness."""

    record = load_mode_definition_source(path)
    capability = load_observable_capability(observable_path)
    readiness = record["classifier_readiness"]
    return {
        "stage": "P11.3",
        "definition_evidence_ready": True,
        "general_mode_taxonomy_ready": bool(readiness["general_mode_taxonomy_ready"]),
        "solver_observable_capability_audit_ready": True,
        "lbw_ybw_label_mapping_ready": bool(readiness["lbw_ybw_label_mapping_ready"]),
        "solver_observable_mapping_ready": bool(readiness["solver_observable_mapping_ready"]),
        "classifier_ready": bool(readiness["classifier_ready"]),
        "regime_map_ready": bool(readiness["regime_map_ready"]),
        "native_observable_count": len(capability["native_solver_observables"]),
        "unresolved_observable_count": len(capability["not_natively_resolved"]),
        "blocking_items": list(readiness["blocking_items"]),
        "promotion_policy": "Do not implement or promote LBW/YBW classification until project labels and solver observables are source-backed."
    }


if __name__ == "__main__":
    print(json.dumps(build_readiness(), indent=2, sort_keys=True))
