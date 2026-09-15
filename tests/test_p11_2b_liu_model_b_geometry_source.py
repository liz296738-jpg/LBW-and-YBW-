"""Regression tests for the Liu model-B validation geometry evidence record."""

import json
import math
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


def test_model_b_transition_is_closed_by_source_backed_geometry_consistency() -> None:
    record = _load()
    geometry = record["confirmed_geometry_records"]
    derived = record["derived_geometry_consistency"]
    model_b = record["model_B_corollary"]

    ramp_projection = geometry["model_A_cavity_depth_m"] / math.tan(
        math.radians(geometry["model_A_cavity_ramp_angle_deg"])
    )
    replacement_length = geometry["model_A_cavity_floor_length_m"] + ramp_projection
    injector_to_divergence = (
        geometry["model_A_cavity_leading_edge_downstream_from_injector_m"]
        + replacement_length
    )
    reconstructed_total = (
        geometry["injector_location_downstream_from_inlet_lip_m"]
        + injector_to_divergence
        + geometry["downstream_diverging_combustor_length_m_from_SRC10"]
    )

    assert derived["cavity_ramp_axial_projection_m"] == ramp_projection
    assert derived["cavity_leading_edge_to_closeout_m"] == replacement_length
    assert derived["injector_to_divergence_start_m"] == injector_to_divergence
    assert derived["reconstructed_total_length_m"] == reconstructed_total
    assert derived["absolute_closure_residual_m"] < 5.0e-5

    assert model_b["derived_replacement_tube_axial_length_m"] == replacement_length
    assert model_b["derived_diverging_start_downstream_from_injector_m"] == injector_to_divergence
    assert model_b["axial_transition_status"] == "FROZEN_BY_SOURCE_BACKED_GEOMETRIC_CLOSURE"
    assert model_b["area_profile_status"] == "BLOCKED_ONLY_ON_2_DEG_CONE_ANGLE_CONVENTION"


def test_station3_is_preferred_solver_origin_and_transition_is_relative_to_it() -> None:
    record = _load()
    coordinate = record["coordinate_records"]
    model_b = record["model_B_corollary"]

    assert coordinate["station_3_definition"] == "isolator exit / combustor inlet / most-upstream fuel injection"
    assert coordinate["preferred_solver_origin"] == "station 3 / injector plane"
    assert coordinate["divergence_start_in_solver_coordinates_m"] == model_b[
        "derived_diverging_start_downstream_from_injector_m"
    ]
    assert coordinate["combustor_exit_in_solver_coordinates_m"] == (
        coordinate["divergence_start_in_solver_coordinates_m"] + 0.357
    )
    assert coordinate["source_to_solver_absolute_offset_m"] is None


def test_two_degree_cone_angle_convention_remains_the_only_area_profile_blocker() -> None:
    record = _load()
    assert any("2 degree cone angle" in item for item in record["evidence_boundary"])
    assert "2-degree cone-angle convention" in record["next_geometry_evidence_priority"]
