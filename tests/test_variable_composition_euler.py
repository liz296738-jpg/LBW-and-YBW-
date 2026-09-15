"""Verification for the teacher cell-wise composition Euler compatibility layer."""

from __future__ import annotations

import numpy as np
import pytest

from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.geometry import AreaProfile, constant_area_profile
from scramjet1d.variable_composition import (
    TeacherCompositionField,
    build_lean_teacher_composition_field,
    variable_composition_conservative_to_primitive,
    variable_composition_primitive_to_conservative,
)
from scramjet1d.variable_composition_euler import (
    variable_composition_euler_fluxes,
    variable_composition_geometric_area_source,
    variable_composition_internal_rusanov_fluxes,
    variable_composition_quasi_1d_rhs_transmissive,
    variable_composition_rusanov_flux,
    variable_composition_transmissive_interface_fluxes,
)
from scramjet1d.variable_euler import (
    variable_euler_flux,
    variable_quasi_1d_rhs_transmissive,
    variable_rusanov_flux,
)


SPECIES = build_species_database()


def _uniform_h2_field(num_cells: int) -> TeacherCompositionField:
    return build_lean_teacher_composition_field(
        "H2",
        phi=np.full(num_cells, 0.55),
        eta=np.full(num_cells, 0.45),
        species=SPECIES,
    )


def test_cell_physical_flux_uses_each_cells_own_composition() -> None:
    field = build_lean_teacher_composition_field(
        "H2",
        phi=np.array([0.25, 0.45, 0.70]),
        eta=np.array([0.10, 0.50, 0.90]),
        species=SPECIES,
    )
    states = variable_composition_primitive_to_conservative(
        rho=np.array([0.50, 0.42, 0.35]),
        u=np.array([900.0, 1200.0, 1450.0]),
        temperature_K=np.array([800.0, 1100.0, 1500.0]),
        field=field,
        species=SPECIES,
    )

    fluxes = variable_composition_euler_fluxes(states, field, SPECIES)
    assert fluxes.shape == (3, 3)
    assert np.all(np.isfinite(fluxes))
    for index in range(field.num_cells):
        expected = variable_euler_flux(
            states[index], field.composition_at(index), SPECIES
        )
        np.testing.assert_allclose(fluxes[index], expected, rtol=1.0e-13, atol=1.0e-8)


def test_pair_rusanov_reduces_exactly_to_fixed_composition_operator() -> None:
    field = _uniform_h2_field(2)
    composition = field.composition_at(0)
    states = variable_composition_primitive_to_conservative(
        rho=np.array([0.52, 0.38]),
        u=np.array([950.0, 1450.0]),
        temperature_K=np.array([850.0, 1350.0]),
        field=field,
        species=SPECIES,
    )

    expected = variable_rusanov_flux(
        states[0], states[1], composition, SPECIES
    )
    actual = variable_composition_rusanov_flux(
        states[0], states[1], composition, composition, SPECIES
    )
    np.testing.assert_allclose(actual, expected, rtol=1.0e-13, atol=1.0e-8)


def test_internal_fluxes_reduce_to_fixed_composition_vectorized_path() -> None:
    field = _uniform_h2_field(5)
    composition = field.composition_at(0)
    states = variable_composition_primitive_to_conservative(
        rho=np.linspace(0.60, 0.32, 5),
        u=np.linspace(700.0, 1500.0, 5),
        temperature_K=np.linspace(650.0, 1450.0, 5),
        field=field,
        species=SPECIES,
    )

    expected = variable_rusanov_flux(
        states[:-1], states[1:], composition, SPECIES
    )
    actual = variable_composition_internal_rusanov_fluxes(
        states, field, SPECIES
    )
    np.testing.assert_allclose(actual, expected, rtol=2.0e-12, atol=2.0e-7)


def test_transmissive_boundaries_equal_local_physical_flux() -> None:
    field = build_lean_teacher_composition_field(
        "C2H4",
        phi=np.array([0.30, 0.50, 0.75]),
        eta=np.array([0.15, 0.55, 0.90]),
        species=SPECIES,
    )
    states = variable_composition_primitive_to_conservative(
        rho=np.array([0.50, 0.43, 0.36]),
        u=np.array([850.0, 1100.0, 1350.0]),
        temperature_K=np.array([750.0, 1050.0, 1400.0]),
        field=field,
        species=SPECIES,
    )
    faces = variable_composition_transmissive_interface_fluxes(
        states, field, SPECIES
    )

    assert faces.shape == (4, 3)
    np.testing.assert_allclose(
        faces[0],
        variable_euler_flux(states[0], field.composition_at(0), SPECIES),
        rtol=1.0e-13,
        atol=1.0e-7,
    )
    np.testing.assert_allclose(
        faces[-1],
        variable_euler_flux(states[-1], field.composition_at(2), SPECIES),
        rtol=1.0e-13,
        atol=1.0e-7,
    )


def test_uniform_composition_quasi_1d_rhs_reduces_to_fixed_composition_path() -> None:
    field = _uniform_h2_field(4)
    composition = field.composition_at(0)
    states = variable_composition_primitive_to_conservative(
        rho=np.array([0.58, 0.50, 0.42, 0.35]),
        u=np.array([800.0, 1000.0, 1200.0, 1450.0]),
        temperature_K=np.array([700.0, 900.0, 1150.0, 1450.0]),
        field=field,
        species=SPECIES,
    )
    geometry = AreaProfile(
        cell_area=np.array([0.0105, 0.0115, 0.0125, 0.0135]),
        face_area=np.array([0.0100, 0.0110, 0.0120, 0.0130, 0.0140]),
    )
    dx = 0.025

    expected = variable_quasi_1d_rhs_transmissive(
        states, geometry, dx, composition, SPECIES
    )
    actual = variable_composition_quasi_1d_rhs_transmissive(
        states, field, geometry, dx, SPECIES
    )
    np.testing.assert_allclose(actual, expected, rtol=2.0e-12, atol=2.0e-7)


def test_variable_composition_constant_area_flux_is_globally_conservative() -> None:
    field = build_lean_teacher_composition_field(
        "H2",
        phi=np.linspace(0.25, 0.80, 6),
        eta=np.linspace(0.10, 0.95, 6),
        species=SPECIES,
    )
    states = variable_composition_primitive_to_conservative(
        rho=np.linspace(0.60, 0.30, 6),
        u=np.linspace(700.0, 1550.0, 6),
        temperature_K=np.linspace(650.0, 1550.0, 6),
        field=field,
        species=SPECIES,
    )
    geometry = constant_area_profile(6, area=0.02)
    dx = 0.015
    faces = variable_composition_transmissive_interface_fluxes(states, field, SPECIES)
    rhs = variable_composition_quasi_1d_rhs_transmissive(
        states, field, geometry, dx, SPECIES
    )

    integrated = np.sum(rhs, axis=0) * dx
    expected = -(faces[-1] - faces[0])
    np.testing.assert_allclose(integrated, expected, rtol=2.0e-12, atol=3.0e-7)


def test_geometric_source_uses_variable_composition_pressure() -> None:
    field = build_lean_teacher_composition_field(
        "C2H4",
        phi=np.array([0.30, 0.55, 0.80]),
        eta=np.array([0.20, 0.60, 0.95]),
        species=SPECIES,
    )
    states = variable_composition_primitive_to_conservative(
        rho=np.array([0.50, 0.42, 0.34]),
        u=np.array([850.0, 1100.0, 1400.0]),
        temperature_K=np.array([800.0, 1100.0, 1500.0]),
        field=field,
        species=SPECIES,
    )
    geometry = AreaProfile(
        cell_area=np.array([0.0105, 0.0115, 0.0125]),
        face_area=np.array([0.0100, 0.0110, 0.0120, 0.0130]),
    )
    dx = 0.02
    source = variable_composition_geometric_area_source(
        states, field, geometry, dx, SPECIES
    )
    primitive = variable_composition_conservative_to_primitive(states, field, SPECIES)
    expected = primitive.p * np.diff(geometry.face_area) / geometry.cell_area / dx

    np.testing.assert_allclose(source[:, 0], 0.0, atol=0.0)
    np.testing.assert_allclose(source[:, 2], 0.0, atol=0.0)
    np.testing.assert_allclose(source[:, 1], expected, rtol=2.0e-12, atol=1.0e-7)


def test_shape_and_field_guards_are_explicit() -> None:
    field = _uniform_h2_field(2)
    composition = field.composition_at(0)
    with pytest.raises(ValueError, match=r"shape \(3,\)"):
        variable_composition_rusanov_flux(
            [1.0, 2.0], [1.0, 2.0, 3.0], composition, composition, SPECIES
        )

    states = variable_composition_primitive_to_conservative(
        rho=np.array([0.5, 0.4]),
        u=np.array([800.0, 1000.0]),
        temperature_K=np.array([800.0, 1000.0]),
        field=field,
        species=SPECIES,
    )
    bad_geometry = constant_area_profile(3)
    with pytest.raises(ValueError, match="cell count"):
        variable_composition_geometric_area_source(
            states, field, bad_geometry, 0.01, SPECIES
        )
