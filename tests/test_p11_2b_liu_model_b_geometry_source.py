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
    assert {source["source_id"] for source in record["sources"]} == {"SRC10", "SRC11", "SRC12"}
    assert geometry["overall_model_length_m_from_SRC11"] == 0.752
    assert geometry["overall_model_length_m_from_SRC12"] == 0.75243
    assert geometry["inlet_length_m_from_SRC12"] == 0.03743
    assert geometry["isolator_diameter_m"] == 0.035
    assert geometry["isolator_length_m_from_SRC10"] == 0.254
    assert geometry["constant_diameter_length_from_inlet_end_to_cavity_leading_edge_m_from_SRC12"] == 0.296
    assert geometry["injector_location_downstream_from_inlet_lip_m"] == 0.2914
    assert geometry["model_A_cavity_leading_edge_downstream_from_injector_m"] == 0.042
    assert geometry["downstream_diverging_combustor_cone_angle_deg"] == 2.0
    assert geometry["downstream_diverging_combustor_length_m_from_SRC10"] == 0.357
    assert model_b["confirmed_constant_diameter_m"] == 0.035
    assert model_b["constant_section_from_injector_to_cavity_leading_edge_m"] == 0.042


def test_station3_and_constant_section_close_across_independent_sources() -> None:
    record = _load()
    geometry = record["confirmed_geometry_records"]
    derived = record["derived_geometry_consistency"]

    station3 = geometry["inlet_length_m_from_SRC12"] + geometry["isolator_length_m_from_SRC10"]
    assert math.isclose(station3, derived["station3_from_inlet_m"], rel_tol=0.0, abs_tol=1.0e-15)
    assert abs(station3 - geometry["injector_location_downstream_from_inlet_lip_m"]) <= 3.1e-5
    assert derived["station3_axial_closure_residual_mm"] <= 0.031

    to_cavity = geometry["isolator_length_m_from_SRC10"] + geometry[
        "model_A_cavity_leading_edge_downstream_from_injector_m"
    ]
    assert math.isclose(to_cavity, 0.296, rel_tol=0.0, abs_tol=1.0e-15)
    assert math.isclose(
        to_cavity,
        geometry["constant_diameter_length_from_inlet_end_to_cavity_leading_edge_m_from_SRC12"],
        rel_tol=0.0,
        abs_tol=1.0e-15,
    )


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
        geometry["model_A_cavity_leading_edge_downstream_from_injector_m"] + replacement_length
    )
    reconstructed_total_src10 = (
        geometry["injector_location_downstream_from_inlet_lip_m"]
        + injector_to_divergence
        + geometry["downstream_diverging_combustor_length_m_from_SRC10"]
    )
    reconstructed_total_src12 = (
        geometry["inlet_length_m_from_SRC12"]
        + geometry["constant_diameter_length_from_inlet_end_to_cavity_leading_edge_m_from_SRC12"]
        + replacement_length
        + geometry["downstream_diverging_combustor_length_m_from_SRC10"]
    )

    assert math.isclose(
        derived["cavity_ramp_axial_projection_m"], ramp_projection, rel_tol=0.0, abs_tol=1.0e-15
    )
    assert math.isclose(
        derived["cavity_leading_edge_to_closeout_m"], replacement_length, rel_tol=0.0, abs_tol=1.0e-15
    )
    assert math.isclose(
        derived["injector_to_divergence_start_m"], injector_to_divergence, rel_tol=0.0, abs_tol=1.0e-15
    )
    assert math.isclose(
        derived["reconstructed_total_length_m_using_SRC10_lip_reference"],
        reconstructed_total_src10,
        rel_tol=0.0,
        abs_tol=1.0e-15,
    )
    assert math.isclose(
        derived["reconstructed_total_length_m_using_SRC12_inlet_and_constant_section"],
        reconstructed_total_src12,
        rel_tol=0.0,
        abs_tol=1.0e-15,
    )
    assert derived["closure_residual_to_SRC11_mm"] < 0.05
    assert derived["closure_residual_to_SRC12_mm"] < 0.45

    assert math.isclose(
        model_b["derived_replacement_tube_axial_length_m"], replacement_length, rel_tol=0.0, abs_tol=1.0e-15
    )
    assert math.isclose(
        model_b["derived_diverging_start_downstream_from_injector_m"], injector_to_divergence, rel_tol=0.0, abs_tol=1.0e-15
    )
    assert model_b["axial_transition_status"] == "FROZEN_BY_SOURCE_BACKED_GEOMETRIC_CLOSURE"
    assert model_b["area_profile_status"] == "BLOCKED_ONLY_ON_2_DEG_CONE_ANGLE_CONVENTION"


def test_station3_coordinate_transform_is_frozen_without_figure_digitization() -> None:
    record = _load()
    coordinate = record["coordinate_records"]
    model_b = record["model_B_corollary"]

    assert coordinate["station_3_definition"] == "isolator exit / combustor inlet / most-upstream fuel injection"
    assert coordinate["preferred_solver_origin"] == "station 3 / injector plane"
    assert coordinate["source_station3_coordinate_m_from_SRC10"] == 0.2914
    assert math.isclose(
        coordinate["source_station3_coordinate_m_crosscheck_from_SRC12"],
        0.29143,
        rel_tol=0.0,
        abs_tol=1.0e-15,
    )
    assert coordinate["source_to_solver_absolute_offset_m"] == 0.2914
    assert coordinate["absolute_offset_status"] == "FROZEN_FROM_SRC10_AND_INDEPENDENTLY_CLOSED_BY_SRC12_DIMENSIONS"
    assert coordinate["divergence_start_in_solver_coordinates_m"] == model_b[
        "derived_diverging_start_downstream_from_injector_m"
    ]
    assert math.isclose(
        coordinate["combustor_exit_in_solver_coordinates_m"],
        coordinate["divergence_start_in_solver_coordinates_m"] + 0.357,
        rel_tol=0.0,
        abs_tol=1.0e-15,
    )


def test_two_degree_cone_angle_convention_remains_the_only_area_profile_blocker() -> None:
    record = _load()
    assert any("2 degree cone angle" in item for item in record["evidence_boundary"])
    assert "2-degree cone-angle convention" in record["next_geometry_evidence_priority"]
