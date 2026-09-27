"""Guard historical and current status of the teacher Eq.11.38 source ledger."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "teacher_eq11_source_vector.json"


def test_eq11_source_ledger_preserves_history_and_current_integration() -> None:
    record = json.loads(LEDGER.read_text(encoding="utf-8"))

    assert record["schema_version"] == 2
    assert record["stage"] == "P11.3I"
    assert record["historical_stage_status"] == (
        "EQ11_38_NON_GEOMETRIC_SOURCE_ADAPTERS_VERIFIED_INTEGRATED_CASE_PENDING"
    )

    historical = record["readiness"]
    assert historical["teacher_fuel_mass_source_ready"] is True
    assert historical["teacher_friction_source_ready"] is True
    assert historical["teacher_boundary_adapter_ready"] is False
    assert historical["integrated_teacher_case_ready"] is False

    current = record["current_status"]
    assert current["source_adapter_integrated"] is True
    assert current["teacher_static_inlet_adapter_ready"] is True
    assert current["teacher_outlet_extrapolation_adapter_ready"] is True
    assert current["integrated_h2_teacher_path_ready"] is True
    assert current["production_flux"] == "Rusanov"
    assert "Eq.11.26 empirical-to-dimensional wall-heat mapping" in current["source_gated_items"]
    assert "variable-thermochemistry Steger-Warming production compatibility" in current["source_gated_items"]
