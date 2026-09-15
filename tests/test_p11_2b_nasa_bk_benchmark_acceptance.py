"""Regression tests for the scoped NASA-BK P11.2B benchmark acceptance record."""

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "cases" / "studies" / "data" / "p11_2b_nasa_bk_benchmark_acceptance.json"


def _load() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_acceptance_scope_is_explicitly_reduced_order_not_experimental() -> None:
    record = _load()
    assert record["status"] == "FORMAL_REDUCED_ORDER_REFERENCE_BENCHMARK_ACCEPTED"
    assert record["benchmark_ready"] is True
    assert record["formal_experimental_validation_ready"] is False
    assert record["source_class"] == "NASA_REFERENCE_SOLUTION_DERIVED"
    assert record["experimental_context"]["formal_acceptance_role"] == "NOT_USED_AS_A_SCALAR_FIT_OR_TUNING_TARGET"


def test_grid_convergence_meets_frozen_acceptance_gate() -> None:
    record = _load()
    convergence = record["grid_convergence"]
    errors = convergence["finest_grid_relative_errors_vs_conservative_target"]
    changes = convergence["finest_vs_previous_relative_changes"]

    assert convergence["all_converged"] is True
    assert convergence["all_supersonic"] is True
    assert convergence["cell_counts"] == [40, 80, 160, 320]
    assert all(abs(float(value)) < 0.02 for value in errors.values())
    assert all(abs(float(value)) < 0.005 for value in changes.values())


def test_primary_result_preserves_conservation_and_supersonic_scope() -> None:
    record = _load()
    result = record["reference_gamma_result"]
    assert result["solver_converged"] is True
    assert float(result["minimum_Mach"]) > 1.0
    assert abs(float(result["energy_integral_mismatch_W"])) < 1.0e-8
    assert abs(float(result["momentum_integral_mismatch_N"])) < 1.0e-10


def test_p11_3_is_authorized_only_as_definition_first_stage() -> None:
    record = _load()
    next_stage = record["next_stage"]
    assert next_stage["stage"] == "P11.3"
    assert next_stage["authorized"] is True
    scope = next_stage["scope"].lower()
    assert "definitions" in scope
    assert "thresholds" in scope
    assert "before any regime classifier" in scope
