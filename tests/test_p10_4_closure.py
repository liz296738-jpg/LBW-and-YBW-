"""Pure aggregation and hard-gate tests for P10.4 closure."""

import copy
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "cases" / "verification" / "p10_4_integrated_vv_closure.py"
SPEC = importlib.util.spec_from_file_location("p10_4_closure", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def valid_inputs() -> dict:
    return {
        "accepted_evidence": copy.deepcopy(MODULE.ACCEPTED_EVIDENCE),
        "ancestry_checks": {stage: True for stage in MODULE.ACCEPTED_EVIDENCE},
        "production_files_changed": [],
        "regression_summary": {
            "pytest_tests": 736,
            "pytest_failures": 0,
            "pytest_errors": 0,
            "pytest_skipped": 0,
            "pytest_passed": 736,
            "pytest_step_passed": True,
            "baseline_validation_passed": True,
        },
        "evidence_matrix": copy.deepcopy(MODULE.EVIDENCE_MATRIX),
        "claim_ledger": copy.deepcopy(MODULE.CLAIM_LEDGER),
        "limitations": list(MODULE.MANDATORY_LIMITATIONS),
    }


def assess(inputs: dict) -> dict:
    return MODULE.assess_closure(**inputs)


def test_synthetic_complete_closure_passes_every_gate() -> None:
    result = assess(valid_inputs())
    assert result["all_passed"] is True
    assert all(result["gates"].values())
    assert set(result["evidence_ids"]) == set(MODULE.EXPECTED_EVIDENCE_IDS)
    assert set(result["claim_ids"]) == set(MODULE.EXPECTED_CLAIM_IDS)


@pytest.mark.parametrize("stage", ["P10.1", "P10.2", "P10.3"])
def test_missing_or_nonancestor_stage_fails(stage: str) -> None:
    missing = valid_inputs(); missing["accepted_evidence"].pop(stage)
    assert assess(missing)["all_passed"] is False
    nonancestor = valid_inputs(); nonancestor["ancestry_checks"][stage] = False
    assert assess(nonancestor)["all_passed"] is False


def test_wrong_accepted_sha_and_production_change_fail() -> None:
    wrong = valid_inputs(); wrong["accepted_evidence"]["P10.2"]["accepted_sha"] = "f" * 40
    assert assess(wrong)["all_passed"] is False
    changed = valid_inputs(); changed["production_files_changed"] = ["src/scramjet1d/solver.py"]
    assert assess(changed)["all_passed"] is False


@pytest.mark.parametrize("field,value", [("pytest_failures", 1), ("pytest_errors", 1), ("pytest_passed", 735), ("pytest_step_passed", False), ("baseline_validation_passed", False)])
def test_regression_failure_fails(field: str, value: int | bool) -> None:
    inputs = valid_inputs(); inputs["regression_summary"][field] = value
    assert assess(inputs)["all_passed"] is False


@pytest.mark.parametrize("collection,id_key,item_id", [("evidence_matrix", "evidence_id", "E01"), ("claim_ledger", "claim_id", "C01")])
def test_missing_and_unexpected_ids_fail(collection: str, id_key: str, item_id: str) -> None:
    missing = valid_inputs(); missing[collection] = [row for row in missing[collection] if row[id_key] != item_id]
    assert assess(missing)["all_passed"] is False
    extra = valid_inputs(); row = copy.deepcopy(extra[collection][0]); row[id_key] = "UNKNOWN"; extra[collection].append(row)
    assert assess(extra)["all_passed"] is False


def test_claim_integrity_qualification_and_scope_overclaim_fail() -> None:
    no_evidence = valid_inputs(); no_evidence["claim_ledger"][0]["evidence_ids"] = []
    assert assess(no_evidence)["all_passed"] is False
    unknown = valid_inputs(); unknown["claim_ledger"][0]["evidence_ids"] = ["E99"]
    assert assess(unknown)["all_passed"] is False
    unqualified = valid_inputs(); next(row for row in unqualified["claim_ledger"] if row["claim_id"] == "C08")["qualification"] = ""
    assert assess(unqualified)["all_passed"] is False
    overclaim = valid_inputs(); next(row for row in overclaim["claim_ledger"] if row["claim_id"] == "C05")["scope"] = "all CFD transient flows"
    assert assess(overclaim)["all_passed"] is False


def test_missing_mandatory_limitation_and_invalid_sha_fail() -> None:
    missing = valid_inputs(); missing["limitations"].pop()
    assert assess(missing)["all_passed"] is False
    with pytest.raises(ValueError):
        MODULE.resolve_head_sha("not-a-sha")


def test_runtime_p10_3_baseline_is_ancestor_and_production_is_frozen() -> None:
    checks = MODULE.git_ancestry_checks()
    assert checks["P10.3"] is True
    assert MODULE.production_files_changed() == []
