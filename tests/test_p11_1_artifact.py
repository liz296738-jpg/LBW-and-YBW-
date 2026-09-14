"""P11.1 aggregation, provenance, and artifact contract tests."""

import copy
import csv
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "cases" / "studies" / "p11_1_parametric_foundation.py"
SPEC = importlib.util.spec_from_file_location("p11_1_artifact", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _valid_result(case) -> dict:
    mach = np.linspace(0.4, 0.5, 2) if case.branch == "subsonic" else np.linspace(2.0, 2.1, 2)
    scale = case.factor.value
    fields = {"rho": [scale, 2 * scale], "u": [3.0, 4.0], "p": [5 * scale, 6 * scale], "T": [7.0, 8.0], "Mach": mach.tolist(), "mass_flow": [9 * scale, 10 * scale], "U": (np.ones((2, 3)) * scale).tolist(), "x": [0.25, 0.75], "area": [1.05, 1.15], "local_total_pressure": [1.0, 1.0], "local_total_temperature": [1.0, 1.0]}
    return {
        "case_id": case.case_id, "branch": case.branch, "pressure_scale": scale,
        "P0": 300000 * scale, "T0": 500.0, "scheme": "steger-warming", "N": 80,
        "CFL": 0.2, "tolerance": 1e-8, "success": True, "converged": True,
        "termination_reason": "converged", "steps": 10, "pseudo_time": 0.01,
        "final_residual": 1e-9, "physical": True, "framework_branch_preserved": True,
        "physics_input_hash": "a" * 64, "run_configuration_hash": "b" * 64,
        "source_totals": {name: 0.0 for name in MODULE.SOURCE_TOTAL_NAMES},
        "mode_classification_status": "not-defined", "mode_label": None,
        "mode_criterion_id": None, "scientific_claim_level": "framework-only",
        "metrics": {name: 0.0 for name in MODULE.REQUIRED_METRIC_NAMES}, "fields": fields,
        "failure": None,
    }


def valid_inputs() -> dict:
    cases = MODULE.build_formal_manifest()
    results = [_valid_result(case) for case in cases]
    by_id = {row["case_id"]: row for row in results}
    for repeat_id in ("SUB-SW-P100", "SUB-SW-P100-REPEAT"):
        by_id[repeat_id]["physics_input_hash"] = "d" * 64
        by_id[repeat_id]["run_configuration_hash"] = "e" * 64
    for branch in MODULE.BRANCHES:
        branch_rows = [row for row in results if row["branch"] == branch and "REPEAT" not in row["case_id"]]
        for row in branch_rows:
            row["physics_input_hash"] = {0.8: "1", 1.0: "2", 1.2: "3"}[row["pressure_scale"]] * 64
    by_id["SUB-SW-P100"]["physics_input_hash"] = by_id["SUB-SW-P100-REPEAT"]["physics_input_hash"] = "2" * 64
    by_id["SUB-SW-P100"]["run_configuration_hash"] = by_id["SUB-SW-P100-REPEAT"]["run_configuration_hash"] = "e" * 64
    similarity = [MODULE.assess_similarity(by_id[f"{prefix}-SW-P100"], by_id[f"{prefix}-SW-P{code}"]) for prefix in ("SUB", "SUP") for code in ("080", "120")]
    reproducibility = MODULE.assess_reproducibility(by_id["SUB-SW-P100"], by_id["SUB-SW-P100-REPEAT"])
    return {"head_sha": "f" * 40, "case_results": results, "similarity_results": similarity, "reproducibility_results": reproducibility, "regression_summary": {"pytest_passed": 754, "pytest_failures": 0, "pytest_errors": 0, "pytest_step_passed": True}, "p10_ancestor": True, "production_files_changed": []}


def test_complete_artifact_is_strict_json_and_writes_required_runtime_outputs(tmp_path: Path) -> None:
    artifact = MODULE.assemble_artifact(**valid_inputs())
    assert artifact["artifact_kind"] == "exact-sha-p11-parametric-foundation"
    assert artifact["baseline_sha"] == MODULE.BASELINE_SHA
    assert artifact["all_passed"] is True
    assert artifact["mode_policy"] == {"lbw_ybw_classification_defined": False, "mode_criterion_id": None, "mode_label": None}
    json.dumps(artifact, allow_nan=False)
    outputs = MODULE.write_artifacts(artifact, tmp_path)
    assert {path.name for path in outputs} == set(MODULE.REQUIRED_ARTIFACT_NAMES)
    with (tmp_path / "p11_1_case_results.csv").open(newline="", encoding="utf-8") as stream:
        assert len(list(csv.DictReader(stream))) == 7
    data = np.load(tmp_path / "p11_1_fields.npz")
    assert "SUB_SW_P080__rho" in data and "SUP_SW_P120__Mach" in data


@pytest.mark.parametrize("mutation", ["bad_kind", "bad_baseline", "bad_head", "missing_case", "extra_case", "metric", "mode_label", "classification", "production", "ancestor", "pytest", "similarity", "reproducibility"])
def test_aggregate_rejects_invalid_provenance_structure_or_gate(mutation: str) -> None:
    inputs = valid_inputs()
    if mutation == "bad_head": inputs["head_sha"] = "bad"
    elif mutation == "missing_case": inputs["case_results"].pop()
    elif mutation == "extra_case": extra = copy.deepcopy(inputs["case_results"][0]); extra["case_id"] = "EXTRA"; inputs["case_results"].append(extra)
    elif mutation == "metric": inputs["case_results"][0]["metrics"].pop(next(iter(MODULE.REQUIRED_METRIC_NAMES)))
    elif mutation == "mode_label": inputs["case_results"][0]["mode_label"] = "LBW"
    elif mutation == "classification": inputs["case_results"][0]["mode_classification_status"] = "defined"
    elif mutation == "production": inputs["production_files_changed"] = ["src/scramjet1d/solver.py"]
    elif mutation == "ancestor": inputs["p10_ancestor"] = False
    elif mutation == "pytest": inputs["regression_summary"]["pytest_failures"] = 1
    elif mutation == "similarity": inputs["similarity_results"][0]["similarity_passed"] = False
    elif mutation == "reproducibility": inputs["reproducibility_results"]["reproducibility_passed"] = False
    elif mutation == "bad_kind": inputs["artifact_kind"] = "wrong"
    elif mutation == "bad_baseline": inputs["baseline_sha"] = "0" * 40
    if mutation in {"bad_head"}:
        with pytest.raises(ValueError): MODULE.assemble_artifact(**inputs)
    else:
        artifact = MODULE.assemble_artifact(**inputs)
        assert artifact["all_passed"] is False


def test_json_writer_rejects_nan(tmp_path: Path) -> None:
    artifact = MODULE.assemble_artifact(**valid_inputs())
    artifact["case_results"][0]["metrics"]["p_min"] = float("nan")
    with pytest.raises(ValueError):
        MODULE.write_artifacts(artifact, tmp_path)


def test_required_plot_failure_marks_written_closure_incomplete(tmp_path: Path) -> None:
    artifact = MODULE.assemble_artifact(**valid_inputs())
    (tmp_path / "p11_1_mach_similarity.png").mkdir()
    with pytest.raises(OSError):
        MODULE.write_artifacts(artifact, tmp_path)
    written = json.loads((tmp_path / "p11_1_foundation.json").read_text(encoding="utf-8"))
    assert written["gates"]["artifact_structural_integrity"] is False
    assert written["all_passed"] is False


def test_runner_is_offline_and_runtime_artifacts_are_ignored() -> None:
    source = SCRIPT.read_text(encoding="utf-8").lower()
    assert all(token not in source for token in ("import requests", "import urllib", "gh api", "curl ", "wget "))
    assert "artifacts/p11_1/" in (ROOT / ".gitignore").read_text(encoding="utf-8")
