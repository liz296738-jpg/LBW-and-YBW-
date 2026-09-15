"""Tests for the machine-readable P11.2B readiness record."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "cases" / "studies" / "p11_2b_readiness.py"
SPEC = importlib.util.spec_from_file_location("p11_2b_readiness", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _requirements_by_name(entries: list[dict]) -> dict[str, dict]:
    return {entry["requirement"]: entry for entry in entries}


def test_current_readiness_record_is_explicitly_blocked() -> None:
    record = MODULE.build_readiness_record()

    assert record["schema_version"] == 1
    assert record["stage"] == "P11.2B"
    assert record["artifact_kind"] == "formal-case-readiness"
    assert record["formal_case_ready"] is False
    assert record["candidate_count"] == 0
    assert record["ready_candidate_count"] == 0
    assert (
        record["declared_project_status"]
        == "BLOCKED_PENDING_SOURCE_BACKED_ABSOLUTE_PROFILE_OR_SHAPE_PLUS_ENERGY"
    )
    assert record["blockers"] == ["no candidate_formal_cases declared"]


def test_evidence_summary_closes_only_requirements_with_dedicated_support() -> None:
    record = MODULE.build_readiness_record()
    summary = record["evidence_gate_summary"]
    resolved = _requirements_by_name(summary["resolved_requirements"])
    open_requirements = _requirements_by_name(summary["open_requirements"])

    assert summary["candidate_id"] == "JIN-LIU-MODEL-B-VALIDATION"
    assert summary["formal_promotion_unchanged"] is True

    axial = resolved["axial_coordinate_mapping"]
    assert axial["status"] == "RESOLVED_SOURCE_BACKED"
    assert axial["solver_transform"].startswith("x_solver = x_source - x_station3")

    area = resolved["study_layer_radial_area_law"]
    assert area["status"] == "RESOLVED_SOURCE_CORROBORATED_INTERPRETATION"
    assert area["classification"] == "SOURCE_CORROBORATED_INTERPRETATION"
    assert area["wall_divergence_angle_deg"] == 2.0
    assert area["primary_source_directly_defines_half_angle"] is False

    assert "axial_coordinate_mapping" not in open_requirements
    assert "study_layer_radial_area_law" not in open_requirements


def test_evidence_summary_retains_all_current_non_geometry_blockers() -> None:
    record = MODULE.build_readiness_record()
    open_requirements = _requirements_by_name(
        record["evidence_gate_summary"]["open_requirements"]
    )

    assert (
        open_requirements["validation_condition_identity"]["status"]
        == "UNRESOLVED_CROSS_MODEL_EQUIVALENCE_RATIO_CONFLICT"
    )
    assert open_requirements[
        "Fig. 14 station-3 / combustor-inlet boundary state"
    ]["status"] == "NOT_FROZEN"
    assert open_requirements["Fig. 14 wall-friction coefficient Cf"]["status"] == "NOT_FROZEN"
    assert open_requirements[
        "Cf convention to repository Darcy friction factor"
    ]["status"] == "NOT_FROZEN"
    assert open_requirements[
        "heat_release_shape_and_absolute_energy_chain"
    ]["status"] == "NOT_PROMOTED_TO_FORMAL_CASE"


def test_readiness_record_round_trips_as_canonical_json(tmp_path: Path) -> None:
    record = MODULE.build_readiness_record()
    output = tmp_path / "p11_2b_readiness.json"

    returned = MODULE.write_readiness_record(record, output)

    assert returned == output
    assert json.loads(output.read_text(encoding="utf-8")) == record
    assert output.read_text(encoding="utf-8").endswith("\n")


def test_require_ready_cli_returns_two_for_current_blocked_ledger(tmp_path: Path) -> None:
    output = tmp_path / "blocked.json"
    code = MODULE.main(["--output", str(output), "--require-ready"])

    assert code == 2
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8"))["formal_case_ready"] is False
