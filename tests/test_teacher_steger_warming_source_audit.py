"""Regression lock for P11.3N Cao/teacher Steger-Warming source audit."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_steger_warming_source_audit.json"


def _load() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_cao_audit_does_not_claim_missing_reconciliation() -> None:
    record = _load()
    conclusion = record["conclusion"]
    assert record["stage"] == "P11.3N"
    assert conclusion["source_backed_variable_cp_absolute_enthalpy"] is True
    assert conclusion["source_backed_classical_constant_property_limit"] is True
    assert conclusion["source_backed_variable_thermochemistry_steger_warming_reconciliation"] is False
    assert conclusion["unsourced_energy_correction_allowed"] is False
    assert conclusion["rusanov_integrated_compatibility_path_remains_primary"] is True


def test_audit_blocks_silent_energy_reference_or_fvs_changes() -> None:
    blocked = " ".join(_load()["blocked_actions"]).lower()
    assert "formation enthalpy" in blocked
    assert "reference-energy correction" in blocked
    assert "physical euler energy flux" in blocked
    assert "guessing" in blocked


def test_both_cao_references_are_recorded() -> None:
    sources = _load()["sources"]
    identities = {item["identity"] for item in sources}
    assert "超燃冲压发动机燃烧模态转换及其控制方法研究_曹瑞峰.pdf" in identities
    assert "面向控制的超燃冲压发动机一维建模研究_曹瑞峰.pdf" in identities
