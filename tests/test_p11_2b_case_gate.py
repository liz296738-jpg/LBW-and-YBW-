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
            "source_id": "SRC-X",
            "operating_condition_id": "CASE-X",
            "length_unit": "m",
            "source_origin_description": "injector centreline",
            "solver_origin_description": "solver domain inlet",
            "scale_to_solver_m": 1.0,
            "offset_m": 0.25,
            "source_locators": ["Fig. X geometry definition"],
        },
        "geometry": {
            "source_id": "SRC-X",
            "operating_condition_id": "CASE-X",
            "source_locators": ["Fig. X area profile"],
            "area_profile_status": "FROZEN",
            "domain_length_m": 0.5,
            "area_model_description": "source-backed axisymmetric piecewise area profile",
        },
        "inlet_state": {
            "source_id": "SRC-X",
            "operating_condition_id": "CASE-X",
            "source_locators": ["Table X station-3 state"],
            "boundary_type": "supersonic-inflow",
            "rho_kg_m3": 0.5,
            "u_m_s": 1200.0,
            "p_Pa": 80_000.0,
        },
        "wall_friction": {
            "source_id": "SRC-X",
            "operating_condition_id": "CASE-X",
            "source_locators": ["Sec. X explicitly neglects wall friction"],
            "mode": "disabled_source_backed",
            "convention": "Darcy",
            "darcy_friction_factor": 0.0,
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


def absolute_tabulated_candidate() -> dict:
    candidate = complete_candidate()
    candidate["shape"] = {
        "model": "tabulated_line_heat",
        "source_id": "SRC-X",
        "operating_condition_id": "CASE-X",
        "source_locators": ["author supplementary absolute line-heat data"],
        "x_m": [0.0, 0.05, 0.10],
        "heat_release_rate_per_length_W_m": [0.0, 2.0e6, 1.0e6],
    }
    candidate.pop("absolute_energy")
    return candidate


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
    assert result["energy_scale_path"] == "separate_absolute_energy"
    assert result["cross_source_authorized"] is False


def test_formal_candidate_requires_geometry_inlet_and_friction_closure() -> None:
    for key, expected in (
        ("geometry", "missing geometry"),
        ("inlet_state", "missing inlet_state"),
        ("wall_friction", "missing wall_friction"),
    ):
        candidate = complete_candidate()
        candidate.pop(key)
        result = GATE.assess_formal_case_candidate(candidate)
        assert result["formal_case_ready"] is False
        assert expected in result["blockers"]


def test_geometry_must_be_solver_ready_and_inlet_must_be_primitive_supersonic() -> None:
    candidate = complete_candidate()
    candidate["geometry"]["area_profile_status"] = "PARTIAL"
    candidate["inlet_state"]["boundary_type"] = "subsonic-inflow-total"
    candidate["inlet_state"]["rho_kg_m3"] = 0.0
    result = GATE.assess_formal_case_candidate(candidate)

    assert result["formal_case_ready"] is False
    assert "geometry.area_profile_status must be 'FROZEN'" in result["blockers"]
    assert "inlet_state.boundary_type must be 'supersonic-inflow' for the current formal P11.2B path" in result["blockers"]
    assert "inlet_state.rho_kg_m3 must be positive" in result["blockers"]


def test_wall_friction_requires_source_backed_repository_convention() -> None:
    candidate = complete_candidate()
    candidate["wall_friction"] = {
        "source_id": "SRC-X",
        "operating_condition_id": "CASE-X",
        "source_locators": ["Sec. X friction coefficient"],
        "mode": "darcy_scalar_source_backed",
        "convention": "skin-friction-Cf",
        "darcy_friction_factor": 0.02,
        "hydraulic_diameter_m": 0.035,
    }
    result = GATE.assess_formal_case_candidate(candidate)
    assert result["formal_case_ready"] is False
    assert "darcy_scalar_source_backed requires wall_friction.convention='Darcy'" in result["blockers"]

    candidate["wall_friction"]["convention"] = "Darcy"
    result = GATE.assess_formal_case_candidate(candidate)
    assert result["formal_case_ready"] is True


def test_shape_and_energy_from_different_conditions_are_rejected() -> None:
    candidate = complete_candidate()
    candidate["absolute_energy"]["operating_condition_id"] = "OTHER-CASE"
    result = GATE.assess_formal_case_candidate(candidate)
    assert result["formal_case_ready"] is False
    assert "absolute_energy operating condition does not match candidate" in result["blockers"]


def test_cross_source_parameter_mixing_without_resolved_link_is_rejected() -> None:
    candidate = complete_candidate()
    candidate["shape"]["source_id"] = "SRC-OTHER"
    result = GATE.assess_formal_case_candidate(candidate)
    assert result["formal_case_ready"] is False
    assert (
        "shape.source_id must match candidate source_id or be authorized by a resolved cross_source_link"
        in result["blockers"]
    )


def test_unresolved_cross_source_link_does_not_authorize_mixing() -> None:
    candidate = complete_candidate()
    candidate["shape"]["source_id"] = "SRC-SHAPE"
    candidate["cross_source_link"] = {
        "status": "UNRESOLVED",
        "source_ids": ["SRC-X", "SRC-SHAPE"],
        "operating_condition_id": "CASE-X",
        "source_locators": ["paper comparison"],
        "link_description": "shape paper claims to fit the primary experiment",
    }
    result = GATE.assess_formal_case_candidate(candidate)
    assert result["formal_case_ready"] is False
    assert "cross_source_link.status must be 'RESOLVED' before cross-source promotion" in result["blockers"]
    assert result["cross_source_authorized"] is False


def test_resolved_traceable_cross_source_link_allows_explicit_closure_source() -> None:
    candidate = complete_candidate()
    candidate["shape"]["source_id"] = "SRC-SHAPE"
    candidate["absolute_energy"]["source_id"] = "SRC-SHAPE"
    candidate["cross_source_link"] = {
        "status": "RESOLVED",
        "source_ids": ["SRC-X", "SRC-SHAPE"],
        "operating_condition_id": "CASE-X",
        "source_locators": ["primary experiment run ID", "closure paper validation table"],
        "link_description": "closure paper explicitly identifies and fits the same primary experimental run",
    }
    result = GATE.assess_formal_case_candidate(candidate)
    assert result["formal_case_ready"] is True
    assert result["blockers"] == []
    assert result["cross_source_authorized"] is True


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


def test_tabulated_line_heat_is_already_an_absolute_energy_path() -> None:
    candidate = absolute_tabulated_candidate()
    result = GATE.assess_formal_case_candidate(candidate)

    assert result["formal_case_ready"] is True
    assert result["blockers"] == []
    assert result["energy_scale_path"] == "absolute_tabulated_line_heat"


def test_tabulated_line_heat_rejects_a_second_absolute_energy_scale() -> None:
    candidate = absolute_tabulated_candidate()
    candidate["absolute_energy"] = {
        "source_id": "SRC-X",
        "operating_condition_id": "CASE-X",
        "source_locators": ["duplicate total-power record"],
        "total_heat_release_power_W": 250_000.0,
    }
    result = GATE.assess_formal_case_candidate(candidate)

    assert result["formal_case_ready"] is False
    assert (
        "tabulated_line_heat already contains the absolute energy scale; omit absolute_energy"
        in result["blockers"]
    )


def test_tabulated_line_heat_requires_positive_strictly_ordered_profile() -> None:
    candidate = absolute_tabulated_candidate()
    candidate["shape"]["x_m"] = [0.0, 0.05, 0.05]
    result = GATE.assess_formal_case_candidate(candidate)

    assert result["formal_case_ready"] is False
    assert "tabulated shape x_m must be strictly increasing" in result["blockers"]
