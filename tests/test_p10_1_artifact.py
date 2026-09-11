"""Strict completeness and runtime provenance gates for the P10.1 artifact."""

import importlib.util
import json
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "cases" / "verification" / "p10_1_conservation_verification.py"
SPEC = importlib.util.spec_from_file_location("p10_1_artifact", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _passing_case():
    return {
        "schemes": {scheme: {"global_balance_pass": True} for scheme in MODULE.EXPECTED_SCHEMES},
        "gates": {"physics_identity": True},
    }


def test_aggregation_rejects_missing_case_scheme_and_failed_gate():
    cases = {case_id: _passing_case() for case_id in MODULE.EXPECTED_CASE_IDS}
    assert MODULE.artifact_passed(cases)
    missing_case = dict(cases); missing_case.pop(next(iter(missing_case)))
    assert not MODULE.artifact_passed(missing_case)
    missing_scheme = _passing_case(); missing_scheme["schemes"].pop("steger-warming")
    assert not MODULE.case_passed(missing_scheme)
    failed_scheme = _passing_case(); failed_scheme["schemes"]["rusanov"]["global_balance_pass"] = False
    assert not MODULE.case_passed(failed_scheme)
    failed_physics = _passing_case(); failed_physics["gates"]["physics_identity"] = False
    assert not MODULE.case_passed(failed_physics)


def test_complete_artifact_is_json_safe_and_uses_runtime_head_sha():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    artifact = MODULE.build_artifact(head)
    assert artifact["head_sha"] == head and len(head) == 40
    assert set(artifact["cases"]) == MODULE.EXPECTED_CASE_IDS
    assert artifact["all_passed"] is True
    json.dumps(artifact, allow_nan=False)


def test_invalid_explicit_head_sha_is_rejected():
    import pytest
    with pytest.raises(ValueError): MODULE.resolve_head_sha("not-a-sha")
