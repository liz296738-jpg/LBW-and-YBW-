"""Contract tests for the P13 teacher-range C_m sensitivity definition."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from cases.studies import p11_4_project_defined_h2_smoke as baseline
from cases.studies import p13_teacher_mixing_constant_sensitivity as study
from scramjet1d.teacher_combustion import MIXING_LENGTH_C_M_RANGE, mixing_length


ROOT = Path(__file__).resolve().parents[1]
DEFINITION = (
    ROOT
    / "cases"
    / "studies"
    / "data"
    / "p13_teacher_mixing_constant_sensitivity_definition.json"
)


def test_p13_sampling_uses_teacher_range_and_preserves_project_baseline() -> None:
    assert study.SOURCE_RANGE == tuple(float(v) for v in MIXING_LENGTH_C_M_RANGE)
    assert study.SOURCE_RANGE == (25.0, 60.0)
    assert study.PROJECT_SAMPLE_VALUES == (25.0, 30.0, 42.5, 60.0)
    assert baseline.MIXING_C_M == 30.0
    assert study.PROJECT_SAMPLE_VALUES[2] == pytest.approx(
        0.5 * (study.SOURCE_RANGE[0] + study.SOURCE_RANGE[1])
    )


def test_p13_definition_labels_source_and_project_roles_explicitly() -> None:
    record = json.loads(DEFINITION.read_text(encoding="utf-8"))

    assert record["classification"] == study.CASE_CLASSIFICATION
    assert record["source_reproduction"] is False
    assert record["varied_parameter"]["source_range"] == [25.0, 60.0]
    roles = {row["value"]: row["role"] for row in record["samples"]}
    assert roles[25.0] == "SOURCE_RANGE_LOWER_BOUND"
    assert roles[30.0] == "CURRENT_PROJECT_BASELINE"
    assert roles[42.5] == "PROJECT_DEFINED_ARITHMETIC_RANGE_MIDPOINT"
    assert roles[60.0] == "SOURCE_RANGE_UPPER_BOUND"
    assert record["acceptance_policy"]["no_optimum_claim"] is True
    assert record["acceptance_policy"]["no_experimental_validation_claim"] is True


def test_changing_C_m_changes_only_mixing_closure_not_frozen_injector_strength() -> None:
    low = baseline.build_case(20, mixing_C_m=25.0)
    high = baseline.build_case(20, mixing_C_m=60.0)

    low_mapping = low[2]
    high_mapping = high[2]
    dx = low[1]

    # Eq.11.20 C_m changes the mixing length/efficiency field.
    assert not np.allclose(
        low_mapping.downstream_closure.mixing_length_m,
        high_mapping.downstream_closure.mixing_length_m,
        rtol=0.0,
        atol=0.0,
    )

    # Fuel injection strength is frozen because phi, inlet state and geometry
    # are unchanged by this sensitivity factor.
    low_fuel = float(np.sum(low_mapping.fuel_mass_flow_gradient_kg_per_s_per_m) * dx)
    high_fuel = float(np.sum(high_mapping.fuel_mass_flow_gradient_kg_per_s_per_m) * dx)
    assert low_fuel == pytest.approx(high_fuel, rel=0.0, abs=0.0)


def test_p13_rejects_values_outside_teacher_source_range() -> None:
    with pytest.raises(ValueError, match="teacher-source range"):
        study._validate_C_m(24.99)
    with pytest.raises(ValueError, match="teacher-source range"):
        study._validate_C_m(60.01)


def test_parallel_closure_has_preregistered_C_m_monotonicity() -> None:
    low = baseline.build_case(40, mixing_C_m=25.0)[2].downstream_closure
    high = baseline.build_case(40, mixing_C_m=60.0)[2].downstream_closure

    # Eq.11.20: with frozen phi and b, L_m is exactly proportional to C_m.
    np.testing.assert_allclose(
        high.mixing_length_m / low.mixing_length_m,
        np.full_like(low.mixing_length_m, 60.0 / 25.0),
        rtol=2.0e-15,
        atol=0.0,
    )

    # Current baseline uses the parallel Eq.11.19 branch eta_raw=x/L_m, so a
    # larger C_m cannot increase raw or physical combustion efficiency at any
    # fixed downstream cell.
    assert np.all(high.raw_mixing_efficiency <= low.raw_mixing_efficiency)
    assert np.all(high.combustion_efficiency <= low.combustion_efficiency)


def test_eq_11_20_baseline_geometry_separates_full_mixing_regimes() -> None:
    downstream_available = baseline.LENGTH_M - baseline.INJECTOR_X_M
    assert downstream_available == pytest.approx(0.32)

    lengths = {
        C_m: mixing_length(
            baseline.EQUIVALENCE_RATIO,
            baseline.COMBUSTOR_HEIGHT_M,
            C_m,
        )
        for C_m in study.PROJECT_SAMPLE_VALUES
    }

    assert lengths[25.0] == pytest.approx(0.25249357575587444)
    assert lengths[30.0] == pytest.approx(0.3029922909070493)
    assert lengths[42.5] == pytest.approx(0.4292390787849865)
    assert lengths[60.0] == pytest.approx(0.6059845818140986)

    assert lengths[25.0] < downstream_available
    assert lengths[30.0] < downstream_available
    assert lengths[42.5] > downstream_available
    assert lengths[60.0] > downstream_available
