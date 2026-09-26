"""Guards for the project-defined H2 baseline input provenance ledger."""
from __future__ import annotations

import json
from pathlib import Path

from cases.studies import p11_4_project_defined_h2_smoke as smoke
from scramjet1d.teacher_combustion import MIXING_LENGTH_C_M_RANGE


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "cases" / "studies" / "data" / "p11_4_project_defined_h2_input_provenance.json"


def _load() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_project_defined_physical_inputs_match_code() -> None:
    record = _load()
    inputs = record["physical_inputs"]

    expected = {
        "LENGTH_M": smoke.LENGTH_M,
        "INLET_AREA_M2": smoke.INLET_AREA_M2,
        "EXIT_AREA_M2": smoke.EXIT_AREA_M2,
        "COMBUSTOR_HEIGHT_M": smoke.COMBUSTOR_HEIGHT_M,
        "INLET_PRESSURE_PA": smoke.INLET_PRESSURE_PA,
        "INLET_TEMPERATURE_K": smoke.INLET_TEMPERATURE_K,
        "INLET_VELOCITY_M_PER_S": smoke.INLET_VELOCITY_M_PER_S,
        "EQUIVALENCE_RATIO": smoke.EQUIVALENCE_RATIO,
        "INJECTOR_X_M": smoke.INJECTOR_X_M,
        "MIXING_C_M": smoke.MIXING_C_M,
        "INJECTION_MODE": smoke.INJECTION_MODE,
        "FUEL_TEMPERATURE_K": smoke.FUEL_TEMPERATURE_K,
        "FUEL_AXIAL_VELOCITY_M_PER_S": smoke.FUEL_AXIAL_VELOCITY_M_PER_S,
        "WALL_HEAT_GRADIENT_J_PER_KG_PER_M": smoke.WALL_HEAT_GRADIENT_J_PER_KG_PER_M,
    }
    for name, value in expected.items():
        assert inputs[name]["value"] == value

    assert tuple(inputs["MIXING_C_M"]["source_range"]) == MIXING_LENGTH_C_M_RANGE
    assert inputs["MIXING_C_M"]["provenance"] == "PROJECT_SELECTED_WITHIN_TEACHER_SOURCE_RANGE"
    assert inputs["WALL_HEAT_GRADIENT_J_PER_KG_PER_M"]["provenance"] == "SOURCE_GATED_NEUTRALIZATION"


def test_project_defined_numerical_controls_match_code() -> None:
    controls = _load()["numerical_controls"]

    assert controls["CFL"]["value"] == smoke.PROJECT_CFL
    assert (
        controls["DEFAULT_DENSITY_CHANGE_TOLERANCE"]["value"]
        == smoke.DEFAULT_DENSITY_CHANGE_TOLERANCE
    )
    assert controls["DEFAULT_MAX_STEPS"]["value"] == smoke.DEFAULT_MAX_STEPS
    assert controls["GRID_LEVELS"]["value"] == [20, 40, 80]

    assert controls["DEFAULT_DENSITY_CHANGE_TOLERANCE"]["provenance"] == (
        "PROJECT_DEFINED_NUMERICAL_TOLERANCE"
    )


def test_phi_match_does_not_promote_case_to_cao_reproduction() -> None:
    record = _load()
    phi = record["physical_inputs"]["EQUIVALENCE_RATIO"]

    assert phi["value"] == 0.20
    assert phi["provenance"].endswith("CAO_CASE2_PHI_ONLY")
    assert record["source_reproduction"] is False
    assert "does not make the smoke case a Case 2 reproduction" in phi["note"]
