"""Regression lock for P11.3L teacher boundary promotion boundaries."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_variable_composition_boundaries.json"


def _load() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_boundary_compatibility_is_ready_before_steger_warming() -> None:
    record = _load()
    readiness = record["readiness"]
    assert record["stage"] == "P11.3L"
    assert readiness["teacher_static_p_T_u_inlet_ready"] is True
    assert readiness["teacher_first_order_outlet_ready"] is True
    assert readiness["source_enabled_boundary_ssp_rk3_ready"] is True
    assert readiness["teacher_variable_composition_steger_warming_ready"] is False
    assert readiness["teacher_near_sonic_smoothing_policy_ready"] is False
    assert readiness["eq11_26_dimensional_wall_heat_adapter_ready"] is False
    assert readiness["formal_integrated_teacher_case_ready"] is False


def test_boundary_ledger_does_not_overclaim_numerics_or_heat_closure() -> None:
    text = " ".join(_load()["scientific_boundaries"]).lower()
    assert "internal interfaces still use rusanov" in text
    assert "eq.11.26-to-dimensional-wall-heat conversion remains pending" in text
    assert "no duplicate qdot" in text
