"""P10.4 artifact schema and output tests."""

import csv
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "cases" / "verification" / "p10_4_integrated_vv_closure.py"
SPEC = importlib.util.spec_from_file_location("p10_4_artifact", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_artifact_is_strict_json_and_writes_required_closure_outputs(tmp_path: Path) -> None:
    regression = {
        "pytest_tests": 740, "pytest_failures": 0, "pytest_errors": 0,
        "pytest_skipped": 0, "pytest_passed": 740, "pytest_step_passed": True,
        "baseline_validation_passed": True,
    }
    artifact = MODULE.assemble_artifact("a" * 40, regression, ancestry_checks={stage: True for stage in MODULE.ACCEPTED_EVIDENCE}, production_files_changed=[])
    assert artifact["schema_version"] == 1
    assert artifact["stage"] == "P10.4"
    assert artifact["artifact_kind"] == "exact-sha-integrated-vv-closure"
    assert artifact["baseline_sha"] == MODULE.BASELINE_SHA
    assert artifact["head_sha"] == "a" * 40
    assert artifact["all_passed"] is True
    json.dumps(artifact, allow_nan=False)

    outputs = MODULE.write_artifacts(artifact, tmp_path)
    assert {path.name for path in outputs} == {
        "p10_4_vv_closure.json", "p10_4_evidence_matrix.csv",
        "p10_4_claim_ledger.csv", "p10_4_limitations.md", "p10_4_summary.md",
    }
    with (tmp_path / "p10_4_evidence_matrix.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
        assert len(rows) == 16 and set(rows[0]) == set(MODULE.EVIDENCE_FIELDS)
    with (tmp_path / "p10_4_claim_ledger.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
        assert len(rows) == 15 and set(rows[0]) == set(MODULE.CLAIM_FIELDS)
    summary = (tmp_path / "p10_4_summary.md").read_text(encoding="utf-8")
    for heading in MODULE.SUMMARY_HEADINGS:
        assert heading in summary
    limitations = (tmp_path / "p10_4_limitations.md").read_text(encoding="utf-8")
    assert all(text in limitations for text in MODULE.MANDATORY_LIMITATIONS)


def test_pytest_xml_parser_handles_testsuites_and_computes_passed(tmp_path: Path) -> None:
    xml = tmp_path / "pytest.xml"
    xml.write_text('<testsuites tests="740" failures="0" errors="0" skipped="2"><testsuite tests="740" failures="0" errors="0" skipped="2"/></testsuites>', encoding="utf-8")
    result = MODULE.parse_pytest_xml(xml)
    assert result == {"pytest_tests": 740, "pytest_failures": 0, "pytest_errors": 0, "pytest_skipped": 2, "pytest_passed": 738}


def test_runner_source_has_no_network_dependency() -> None:
    source = SCRIPT.read_text(encoding="utf-8").lower()
    assert "import requests" not in source
    assert "import urllib" not in source
    assert "gh api" not in source
    assert "curl " not in source
    assert "wget " not in source
