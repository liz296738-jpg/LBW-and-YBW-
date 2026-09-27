"""Regression lock for P11.3K source-enabled solver promotion boundaries."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_source_enabled_time_march.json"


def _load() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_source_enabled_solver_preserves_stage_snapshot_and_current_status() -> None:
    record = _load()
    readiness = record["readiness"]
    current = record["current_status"]

    assert record["schema_version"] == 2
    assert record["stage"] == "P11.3K"

    # Historical P11.3K readiness remains frozen.
    assert readiness["single_injector_mapping_ready"] is True
    assert readiness["eq11_38_source_vector_ready"] is True
    assert readiness["source_enabled_rhs_ready"] is True
    assert readiness["source_enabled_ssp_rk3_ready"] is True
    assert readiness["teacher_static_inlet_adapter_ready"] is False
    assert readiness["teacher_outlet_extrapolation_adapter_ready"] is False
    assert readiness["teacher_variable_composition_steger_warming_ready"] is False
    assert readiness["eq11_26_dimensional_wall_heat_adapter_ready"] is False
    assert readiness["formal_integrated_teacher_case_ready"] is False

    # Current status records later verified integration.
    assert current["teacher_static_inlet_adapter_ready"] is True
    assert current["teacher_outlet_extrapolation_adapter_ready"] is True
    assert current["integrated_source_enabled_h2_path_ready"] is True
    assert current["production_flux"] == "Rusanov"
    assert "Eq.11.26 empirical-to-dimensional wall-heat mapping" in current["source_gated_items"]


def test_source_enabled_solver_preserves_energy_and_boundary_gates() -> None:
    text = " ".join(_load()["scientific_boundaries"]).lower()
    assert "not added through an independent qdot" in text
    assert "not converted to a dimensional wall heat" in text
    assert "transmissive boundaries" in text
    assert "static inlet p/t/u" in text
