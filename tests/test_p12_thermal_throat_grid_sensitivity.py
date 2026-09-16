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


def test_continuation_acceptance_freezes_near_sonic_result_without_overclaim() -> None:
    path = Path("cases/studies/data/p12_thermal_throat_continuation_acceptance.json")
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["not_a_source_reproduction"] is True
    assert record["accepted_head_sha"] == "7888173c44f75f45830b88babb07d3387bdce815"
    by_phi = {float(point["equivalence_ratio"]): point for point in record["points"]}
    assert by_phi[0.24]["cao_thermal_throat_state"] == "SCRAM_SIDE"
    assert by_phi[0.26]["cao_thermal_throat_state"] == "CRITICAL_TRANSITION_BAND"
    assert abs(by_phi[0.26]["sonic_margin"]) < record["project_sonic_tolerance"]
    assert by_phi[0.28]["cao_thermal_throat_state"] is None
    assert "not a grid-independent transition value" in record["interpretation"]
