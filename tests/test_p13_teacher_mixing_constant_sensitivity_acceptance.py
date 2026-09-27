"""Acceptance guards for the frozen P13 teacher-range C_m sensitivity."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = (
    ROOT
    / "cases"
    / "studies"
    / "data"
    / "p13_teacher_mixing_constant_sensitivity_acceptance.json"
)


def _record() -> dict:
    return json.loads(ACCEPTANCE.read_text(encoding="utf-8"))


def test_p13_acceptance_freezes_successful_parallel_workflow() -> None:
    record = _record()
    provenance = record["provenance"]

    assert record["classification"] == (
        "P13_TEACHER_MIXING_CONSTANT_SENSITIVITY_ACCEPTANCE"
    )
    assert record["not_a_source_reproduction"] is True
    assert record["not_experimental_validation"] is True
    assert provenance["accepted_head_sha"] == (
        "b92b9095b818f835c9d485278334a45245ac40f7"
    )
    assert provenance["workflow_run_id"] == 36312725524
    assert provenance["workflow_run_number"] == 4
    assert provenance["aggregate_artifact_id"] == 10929383596
    assert provenance["aggregate_artifact_zip_sha256"] == (
        "c08ec1ccc28decdf31dbd4b82fa00e1ac2866a9d6939cef21d9a5e4c073a6dec"
    )


def test_all_p13_points_pass_frozen_numerical_and_mass_qa() -> None:
    record = _record()
    points = record["points"]

    assert len(points) == 8
    assert {(row["mixing_C_m"], row["cells"]) for row in points} == {
        (C_m, cells)
        for C_m in (25.0, 30.0, 42.5, 60.0)
        for cells in (20, 40)
    }
    for row in points:
        assert row["status"] == "CONVERGED"
        assert row["converged"] is True
        assert row["density_change"] <= 2.0e-5
        assert row["mass_inventory_relative_to_inlet"] <= 5.0e-3
        assert row["min_pressure_Pa"] > 0.0
        assert row["min_temperature_K"] > 0.0

    fuel = {row["fuel_mass_source_kg_per_s"] for row in points}
    assert fuel == {0.006975386332365369}


def test_pressure_and_temperature_response_is_monotonic_on_both_grids() -> None:
    points = _record()["points"]

    for cells in (20, 40):
        rows = sorted(
            (row for row in points if row["cells"] == cells),
            key=lambda row: row["mixing_C_m"],
        )
        max_pressure = [row["max_pressure_Pa"] for row in rows]
        max_temperature = [row["max_temperature_K"] for row in rows]

        assert all(a > b for a, b in zip(max_pressure, max_pressure[1:]))
        assert all(a > b for a, b in zip(max_temperature, max_temperature[1:]))


def test_minimum_mach_is_not_promoted_as_monotonic() -> None:
    points = _record()["points"]

    min_mach_20 = {
        row["mixing_C_m"]: row["min_mach"]
        for row in points
        if row["cells"] == 20
    }
    min_mach_40 = {
        row["mixing_C_m"]: row["min_mach"]
        for row in points
        if row["cells"] == 40
    }

    # Low-C_m ordering reverses between grids, so a monotonic-Mach claim would
    # be scientifically unsupported.
    assert min_mach_20[25.0] > min_mach_20[30.0]
    assert min_mach_40[25.0] < min_mach_40[30.0]

    interpretation = " ".join(_record()["accepted_interpretation"])
    assert "not promoted as a monotonic function" in interpretation


def test_two_grid_changes_remain_robustness_only() -> None:
    record = _record()
    changes = record["grid_changes"]

    assert [row["mixing_C_m"] for row in changes] == [25.0, 30.0, 42.5, 60.0]
    assert all(row["coarse_cells"] == 20 for row in changes)
    assert all(row["fine_cells"] == 40 for row in changes)

    limits = record["acceptance_policy"]["interpretation_limits"]
    assert "No optimum C_m is claimed." in limits
    assert "No experimental validation is claimed." in limits
    assert "No Cao Case 2 reproduction is claimed." in limits
