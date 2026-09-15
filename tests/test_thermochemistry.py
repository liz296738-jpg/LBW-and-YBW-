"""Tests for the teacher-reference variable thermochemistry foundation."""

import math

import pytest

from scramjet1d.thermochemistry import (
    UNIVERSAL_GAS_CONSTANT_J_PER_KMOL_K,
    SpeciesThermoPolynomial,
    mixture_molecular_weight,
    mixture_pressure,
    mixture_thermo_state,
    normalized_mass_fractions,
    temperature_from_specific_internal_energy,
)


def _constant_cp_species(name: str, gas_constant: float, cp: float, a6: float = 0.0) -> SpeciesThermoPolynomial:
    molecular_weight = UNIVERSAL_GAS_CONSTANT_J_PER_KMOL_K / gas_constant
    return SpeciesThermoPolynomial(
        name=name,
        molecular_weight_kg_per_kmol=molecular_weight,
        temperature_min_K=200.0,
        temperature_max_K=4000.0,
        coefficients=(cp / gas_constant, 0.0, 0.0, 0.0, 0.0, a6),
    )


def test_species_polynomial_matches_constant_cp_limit_and_enthalpy_offset() -> None:
    species = _constant_cp_species("X", gas_constant=300.0, cp=1200.0, a6=50.0)

    assert species.cp(1000.0) == pytest.approx(1200.0)
    assert species.h(1000.0) == pytest.approx(1200.0 * 1000.0 + 300.0 * 50.0)


def test_species_enthalpy_temperature_derivative_matches_cp() -> None:
    species = SpeciesThermoPolynomial(
        name="poly",
        molecular_weight_kg_per_kmol=28.0,
        temperature_min_K=200.0,
        temperature_max_K=3000.0,
        coefficients=(3.0, 1.0e-3, -2.0e-7, 4.0e-11, -3.0e-15, -900.0),
    )
    T = 1200.0
    delta = 1.0e-3
    derivative = (species.h(T + delta) - species.h(T - delta)) / (2.0 * delta)

    assert derivative == pytest.approx(species.cp(T), rel=2.0e-9)


def test_mixture_molecular_weight_uses_mass_fraction_reciprocal_rule() -> None:
    species = {
        "A": _constant_cp_species("A", gas_constant=300.0, cp=1200.0),
        "B": _constant_cp_species("B", gas_constant=200.0, cp=1000.0),
    }
    fractions = {"A": 0.25, "B": 0.75}
    expected_inverse_weight = (
        0.25 / species["A"].molecular_weight_kg_per_kmol
        + 0.75 / species["B"].molecular_weight_kg_per_kmol
    )

    assert mixture_molecular_weight(fractions, species) == pytest.approx(1.0 / expected_inverse_weight)


def test_mixture_state_matches_mass_weighted_cp_h_and_ideal_gas_relations() -> None:
    species = {
        "A": _constant_cp_species("A", gas_constant=300.0, cp=1200.0, a6=10.0),
        "B": _constant_cp_species("B", gas_constant=200.0, cp=1000.0, a6=-20.0),
    }
    fractions = {"A": 0.25, "B": 0.75}
    T = 1000.0
    state = mixture_thermo_state(T, fractions, species)

    expected_R = 0.25 * 300.0 + 0.75 * 200.0
    expected_cp = 0.25 * 1200.0 + 0.75 * 1000.0
    expected_h = 0.25 * species["A"].h(T) + 0.75 * species["B"].h(T)
    expected_cv = expected_cp - expected_R

    assert state.gas_constant_J_per_kg_K == pytest.approx(expected_R)
    assert state.cp_J_per_kg_K == pytest.approx(expected_cp)
    assert state.cv_J_per_kg_K == pytest.approx(expected_cv)
    assert state.gamma == pytest.approx(expected_cp / expected_cv)
    assert state.specific_enthalpy_J_per_kg == pytest.approx(expected_h)
    assert state.specific_internal_energy_J_per_kg == pytest.approx(expected_h - expected_R * T)


def test_mixture_pressure_equals_dalton_sum() -> None:
    species = {
        "A": _constant_cp_species("A", gas_constant=300.0, cp=1200.0),
        "B": _constant_cp_species("B", gas_constant=200.0, cp=1000.0),
    }
    fractions = {"A": 0.25, "B": 0.75}
    rho = 0.4
    T = 900.0
    pressure = mixture_pressure(rho, T, fractions, species)
    dalton = rho * T * (0.25 * 300.0 + 0.75 * 200.0)

    assert pressure == pytest.approx(dalton)


def test_single_species_constant_cp_limit_recovers_gamma_14() -> None:
    species = {"airlike": _constant_cp_species("airlike", gas_constant=287.0, cp=1004.5)}
    state = mixture_thermo_state(1000.0, {"airlike": 1.0}, species)

    assert state.gas_constant_J_per_kg_K == pytest.approx(287.0)
    assert state.cp_J_per_kg_K == pytest.approx(1004.5)
    assert state.gamma == pytest.approx(1004.5 / (1004.5 - 287.0))
    assert state.gamma == pytest.approx(1.4, rel=5.0e-4)


def test_internal_energy_temperature_inversion_recovers_original_temperature() -> None:
    species = {
        "A": SpeciesThermoPolynomial(
            name="A",
            molecular_weight_kg_per_kmol=28.0,
            temperature_min_K=200.0,
            temperature_max_K=4000.0,
            coefficients=(3.2, 7.0e-4, -1.0e-7, 0.0, 0.0, 100.0),
        ),
        "B": _constant_cp_species("B", gas_constant=250.0, cp=1100.0, a6=-25.0),
    }
    fractions = {"A": 0.6, "B": 0.4}
    expected_temperature = 1750.0
    target = mixture_thermo_state(expected_temperature, fractions, species).specific_internal_energy_J_per_kg

    recovered = temperature_from_specific_internal_energy(
        target,
        fractions,
        species,
        temperature_min_K=500.0,
        temperature_max_K=3000.0,
    )

    assert recovered == pytest.approx(expected_temperature, abs=2.0e-8)


def test_mass_fractions_are_validated_but_never_silently_renormalized() -> None:
    species = {"A": _constant_cp_species("A", gas_constant=287.0, cp=1004.5)}

    with pytest.raises(ValueError, match="sum to one"):
        normalized_mass_fractions({"A": 0.99}, species)
    with pytest.raises(ValueError, match="nonnegative"):
        normalized_mass_fractions({"A": -1.0}, species)
    with pytest.raises(ValueError, match="unknown species"):
        normalized_mass_fractions({"B": 1.0}, species)


def test_species_temperature_range_is_enforced_without_extrapolation() -> None:
    species = _constant_cp_species("A", gas_constant=287.0, cp=1004.5)

    with pytest.raises(ValueError, match="outside A validity range"):
        species.cp(100.0)
    with pytest.raises(ValueError, match="outside A validity range"):
        species.h(5000.0)


def test_internal_energy_inversion_rejects_unbracketed_target() -> None:
    species = {"A": _constant_cp_species("A", gas_constant=287.0, cp=1004.5)}
    fractions = {"A": 1.0}
    target = mixture_thermo_state(3000.0, fractions, species).specific_internal_energy_J_per_kg

    with pytest.raises(ValueError, match="outside the supplied temperature bracket"):
        temperature_from_specific_internal_energy(
            target,
            fractions,
            species,
            temperature_min_K=300.0,
            temperature_max_K=1000.0,
        )


def test_invalid_species_metadata_is_rejected() -> None:
    with pytest.raises(ValueError):
        SpeciesThermoPolynomial(
            name="",
            molecular_weight_kg_per_kmol=28.0,
            temperature_min_K=200.0,
            temperature_max_K=3000.0,
            coefficients=(1.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        )
    with pytest.raises(ValueError):
        SpeciesThermoPolynomial(
            name="X",
            molecular_weight_kg_per_kmol=math.nan,
            temperature_min_K=200.0,
            temperature_max_K=3000.0,
            coefficients=(1.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        )
