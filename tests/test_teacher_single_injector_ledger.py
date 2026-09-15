"""Regression lock for P11.3J single-injector mapping boundaries."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_single_injector_mapping.json"


def _load() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_single_injector_mapping_readiness_is_narrow_and_explicit() -> None:
    record = _load()
    readiness = record["readiness"]
    assert record["stage"] == "P11.3J"
    assert readiness["air_only_upstream_mapping_ready"] is True
    assert readiness["single_cell_fuel_source_mapping_ready"] is True
    assert readiness["downstream_algebraic_composition_mapping_ready"] is True
    assert readiness["double_counting_guard_ready"] is True
    assert readiness["source_enabled_variable_composition_rhs_ready"] is False
    assert readiness["teacher_boundary_adapter_ready"] is False
    assert readiness["integrated_teacher_case_ready"] is False


def test_single_injector_ledger_preserves_scientific_boundaries() -> None:
    text = " ".join(_load()["scientific_boundaries"]).lower()
    assert "not a second conservative mass source" in text
    assert "air-only upstream" in text
    assert "no species transport pde" in text
    assert "no eq.11.26-to-dimensional-wall-heat conversion" in text
