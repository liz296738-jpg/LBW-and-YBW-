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


def test_p13_remains_in_progress_until_acceptance_is_frozen() -> None:
    record = json.loads(MAP.read_text(encoding="utf-8"))
    p13 = record["sections"]["11_p13_in_progress"]

    assert p13["status"] == "IN_PROGRESS_NOT_ACCEPTED"
    assert all("acceptance" not in path for path in p13["evidence"])
    assert "no numerical conclusion" in p13["claim_scope"]


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
