"""Regression tests for per-cell teacher variable-composition compatibility."""

from __future__ import annotations

import numpy as np
import pytest

from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.variable_composition import (
    TeacherCompositionField,
    build_lean_teacher_composition_field,
    cell_temperature_bounds,
    variable_composition_conservative_to_primitive,
    variable_composition_primitive_to_conservative,
)
from scramjet1d.variable_state import (
    variable_conservative_to_primitive,
    variable_primitive_to_conservative,
)


SPECIES = build_species_database()


def test_hydrogen_composition_field_is_normalized_nonnegative_and_immutable() -> None:
    field = build_lean_teacher_composition_field(
        "H2",
        np.array([0.35, 0.55, 0.75, 1.0]),
        np.array([0.0, 0.35, 0.75, 1.0]),
        SPECIES,
    )
    assert field.num_cells == 4
    assert field.num_species == 6
    assert field.species_names == ("H2", "O2", "N2", "AR", "H2O", "CO2")
    np.testing.assert_allclose(np.sum(field.mass_fractions, axis=1), 1.0, atol=2.0e-15)
    assert np.all(field.mass_fractions >= 0.0)
    assert field.mass_fractions.flags.writeable is False
    with pytest.raises(ValueError):
        field.mass_fractions[0, 0] = 0.2


def test_ethylene_field_uses_source_backed_core_species() -> None:
    field = build_lean_teacher_composition_field(
        "C2H4",
        np.array([0.4, 0.7, 0.9]),
        np.array([0.2, 0.6, 0.95]),
        SPECIES,
    )
    assert field.species_names == ("C2H4", "O2", "N2", "AR", "H2O", "CO2")
    for index in range(field.num_cells):
        composition = field.composition_at(index)
        assert set(composition).issubset(SPECIES)
        assert sum(composition.values()) == pytest.approx(1.0, abs=2.0e-15)


def test_fuel_fraction_decreases_and_product_fraction_increases_with_eta() -> None:
    eta = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    field = build_lean_teacher_composition_field(
        "C2H4", np.full(eta.size, 0.7), eta, SPECIES
    )
    fuel_column = field.species_names.index("C2H4")
    water_column = field.species_names.index("H2O")
    carbon_dioxide_column = field.species_names.index("CO2")
    assert np.all(np.diff(field.mass_fractions[:, fuel_column]) < 0.0)
    assert np.all(np.diff(field.mass_fractions[:, water_column]) > 0.0)
    assert np.all(np.diff(field.mass_fractions[:, carbon_dioxide_column]) > 0.0)


def test_cell_temperature_bounds_are_source_backed_and_include_working_range() -> None:
    field = build_lean_teacher_composition_field(
        "H2", np.array([0.4, 0.8]), np.array([0.3, 0.9]), SPECIES
    )
    lower, upper = cell_temperature_bounds(field, SPECIES)
    assert lower.shape == (2,)
    assert upper.shape == (2,)
    assert np.all(lower <= 300.0)
    assert np.all(upper >= 3000.0)
    assert np.all(upper > lower)


def test_variable_composition_round_trip_recovers_each_cell_state() -> None:
    field = build_lean_teacher_composition_field(
        "H2",
        np.array([0.35, 0.55, 0.75, 0.95]),
        np.array([0.15, 0.45, 0.75, 1.0]),
        SPECIES,
    )
    rho = np.array([0.72, 0.55, 0.39, 0.25])
    u = np.array([650.0, 1050.0, 1450.0, 1850.0])
    T = np.array([600.0, 999.0, 1000.0, 1800.0])

    U = variable_composition_primitive_to_conservative(rho, u, T, field, SPECIES)
    recovered = variable_composition_conservative_to_primitive(U, field, SPECIES)

    np.testing.assert_allclose(recovered.rho, rho, rtol=0.0, atol=1.0e-13)
    np.testing.assert_allclose(recovered.u, u, rtol=0.0, atol=1.0e-12)
    np.testing.assert_allclose(recovered.T, T, rtol=0.0, atol=3.0e-7)
    assert np.all(recovered.p > 0.0)
    assert np.all(recovered.gamma > 1.0)
    assert np.all(np.isfinite(recovered.h))


def test_uniform_composition_field_reduces_exactly_to_fixed_composition_state_path() -> None:
    base = build_lean_teacher_composition_field(
        "C2H4", np.array([0.65]), np.array([0.55]), SPECIES
    )
    composition = base.composition_at(0)
    values = np.repeat(base.mass_fractions, 3, axis=0)
    field = TeacherCompositionField(base.species_names, values)

    rho = np.array([0.8, 0.6, 0.4])
    u = np.array([500.0, 1000.0, 1500.0])
    T = np.array([700.0, 1100.0, 1700.0])
    variable_U = variable_composition_primitive_to_conservative(rho, u, T, field, SPECIES)
    fixed_U = variable_primitive_to_conservative(rho, u, T, composition, SPECIES)
    np.testing.assert_allclose(variable_U, fixed_U, rtol=0.0, atol=0.0)

    variable_primitive = variable_composition_conservative_to_primitive(
        variable_U, field, SPECIES
    )
    fixed_primitive = variable_conservative_to_primitive(fixed_U, composition, SPECIES)
    for attribute in ("rho", "u", "p", "T", "Mach", "gamma", "R", "cp", "h"):
        np.testing.assert_allclose(
            getattr(variable_primitive, attribute),
            getattr(fixed_primitive, attribute),
            rtol=2.0e-12,
            atol=3.0e-7,
        )


def test_scalar_primitive_inputs_broadcast_across_composition_field() -> None:
    field = build_lean_teacher_composition_field(
        "H2", np.array([0.4, 0.6, 0.8]), np.array([0.2, 0.6, 1.0]), SPECIES
    )
    U = variable_composition_primitive_to_conservative(0.5, 1200.0, 900.0, field, SPECIES)
    assert U.shape == (3, 3)
    recovered = variable_composition_conservative_to_primitive(U, field, SPECIES)
    np.testing.assert_allclose(recovered.rho, 0.5, atol=1.0e-13)
    np.testing.assert_allclose(recovered.u, 1200.0, atol=1.0e-12)
    np.testing.assert_allclose(recovered.T, 900.0, atol=3.0e-7)


def test_c10h22_and_rich_composition_remain_explicitly_gated() -> None:
    with pytest.raises(ValueError, match="C10H22 thermochemistry remains source-gated"):
        build_lean_teacher_composition_field(
            "C10H22", np.array([0.8]), np.array([0.7]), SPECIES
        )
    with pytest.raises(ValueError, match="phi must lie in"):
        build_lean_teacher_composition_field(
            "H2", np.array([1.01]), np.array([0.8]), SPECIES
        )


def test_field_and_state_shape_validation_rejects_mismatch() -> None:
    with pytest.raises(ValueError, match="sum to one"):
        TeacherCompositionField(("H2", "O2"), np.array([[0.4, 0.4]]))
    with pytest.raises(ValueError, match="unique"):
        TeacherCompositionField(("H2", "H2"), np.array([[0.5, 0.5]]))

    field = build_lean_teacher_composition_field(
        "H2", np.array([0.4, 0.6]), np.array([0.3, 0.7]), SPECIES
    )
    with pytest.raises(ValueError, match=r"shape \(2, 3\)"):
        variable_composition_conservative_to_primitive(np.ones((3, 3)), field, SPECIES)
    with pytest.raises(ValueError, match=r"broadcast to \(2,\)"):
        variable_composition_primitive_to_conservative(
            np.ones(3), 1000.0, 900.0, field, SPECIES
        )
