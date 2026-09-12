"""Strict P10.3 artifact completeness, provenance, and output tests."""

import csv
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "cases" / "verification" / "p10_3_cfl_temporal_scheme_sensitivity.py"
SPEC = importlib.util.spec_from_file_location("p10_3_artifact", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _record(branch: str, scheme: str, cfl: float, offset: float) -> dict:
    return {
        "branch": branch, "scheme": scheme, "CFL": cfl, "N": 80, "dx": 0.0125,
        "steps": 100, "pseudo_time": 0.05, "initial_residual": 0.04, "final_residual": 9e-9,
        "termination_reason": "converged", "converged": True, "physical": True, "branch_preserved": True,
        "state": {"min_rho": 1.0, "min_p": 1.0, "min_T": 1.0, "min_Mach": 0.2 if branch == "subsonic" else 2.0, "max_Mach": 0.8 if branch == "subsonic" else 2.2},
        "analytical_errors": {variable: {"relative_l1": 0.1, "relative_linf": 0.1} for variable in MODULE.VARIABLES},
        "numerical_fields": {variable: [1.0 + offset, 1.0 + offset] for variable in MODULE.VARIABLES},
    }


def _steady() -> dict:
    return {
        branch: {
            scheme: {
                MODULE.cfl_key(cfl): _record(branch, scheme, cfl, (cfl - 0.2) * 0.005 + (0.0002 if scheme == "steger-warming" else 0.0))
                for cfl in MODULE.CFLS
            }
            for scheme in MODULE.SCHEMES
        }
        for branch in MODULE.BRANCHES
    }


def test_complete_artifact_is_json_safe_and_writes_six_required_outputs(tmp_path: Path) -> None:
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    artifact = MODULE.assemble_artifact(head, _steady(), MODULE.run_rk3_temporal_verification(), scales={branch: {variable: 1.0 for variable in MODULE.VARIABLES} for branch in MODULE.BRANCHES})
    assert artifact["baseline_sha"] == "ce27e3fd841362432791f45f3c8ad53a3002ecf4"
    assert artifact["head_sha"] == head and artifact["all_passed"] is True
    json.dumps(artifact, allow_nan=False)
    outputs = MODULE.write_artifacts(artifact, tmp_path)
    assert {path.name for path in outputs} == {
        "p10_3_sensitivity.json", "p10_3_cfl_results.csv", "p10_3_rk3_temporal.csv",
        "p10_3_cfl_invariance.png", "p10_3_rk3_temporal_convergence.png", "p10_3_scheme_comparison.png",
    }
    with (tmp_path / "p10_3_cfl_results.csv").open(newline="", encoding="utf-8") as stream:
        assert len(list(csv.DictReader(stream))) == 2 * 2 * 2 * 5


def test_artifact_rejects_missing_branch_scheme_and_invalid_sha() -> None:
    rk3 = MODULE.run_rk3_temporal_verification(); scales = {branch: {variable: 1.0 for variable in MODULE.VARIABLES} for branch in MODULE.BRANCHES}
    missing_branch = _steady(); missing_branch.pop("supersonic")
    assert MODULE.assemble_artifact("a" * 40, missing_branch, rk3, scales=scales)["all_passed"] is False
    missing_scheme = _steady(); missing_scheme["subsonic"].pop("steger-warming")
    assert MODULE.assemble_artifact("a" * 40, missing_scheme, rk3, scales=scales)["all_passed"] is False
    wrong_identity = _steady(); wrong_identity["subsonic"]["rusanov"]["0.1"]["scheme"] = "steger-warming"
    assert MODULE.assemble_artifact("a" * 40, wrong_identity, rk3, scales=scales)["all_passed"] is False
    with pytest.raises(ValueError): MODULE.resolve_head_sha("not-a-sha")
