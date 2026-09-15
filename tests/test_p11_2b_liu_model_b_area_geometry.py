"""Tests for evidence-backed Liu model-B quasi-1D area geometry."""

import importlib.util
import math
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "cases" / "studies" / "p11_2b_liu_model_b_geometry.py"
SPEC = importlib.util.spec_from_file_location("p11_2b_liu_model_b_geometry", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_angle_evidence_remains_source_corroborated_not_primary_direct() -> None:
    evidence = MODULE.load_model_b_geometry_evidence()
    decision = evidence["angle"]["interpretation_decision"]

    assert decision["classification"] == "SOURCE_CORROBORATED_INTERPRETATION"
    assert decision["status"] == "READY_FOR_STUDY_LAYER_AREA_PROFILE"
    assert decision["wall_divergence_angle_deg"] == 2.0
    assert decision["primary_source_direct_definition"] is False


def test_model_b_area_profile_matches_tracked_geometry_metrics() -> None:
    geometry = MODULE.build_liu_model_b_area_geometry(240)
    profile = geometry.profile
    metadata = geometry.metadata

    inlet_area = math.pi * (0.035 / 2.0) ** 2
    assert profile.face_area[0] == pytest.approx(inlet_area, rel=2.0e-15)
    assert geometry.x_face_m[0] == 0.0
    assert geometry.x_face_m[-1] == pytest.approx(0.46055634918610404)
    assert metadata["divergence_start_m"] == pytest.approx(0.10355634918610404)
    assert metadata["wall_divergence_angle_deg"] == 2.0
    assert metadata["exit_to_inlet_area_ratio"] == pytest.approx(2.9322579279146552)
    assert metadata["formal_case_ready"] is False


def test_area_is_constant_upstream_and_monotone_after_divergence_start() -> None:
    geometry = MODULE.build_liu_model_b_area_geometry(500)
    x_face = geometry.x_face_m
    area = geometry.profile.face_area
    x_div = float(geometry.metadata["divergence_start_m"])

    upstream = x_face <= x_div
    assert np.allclose(area[upstream], area[0], rtol=0.0, atol=1.0e-18)

    downstream_area = area[x_face >= x_div]
    assert np.all(np.diff(downstream_area) >= 0.0)
    assert downstream_area[-1] > downstream_area[0]


def test_adopted_two_degree_wall_angle_is_materially_distinct_from_included_angle_counterfactual() -> None:
    evidence = MODULE.load_model_b_geometry_evidence()
    angle = evidence["angle"]
    adopted = angle["derived_area_profile_metrics"]
    counterfactual = angle["counterfactual_if_2_deg_were_full_included_angle"]

    assert adopted["adopted_wall_angle_deg"] == 2.0
    assert counterfactual["wall_angle_deg"] == 1.0
    assert adopted["exit_to_inlet_area_ratio"] == pytest.approx(2.9322579279146552)
    assert counterfactual["exit_to_inlet_area_ratio"] == pytest.approx(1.8389619830836306)
    assert counterfactual["adopted_to_counterfactual_area_ratio_factor"] == pytest.approx(
        adopted["exit_to_inlet_area_ratio"] / counterfactual["exit_to_inlet_area_ratio"]
    )


def test_geometry_builder_rejects_invalid_cell_counts() -> None:
    for invalid in (0, -1, True, 3.5):
        with pytest.raises(ValueError):
            MODULE.build_liu_model_b_area_geometry(invalid)
