"""Guard the claim boundary for external C10H22 candidates."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = (
    ROOT
    / "cases"
    / "studies"
    / "data"
    / "c10h22_external_thermochemistry_candidates.json"
)


def test_external_c10h22_candidates_do_not_promote_teacher_readiness() -> None:
    record = json.loads(LEDGER.read_text(encoding="utf-8"))

    assert record["teacher_path_status"] == (
        "BLOCKED_SOURCE_COMPATIBLE_THERMOCHEMISTRY_NOT_RECOVERED"
    )
    assert record["external_branch_status"] == (
        "SUPPORTED_IN_PRINCIPLE_NOT_INTEGRATED"
    )

    policy = record["current_production_policy"]
    assert policy["teacher_H2_C2H4_path_ready"] is True
    assert policy["teacher_C10H22_path_ready"] is False
    assert policy["external_C10H22_branch_integrated"] is False

    forbidden = " ".join(record["prohibited_promotions"])
    assert "Do not add external C10H22 coefficients" in forbidden
    assert "reference-state conventions" in forbidden
    assert "teacher/Cao source reproduction" in forbidden


def test_c10h22_candidate_sources_are_traceable() -> None:
    record = json.loads(LEDGER.read_text(encoding="utf-8"))
    candidates = record["candidates"]

    assert len(candidates) == 3
    dois = {row.get("doi") for row in candidates if row.get("doi")}
    assert "10.1016/j.proci.2008.06.218" in dois
    assert "10.1080/00102202.2011.575420" in dois
    assert any("LLNL" in row["source"] or "Livermore" in row["source"] for row in candidates)
