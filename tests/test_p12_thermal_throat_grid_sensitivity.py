import json
from pathlib import Path

import pytest

from cases.studies import p12_thermal_throat_grid_sensitivity as study


def test_grid_sensitivity_scope_is_explicit() -> None:
    assert study.CASE_CLASSIFICATION == "P12_PROJECT_DEFINED_THERMAL_THROAT_GRID_SENSITIVITY"
    assert study.NOT_A_SOURCE_REPRODUCTION is True
    assert study.GRID_LEVELS == (20, 40, 80)
    assert study.CONTINUATION_EQUIVALENCE_RATIOS == (0.20, 0.22, 0.24, 0.26)
    assert study.TARGET_EQUIVALENCE_RATIOS == (0.24, 0.26)
    assert study.PROJECT_SONIC_TOLERANCE == 1.0e-3
    assert study.TEACHER_STEADY_TOLERANCE == 2.0e-5


def test_grid_level_rejects_unplanned_cell_count() -> None:
    with pytest.raises(ValueError, match="cells must be one of"):
        study.run_grid_level(30)


def test_continuation_acceptance_freezes_eq1146_result_without_overclaim() -> None:
    path = Path("cases/studies/data/p12_thermal_throat_continuation_acceptance.json")
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["not_a_source_reproduction"] is True
    assert record["teacher_eq_11_46_steady_tolerance"] == 2.0e-5
    assert record["mass_inventory_relative_to_inlet_gate"] == 0.005
    assert record["normalized_residual_role"].startswith("independent diagnostic only")
    assert record["workflow_evidence"]["head_sha"] == "88e03edd0c3a6764c908c68483f06f57de69e0a1"
    assert record["workflow_evidence"]["artifact_sha256"] == "e3ced4192e526ab711d96ae9b73fbcbf8fadb9e98361bc75bae7082593d12602"

    by_phi = {float(point["equivalence_ratio"]): point for point in record["points"]}
    assert set(by_phi) == {0.20, 0.22, 0.24, 0.26}
    for phi in (0.20, 0.22, 0.24):
        point = by_phi[phi]
        assert point["status"] == "CONVERGED"
        assert point["density_change"] <= record["teacher_eq_11_46_steady_tolerance"]
        assert point["mass_inventory_relative_to_inlet"] <= record["mass_inventory_relative_to_inlet_gate"]
        assert point["cao_thermal_throat_state"] == "SCRAM_SIDE"

    guarded = by_phi[0.26]
    assert guarded["status"] == "FORWARD_FLOW_GUARD_TRIGGERED"
    assert guarded["cao_thermal_throat_state"] is None
    assert "forward axial flow" in guarded["note"]
    assert "solver/model-domain inadmissible" in record["interpretation"]
    assert "No grid-independent transition equivalence ratio is claimed" in record["interpretation"]
