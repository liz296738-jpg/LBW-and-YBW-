"""Regression tests for the Liu model-B validation geometry evidence record."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "cases" / "studies" / "data" / "p11_2b_liu_model_b_geometry_source.json"


def _load() -> dict:
    return json.loads(RECORD.read_text(encoding="utf-8"))


def test_source_backed_model_b_geometry_records_are_retained() -> None:
    record = _load()
    geometry = record["confirmed_geometry_records"]
    model_b = record["model_B_corollary"]

    assert record["candidate_id"] == "JIN-LIU-MODEL-B-VALIDATION"
    assert {source["source_id"] for source in record["sources"]} == {"SRC10", "SRC11"}
    assert geometry["overall_model_length_m_from_SRC11"] == 0.752
    assert geometry["isolator_diameter_m"] == 0.035
    assert geometry["isolator_length_m_from_SRC10"] == 0.254
    assert geometry["injector_location_downstream_from_inlet_lip_m"] == 0.2914
    assert geometry["model_A_cavity_leading_edge_downstream_from_injector_m"] == 0.042
    assert geometry["downstream_diverging_combustor_cone_angle_deg"] == 2.0
    assert geometry["downstream_diverging_combustor_length_m_from_SRC10"] == 0.357
    assert model_b["confirmed_constant_diameter_m"] == 0.035
    assert model_b["constant_section_from_injector_to_cavity_leading_edge_m"] == 0.042


def test_unresolved_model_b_transition_is_not_silently_frozen() -> None:
    record = _load()
    model_b = record["model_B_corollary"]

    assert model_b["exact_replacement_tube_axial_length_m"] is None
    assert model_b["diverging_start_downstream_from_injector_m"] is None
    assert model_b["status"] == "PARTIALLY_FROZEN_GEOMETRY_TRANSITION_LOCATION_UNRESOLVED"
    assert any("2 degree cone angle" in item for item in record["evidence_boundary"])


def test_station3_is_preferred_solver_origin_without_inventing_absolute_offset() -> None:
    record = _load()
    coordinate = record["coordinate_records"]

    assert coordinate["station_3_definition"] == "isolator exit / combustor inlet / most-upstream fuel injection"
    assert coordinate["preferred_solver_origin"] == "station 3 / injector plane"
    assert coordinate["source_to_solver_absolute_offset_m"] is None
