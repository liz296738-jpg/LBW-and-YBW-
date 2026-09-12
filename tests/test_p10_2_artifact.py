"""Artifact, provenance, and separate-integration-workflow gates for P10.2."""

import csv
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "cases" / "verification" / "p10_2_grid_convergence.py"
SPEC = importlib.util.spec_from_file_location("p10_2_artifact", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _scheme() -> dict:
    grids = {}
    for n, error in zip(MODULE.GRIDS, (0.04, 0.02, 0.01), strict=True):
        grids[str(n)] = {
            "N": n,
            "dx": 1.0 / n,
            "steps": 10,
            "pseudo_time": 0.01,
            "final_residual": 1.0e-9,
            "termination_reason": "converged",
            "converged": True,
            "physical": True,
            "branch_preserved": True,
            "state": {"min_rho": 1.0, "min_p": 1.0, "min_T": 1.0, "min_Mach": 0.2, "max_Mach": 0.8},
            "errors": {variable: {"relative_l1": error, "relative_linf": error, "interior_relative_l1": error, "interior_relative_linf": error} for variable in MODULE.VARIABLES},
            "smallest_relative_l1": error,
            "residual_error_ratio": 1.0e-7,
        }
    assessment = MODULE.assess_scheme(grids)
    return {"grids": grids, **assessment}


def _artifact(head: str) -> dict:
    branches = {branch: {scheme: _scheme() for scheme in MODULE.SCHEMES} for branch in MODULE.BRANCHES}
    return MODULE.assemble_artifact(head, branches)


def test_complete_artifact_is_exact_json_safe_and_writes_all_outputs(tmp_path: Path) -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    artifact = _artifact(head)
    assert artifact["schema_version"] == 1 and artifact["stage"] == "P10.2"
    assert artifact["baseline_sha"] == "32eb50cd687da6e23a4cb2269bc31120fbff2b3e"
    assert artifact["head_sha"] == head and artifact["grids"] == [40, 80, 160]
    assert artifact["all_passed"] is True
    json.dumps(artifact, allow_nan=False)

    outputs = MODULE.write_artifacts(artifact, tmp_path)
    assert {path.name for path in outputs} == {
        "p10_2_grid_convergence.json",
        "p10_2_grid_errors.csv",
        "p10_2_l1_convergence.png",
        "p10_2_linf_convergence.png",
    }
    with outputs[1].open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 2 * 2 * 3 * 5
    assert set(rows[0]) == {"branch", "scheme", "N", "dx", "variable", "relative_l1", "relative_linf", "interior_relative_l1", "interior_relative_linf", "steps", "residual"}


def test_top_level_aggregation_rejects_missing_branch_scheme_and_invalid_sha() -> None:
    head = "a" * 40
    artifact = _artifact(head)
    missing_branch = dict(artifact["branches"])
    missing_branch.pop("supersonic")
    assert MODULE.assemble_artifact(head, missing_branch)["all_passed"] is False
    missing_scheme = {branch: dict(schemes) for branch, schemes in artifact["branches"].items()}
    missing_scheme["subsonic"].pop("steger-warming")
    assert MODULE.assemble_artifact(head, missing_scheme)["all_passed"] is False
    with pytest.raises(ValueError):
        MODULE.resolve_head_sha("not-a-sha")


def test_formal_study_has_a_dedicated_nonstandard_ci_workflow() -> None:
    workflow = (ROOT / ".github" / "workflows" / "p10_2_grid_convergence.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow
    assert "python cases/verification/p10_2_grid_convergence.py" in workflow
    assert "artifacts/p10_2/" in workflow
    assert "pytest -q" not in workflow
