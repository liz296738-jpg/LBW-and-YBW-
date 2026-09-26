"""Contract tests for the mentor-facing local dashboard."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "mentor_dashboard.py"


def _load_dashboard():
    spec = importlib.util.spec_from_file_location("mentor_dashboard_test_module", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


dashboard = _load_dashboard()


def test_dashboard_run_specs_match_frozen_project_defined_paths() -> None:
    baseline = dashboard.RUN_SPECS["baseline"]
    response = dashboard.RUN_SPECS["response"]
    profile = dashboard.RUN_SPECS["profile"]

    assert baseline["classification"] == "PROJECT_DEFINED_INTEGRATED_SMOKE_CASE"
    assert baseline["cells"] == 20
    assert baseline["cfl"] == 0.5
    assert baseline["teacher_eq_11_46_tolerance"] == 1.0e-4
    assert baseline["max_steps"] == 8_000
    assert baseline["source_reproduction"] is False

    assert response["classification"] == "P12_PROJECT_DEFINED_RESPONSE_SWEEP"
    assert response["equivalence_ratios"] == [0.10, 0.20, 0.30]
    assert response["teacher_eq_11_46_tolerance"] == 2.0e-5
    assert response["source_reproduction"] is False

    assert profile["classification"] == "PROJECT_DEFINED_H2_FULL_PROFILE_EXPORT"
    assert profile["cells"] == 80
    assert profile["teacher_eq_11_46_tolerance"] == 2.0e-5
    assert profile["source_reproduction"] is False


def test_dashboard_summary_preserves_scientific_claim_boundaries() -> None:
    summary = dashboard.build_summary()
    claims = summary["claim_boundaries"]

    assert summary["project"]["status"] == "DELIVERABLE_COMPLETE"
    assert claims["formal_cao_case2_reproduction"] is False
    assert claims["forward_flow_guard_meaning"] == "solver/model-domain inadmissible"
    assert claims["forward_flow_guard_is_unstart"] is False
    assert claims["lbw_ybw_are_mode_labels"] is False
    assert "diagnostic only" in claims["normalized_residual_role"]
    assert "grid-convergence trend only" in claims["grid_claim"]
    assert summary["source_gate"]["formal_reproduction_ready"] is False
    assert summary["blockers"]


def test_dashboard_frontend_exists_and_states_guard_boundary() -> None:
    index = dashboard.WEB_INDEX
    assert index.is_file()
    text = index.read_text(encoding="utf-8")

    assert "导师控制台" in text
    assert "Deliverable complete" in text
    assert "solver/model-domain inadmissible" in text
    assert "不解释为 unstart" in text
    assert "Cao Case 2" in text
    assert "python tools/mentor_dashboard.py" in text


def test_dashboard_only_exposes_known_run_modes() -> None:
    assert set(dashboard.RUNNERS) == {"baseline", "response", "profile"}


def test_dashboard_artifact_urls_are_confined_to_artifact_root() -> None:
    candidate = dashboard.ARTIFACT_ROOT / "example.json"
    assert dashboard._artifact_download_url(candidate) == "/api/artifacts/example.json"


def test_dashboard_artifact_request_rejects_path_traversal() -> None:
    import pytest

    with pytest.raises(ValueError, match="escaped"):
        dashboard._resolve_artifact_request("../course_deliverable_manifest.json")

    with pytest.raises(ValueError, match="escaped"):
        dashboard._resolve_artifact_request("%2E%2E/course_deliverable_manifest.json")


def test_dashboard_runtime_identity_is_non_secret_and_versioned() -> None:
    identity = dashboard._runtime_identity()

    assert identity["python"]
    assert set(identity["packages"]) == {"numpy", "matplotlib", "scramjet1d"}
    assert set(identity["render"]) == {
        "is_render",
        "git_commit",
        "git_branch",
        "git_repo_slug",
        "service_id",
    }


def test_dashboard_provenanced_json_is_self_describing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(dashboard, "ARTIFACT_ROOT", tmp_path)
    monkeypatch.setattr(
        dashboard,
        "_runtime_identity",
        lambda: {
            "python": "3.11.11",
            "packages": {"numpy": "2.4.6"},
            "render": {"git_commit": "abc123"},
        },
    )
    monkeypatch.setattr(dashboard, "_utc_now", lambda: "2026-09-26T00:00:00+00:00")

    payload, path = dashboard._write_provenanced_json_artifact(
        "example.json",
        {"classification": "PROJECT_DEFINED_TEST", "value": 1.0},
    )

    stored = json.loads(path.read_text(encoding="utf-8"))
    assert stored == payload
    assert stored["generated_at_utc"] == "2026-09-26T00:00:00+00:00"
    assert stored["runtime_provenance"]["python"] == "3.11.11"
    assert stored["runtime_provenance"]["render"]["git_commit"] == "abc123"

    digest = dashboard._sha256_file(path)
    assert len(digest) == 64
    assert all(character in "0123456789abcdef" for character in digest)
