"""Guard the role of external peer-reviewed scramjet literature."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = (
    ROOT
    / "cases"
    / "studies"
    / "data"
    / "supporting_peer_reviewed_literature.json"
)


def test_peer_reviewed_literature_remains_supporting_only() -> None:
    record = json.loads(LEDGER.read_text(encoding="utf-8"))

    assert record["role"] == "SUPPORTING_ONLY_NOT_PRIMARY_TEACHER_AUTHORITY"
    forbidden = " ".join(record["claim_policy"]["may_not_support"])
    assert "teacher Eq" in forbidden or "teacher Eqs" in forbidden
    assert "Eq.11.26" in forbidden
    assert "Steger-Warming" in forbidden
    assert "Cao Case 2" in forbidden


def test_peer_reviewed_ledger_freezes_four_traceable_papers() -> None:
    record = json.loads(LEDGER.read_text(encoding="utf-8"))
    papers = record["papers"]

    assert len(papers) == 4
    dois = {paper["doi"] for paper in papers}
    assert dois == {
        "10.2514/1.43716",
        "10.2514/1.50272",
        "10.2514/1.B35177",
        "10.2514/1.B35887",
    }
    assert all(paper["journal"] == "Journal of Propulsion and Power" for paper in papers)
