"""Validate canonical-paper evidence mapping and source boundaries."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "paper" / "evidence_map.json"
PAPER = ROOT / "paper" / "main_paper_zh.md"


def test_canonical_paper_evidence_map_references_existing_files() -> None:
    record = json.loads(MAP.read_text(encoding="utf-8"))

    assert record["paper"] == "paper/main_paper_zh.md"
    for section in record["sections"].values():
        for relative in section.get("evidence", []):
            assert (ROOT / relative).is_file(), relative
        for relative in section.get("figures", []):
            assert (ROOT / relative).is_file(), relative


def test_p13_is_promoted_only_with_frozen_acceptance() -> None:
    record = json.loads(MAP.read_text(encoding="utf-8"))
    p13 = record["sections"]["7.4_p13_cm_sensitivity"]

    assert p13["status"] == "ACCEPTED_PROJECT_DEFINED_SENSITIVITY"
    assert (
        "cases/studies/data/p13_teacher_mixing_constant_sensitivity_acceptance.json"
        in p13["evidence"]
    )
    assert "no optimum" in p13["claim_scope"]
    assert "grid-independence" in p13["claim_scope"]


def test_paper_mentions_all_mapped_figures() -> None:
    record = json.loads(MAP.read_text(encoding="utf-8"))
    paper = PAPER.read_text(encoding="utf-8")

    figures = {
        relative
        for section in record["sections"].values()
        for relative in section.get("figures", [])
    }
    for relative in figures:
        paper_relative = relative.removeprefix("paper/")
        assert f"]({paper_relative})" in paper


def test_global_claim_policy_preserves_scientific_boundaries() -> None:
    policy = json.loads(MAP.read_text(encoding="utf-8"))["policy"]

    assert "acceptance/evidence" in policy["accepted_result_rule"]
    assert "project-defined" in policy["project_defined_rule"]
    assert "unresolved" in policy["source_gated_rule"]
    assert "in-progress" in policy["in_progress_rule"]
