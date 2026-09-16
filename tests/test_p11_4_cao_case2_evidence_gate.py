import json
from pathlib import Path


DATA_DIR = Path("cases/studies/data")


def _load(name: str) -> dict:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def test_cao_case2_gate_acknowledges_existing_source_record():
    gate = _load("p11_4_cao_case2_evidence_gate.json")
    source = _load("teacher_cao_case2_source.json")

    assert gate["formal_reproduction_ready"] is False
    assert source["readiness"]["source_identity_ready"] is True
    assert source["readiness"]["isolator_entrance_state_ready"] is True
    assert "teacher_cao_case2_source.json" in gate["repository_evidence_search"]["result"]
    assert any("area profile A(x)" in item for item in gate["required_before_promotion"])
    assert any("Yi(x)" in item for item in gate["required_before_promotion"])


def test_gate_does_not_reintroduce_already_frozen_source_identity_as_blocker():
    gate = _load("p11_4_cao_case2_evidence_gate.json")
    blockers = "\n".join(gate["required_before_promotion"])

    assert "traceable primary-source identity" not in blockers
    assert "exact source-backed inlet/boundary state" not in blockers
    assert any("primary-source identity" in item for item in gate["already_frozen"])
