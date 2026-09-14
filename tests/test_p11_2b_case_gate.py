"""Hard-gate tests for formal P11.2B source-backed heat-release cases."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "cases" / "studies" / "p11_2b_case_gate.py"
CLOSURE_PATH = ROOT / "cases" / "studies" / "p11_2b_heat_release_closure.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GATE = _load(GATE_PATH, "p11_2b_case_gate")
CLOSURE = _load(CLOSURE_PATH, "p11_2b_heat_release_closure_for_gate")


def complete_candidate() -> dict:
    return {
        "case_id": "SYNTHETIC-COMPLETE-GATE-TEST",
        "source_id": "SRC-X",
        "operating_condition_id": "CASE-X",
        "source_locators": ["Table X", "Eq. X"],
        "coordinate_mapping": {
            "length_unit": "m",
            "source_origin_description": "injector centreline",
            "solver_origin_description": "solver domain inlet",
            "scale_to_solver_m": 1.0,
            "offset_m": 0.25,
            "source_locators": ["Fig. X geometry definition"],
        },
        "shape": {
            "model": "eq8_asymmetric",
            "source_id": "SRC-X",
            "operating_condition_id": "CASE-X",
            "source_locators": ["Eq. 8 and Table X fitted parameters"],
            "x_initiation_m": 0.02,
            "x_peak_m": 0.08,
            "x_core_end_m": 0.16,
            "asymmetry_length_m": 0.0056,
        },
        "absolute_energy": {
            "source_id": "SRC-X",
            "operating_condition_id": "CASE-X",
            "source_locators": ["Table X total heat release"],
            "total_heat_release_power_W": 250_000.0,
        },
    }


def test_current_source_ledger_stays_formally_blocked() -> None:
    ledger = CLOSURE.load_heat_release_source_ledger()
    result = GATE.assess_ledger_formal_case_readiness(ledger)

    assert result["formal_case_ready"] is False
    assert result["ready_candidate_count"] == 0
    assert "no candidate_formal_cases declared" in result["blockers"]


def test_complete_same_condition_candidate_passes_gate() -> None:
    result = GATE.assess_formal_case_candidate(complete_candidate())
    assert result["formal_case_ready"] is True
    assert result["blockers"] == []


def test_shape_and_energy_from_different_conditions_are_rejected() -> None:
    candidate = complete_candidate()
    candidate["absolute_energy"]["operating_condition_id"] = "OTHER-CASE"
    result = GATE.assess_formal_case_candidate(candidate)
    assert result["formal_case_ready"] is False
    assert "absolute-energy operating condition does not match candidate" in result["blockers"]


def test_cross_source_parameter_mixing_is_rejected() -> None:
    candidate = complete_candidate()
    candidate["shape"]["source_id"] = "SRC-OTHER"
    result = GATE.assess_formal_case_candidate(candidate)
    assert result["formal_case_ready"] is False
    assert "shape.source_id must match candidate source_id" in result["blockers"]


def test_enthalpy_route_requires_mass_flow_and_excludes_duplicate_power() -> None:
    candidate = complete_candidate()
    candidate["absolute_energy"].pop("total_heat_release_power_W")
    candidate["absolute_energy"]["stagnation_enthalpy_increment_J_kg"] = 400_000.0
    result = GATE.assess_formal_case_candidate(candidate)
    assert result["formal_case_ready"] is False
    assert "stagnation-enthalpy route requires positive mass_flow_rate_kg_s" in result["blockers"]

    candidate["absolute_energy"]["mass_flow_rate_kg_s"] = 0.6
    result = GATE.assess_formal_case_candidate(candidate)
    assert result["formal_case_ready"] is True

    candidate["absolute_energy"]["total_heat_release_power_W"] = 100_000.0
    result = GATE.assess_formal_case_candidate(candidate)
    assert result["formal_case_ready"] is False
    assert "absolute_energy must provide exactly one of total power or stagnation-enthalpy increment" in result["blockers"]


def test_tabulated_line_heat_requires_positive_strictly_ordered_profile() -> None:
    candidate = complete_candidate()
    candidate["shape"] = {
        "model": "tabulated_line_heat",
        "source_id": "SRC-X",
        "operating_condition_id": "CASE-X",
        "source_locators": ["author supplementary data"],
        "x_m": [0.0, 0.05, 0.10],
        "heat_release_rate_per_length_W_m": [0.0, 2.0e6, 1.0e6],
    }
    assert GATE.assess_formal_case_candidate(candidate)["formal_case_ready"] is True

    candidate["shape"]["x_m"] = [0.0, 0.05, 0.05]
    result = GATE.assess_formal_case_candidate(candidate)
    assert result["formal_case_ready"] is False
    assert "tabulated shape x_m must be strictly increasing" in result["blockers"]
