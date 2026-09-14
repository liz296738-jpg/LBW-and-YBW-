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


def test_current_readiness_record_is_explicitly_blocked() -> None:
    record = MODULE.build_readiness_record()

    assert record["schema_version"] == 1
    assert record["stage"] == "P11.2B"
    assert record["artifact_kind"] == "formal-case-readiness"
    assert record["formal_case_ready"] is False
    assert record["candidate_count"] == 0
    assert record["ready_candidate_count"] == 0
    assert record["declared_project_status"] == "BLOCKED_PENDING_SOURCE_BACKED_ABSOLUTE_POWER_AND_SHAPE_PARAMETERS"
    assert record["blockers"] == ["no candidate_formal_cases declared"]


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
