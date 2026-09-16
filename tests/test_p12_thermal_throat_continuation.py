import numpy as np

from cases.studies import p12_thermal_throat_continuation as continuation
from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.variable_composition import variable_composition_conservative_to_primitive


def test_continuation_scope_and_controls_are_explicit() -> None:
    assert continuation.CASE_CLASSIFICATION == "P12_PROJECT_DEFINED_WARM_START_CONTINUATION"
    assert continuation.NOT_A_SOURCE_REPRODUCTION is True
    assert continuation.PROJECT_EQUIVALENCE_RATIOS == (0.20, 0.22, 0.24, 0.26, 0.28, 0.30)
    assert continuation.PROJECT_SONIC_TOLERANCE == 1.0e-3


def test_composition_consistent_warm_start_preserves_p_T_u() -> None:
    species = build_species_database()
    _dx, previous_mapping = continuation._build_mapping(0.20, 4, species)
    _dx, next_mapping = continuation._build_mapping(0.22, 4, species)
    previous_U = continuation._cold_start(previous_mapping, species)

    remapped_U = continuation.composition_consistent_warm_start(
        previous_U,
        previous_mapping,
        next_mapping,
        species,
    )
    previous = variable_composition_conservative_to_primitive(
        previous_U,
        previous_mapping.composition,
        species,
    )
    remapped = variable_composition_conservative_to_primitive(
        remapped_U,
        next_mapping.composition,
        species,
    )

    np.testing.assert_allclose(remapped.p, previous.p, rtol=2.0e-11, atol=1.0e-7)
    np.testing.assert_allclose(remapped.T, previous.T, rtol=2.0e-11, atol=1.0e-8)
    np.testing.assert_allclose(remapped.u, previous.u, rtol=1.0e-13, atol=1.0e-10)


def test_continuation_sequence_is_strictly_increasing() -> None:
    phis = continuation.PROJECT_EQUIVALENCE_RATIOS
    assert all(right > left for left, right in zip(phis, phis[1:]))
