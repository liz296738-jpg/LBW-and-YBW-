import numpy as np
import pytest

from scramjet1d.cao_mode_criteria import (
    CaoTable31State,
    ThermalThroatState,
    classify_cao_table_3_1,
    classify_thermal_throat,
)


def test_thermal_throat_source_sides_and_explicit_transition_band() -> None:
    assert (
        classify_thermal_throat([2.0, 1.3, 1.05], sonic_tolerance=0.01).state
        == ThermalThroatState.SCRAM_SIDE
    )
    assert (
        classify_thermal_throat([2.0, 1.4, 0.85], sonic_tolerance=0.01).state
        == ThermalThroatState.RAM_SIDE
    )
    critical = classify_thermal_throat(
        np.array([2.0, 1.2, 1.005]), sonic_tolerance=0.01
    )
    assert critical.state == ThermalThroatState.CRITICAL_TRANSITION_BAND
    assert critical.minimum_mach == pytest.approx(1.005)


def test_thermal_throat_requires_explicit_valid_numerical_tolerance() -> None:
    with pytest.raises(TypeError):
        classify_thermal_throat([1.2, 1.1])
    for tolerance in (0.0, -1.0, 1.0):
        with pytest.raises(ValueError):
            classify_thermal_throat([1.2, 1.1], sonic_tolerance=tolerance)


def test_thermal_throat_rejects_invalid_profiles() -> None:
    for profile in ([], [1.2, 0.0], [1.2, float("nan")]):
        with pytest.raises(ValueError):
            classify_thermal_throat(profile, sonic_tolerance=0.01)
    with pytest.raises(ValueError):
        classify_thermal_throat(1.2, sonic_tolerance=0.01)


def test_table_3_1_source_criteria_are_transcribed_without_equality_guessing() -> None:
    no_shock = classify_cao_table_3_1(
        ma_s=2.0, ma_2=2.5, ma_3m=2.0, ma_2min=0.7
    )
    assert no_shock.state == CaoTable31State.NO_SHOCK_SCRAM

    oblique = classify_cao_table_3_1(
        ma_s=1.5, ma_2=2.5, ma_3m=2.0, ma_2min=0.7
    )
    assert oblique.state == CaoTable31State.OBLIQUE_SHOCK_SCRAM

    ram = classify_cao_table_3_1(
        ma_s=0.8, ma_2=1.2, ma_3m=1.5, ma_2min=0.7
    )
    assert ram.state == CaoTable31State.RAM

    boundary = classify_cao_table_3_1(
        ma_s=0.762 * 2.5, ma_2=2.5, ma_3m=2.0, ma_2min=0.7
    )
    assert boundary.state == CaoTable31State.BOUNDARY_OR_UNCLASSIFIED


def test_table_3_1_does_not_force_mathematically_overlapping_inputs() -> None:
    # With arbitrary independent inputs, the no-shock Ma_s inequality and the
    # ram Ma_2 interval can both be true. Such a set is not a source-consistent
    # physical state, so the implementation must not pick one by precedence.
    result = classify_cao_table_3_1(
        ma_s=1.0, ma_2=1.2, ma_3m=1.5, ma_2min=0.7
    )
    assert result.state == CaoTable31State.BOUNDARY_OR_UNCLASSIFIED


def test_table_3_1_validates_characteristic_mach_ordering() -> None:
    with pytest.raises(ValueError, match="ma_2min"):
        classify_cao_table_3_1(
            ma_s=1.0, ma_2=1.2, ma_3m=0.7, ma_2min=0.7
        )
