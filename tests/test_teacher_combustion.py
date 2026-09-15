"""Regression tests for teacher Chapter 11 mixing and combustion closures."""

from __future__ import annotations

import math

import numpy as np
import pytest

from cases.studies.teacher_thermochemistry_database import build_species_database
from scramjet1d.teacher_combustion import (
    MIXING_LENGTH_C_M_RANGE,
    NORMAL_INJECTION_ALPHA_RANGE,
    STRUT_INJECTION_A_RANGE,
    TEACHER_AIR_AR_PER_O2,
    TEACHER_AIR_N2_PER_O2,
    equivalence_ratio,
    fuel_stoichiometric_ratio,
    lean_reaction_mass_fractions,
    lean_reaction_mole_amounts,
    mass_fractions_from_mole_amounts,
    mixing_efficiency_raw,
    mixing_length,
    mole_fractions,
    stoichiometric_fuel_air_ratio,
)


SPECIES = build_species_database()
FUEL_ATOMS = {
    "H2": (0, 2),
    "C2H4": (2, 4),
    "C10H22": (10, 22),
}
SPECIES_ATOMS = {
    "H2": {"H": 2},
    "C2H4": {"C": 2, "H": 4},
    "C10H22": {"C": 10, "H": 22},
    "O2": {"O": 2},
    "N2": {"N": 2},
    "AR": {"Ar": 1},
    "H2O": {"H": 2, "O": 1},
    "CO2": {"C": 1, "O": 2},
}


def _product_element_totals(amounts: dict[str, float]) -> dict[str, float]:
    totals = {"C": 0.0, "H": 0.0, "O": 0.0, "N": 0.0, "Ar": 0.0}
    for species, amount in amounts.items():
        for element, count in SPECIES_ATOMS[species].items():
            totals[element] += count * amount
    return totals


@pytest.mark.parametrize(
    ("fuel", "expected"),
    [
        ("H2", 3.0 / 103.0),
        ("C2H4", 0.068),
        ("C10H22", 0.0667),
    ],
)
def test_teacher_stoichiometric_ratios_match_textbook_values(fuel: str, expected: float) -> None:
    value = fuel_stoichiometric_ratio(fuel)  # type: ignore[arg-type]
    if fuel == "H2":
        assert value == pytest.approx(expected, rel=0.0, abs=1.0e-15)
    else:
        assert value == pytest.approx(expected, rel=0.0, abs=5.0e-5)


def test_general_stoichiometric_formula_matches_named_fuels() -> None:
    for fuel, (x, y) in FUEL_ATOMS.items():
        assert stoichiometric_fuel_air_ratio(x, y) == pytest.approx(
            fuel_stoichiometric_ratio(fuel), rel=0.0, abs=1.0e-15  # type: ignore[arg-type]
        )


def test_equivalence_ratio_reconstructs_requested_phi() -> None:
    air_flow = 0.85
    for fuel in ("H2", "C2H4", "C10H22"):
        requested_phi = 0.72
        fuel_flow = requested_phi * fuel_stoichiometric_ratio(fuel) * air_flow  # type: ignore[arg-type]
        assert equivalence_ratio(fuel_flow, air_flow, fuel) == pytest.approx(  # type: ignore[arg-type]
            requested_phi, rel=2.0e-15
        )


def test_mixing_length_implements_both_eq_11_20_branches() -> None:
    b = 0.035
    C_m = 40.0
    lean = mixing_length(0.8, b, C_m)
    rich = mixing_length(1.2, b, C_m)
    assert lean == pytest.approx(0.179 * C_m * math.exp(1.72 * 0.8) * b)
    assert rich == pytest.approx(3.333 * C_m * math.exp(-1.204 * 1.2) * b)


def test_mixing_length_branches_are_nearly_continuous_at_phi_one() -> None:
    b = 0.02
    C_m = 50.0
    left = mixing_length(1.0, b, C_m)
    right_limit = 3.333 * C_m * math.exp(-1.204) * b
    assert abs(left - right_limit) / left < 3.0e-4


def test_source_ranges_are_enforced_for_empirical_calibration_constants() -> None:
    with pytest.raises(ValueError, match="teacher-source range"):
        mixing_length(0.8, 0.03, MIXING_LENGTH_C_M_RANGE[0] - 0.1)
    with pytest.raises(ValueError, match="teacher-source range"):
        mixing_efficiency_raw(
            0.01,
            0.1,
            "normal",
            alpha=NORMAL_INJECTION_ALPHA_RANGE[1] + 0.01,
        )
    with pytest.raises(ValueError, match="teacher-source range"):
        mixing_efficiency_raw(
            0.01,
            0.1,
            "strut",
            A=STRUT_INJECTION_A_RANGE[0] - 0.01,
        )


def test_eq_11_19_parallel_and_strut_have_expected_complete_mixing_endpoints() -> None:
    L_m = 0.24
    x = np.array([0.0, 0.5 * L_m, L_m])
    parallel = mixing_efficiency_raw(x, L_m, "parallel")
    strut = mixing_efficiency_raw(x, L_m, "strut", A=2.5)
    np.testing.assert_allclose(parallel, [0.0, 0.5, 1.0], rtol=0.0, atol=1.0e-15)
    assert strut[0] == pytest.approx(0.0, abs=1.0e-15)
    assert strut[-1] == pytest.approx(1.0, abs=2.0e-15)
    assert np.all(np.diff(strut) > 0.0)


def test_normal_injection_correlation_is_returned_raw_without_silent_clipping() -> None:
    eta = float(mixing_efficiency_raw(1.0, 1.0, "normal", alpha=0.20))
    assert eta > 1.0
    assert eta == pytest.approx((1.0 + 1.0 / 250.0) ** 0.20)


@pytest.mark.parametrize("fuel", ["H2", "C2H4", "C10H22"])
def test_lean_reaction_equations_conserve_atoms(fuel: str) -> None:
    phi = 0.73
    eta = 0.64
    x, y = FUEL_ATOMS[fuel]
    nu_o2 = x + y / 4.0
    expected = {
        "C": x * phi,
        "H": y * phi,
        "O": 2.0 * nu_o2,
        "N": 2.0 * nu_o2 * TEACHER_AIR_N2_PER_O2,
        "Ar": nu_o2 * TEACHER_AIR_AR_PER_O2,
    }
    amounts = lean_reaction_mole_amounts(fuel, phi, eta)  # type: ignore[arg-type]
    totals = _product_element_totals(amounts)
    for element, value in expected.items():
        assert totals[element] == pytest.approx(value, rel=2.0e-15, abs=2.0e-15)


def test_hydrogen_complete_combustion_limit_matches_eq_11_27() -> None:
    phi = 0.6
    amounts = lean_reaction_mole_amounts("H2", phi, 1.0)
    assert amounts["H2"] == pytest.approx(0.0)
    assert amounts["H2O"] == pytest.approx(phi)
    assert amounts["O2"] == pytest.approx(0.5 * (1.0 - phi))
    assert amounts["CO2"] == pytest.approx(0.0)


def test_ethylene_no_combustion_limit_retains_fuel_and_oxidizer() -> None:
    phi = 0.55
    amounts = lean_reaction_mole_amounts("C2H4", phi, 0.0)
    assert amounts["C2H4"] == pytest.approx(phi)
    assert amounts["O2"] == pytest.approx(3.0)
    assert amounts["H2O"] == pytest.approx(0.0)
    assert amounts["CO2"] == pytest.approx(0.0)


def test_transcribed_composition_relations_reject_rich_or_unphysical_efficiency() -> None:
    with pytest.raises(ValueError, match="phi must lie in"):
        lean_reaction_mole_amounts("C2H4", 1.01, 0.8)
    with pytest.raises(ValueError, match="eta must lie in"):
        lean_reaction_mole_amounts("H2", 0.8, 1.01)


def test_mole_fraction_normalization_preserves_all_species_keys() -> None:
    amounts = lean_reaction_mole_amounts("H2", 1.0, 1.0)
    fractions = mole_fractions(amounts)
    assert set(fractions) == set(amounts)
    assert sum(fractions.values()) == pytest.approx(1.0, abs=2.0e-15)
    assert fractions["H2"] == pytest.approx(0.0)
    assert fractions["O2"] == pytest.approx(0.0)


@pytest.mark.parametrize("fuel", ["H2", "C2H4"])
def test_source_backed_core_database_converts_reaction_moles_to_mass_fractions(fuel: str) -> None:
    fractions = lean_reaction_mass_fractions(fuel, 0.75, 0.82, SPECIES)  # type: ignore[arg-type]
    assert sum(fractions.values()) == pytest.approx(1.0, abs=2.0e-15)
    assert all(value >= 0.0 for value in fractions.values())
    assert fractions[fuel] > 0.0
    assert fractions["O2"] > 0.0
    assert fractions["N2"] > 0.0
    assert fractions["AR"] > 0.0
    assert fractions["H2O"] > 0.0


def test_partial_c10h22_mass_fraction_conversion_remains_thermochemistry_gated() -> None:
    amounts = lean_reaction_mole_amounts("C10H22", 0.8, 0.7)
    with pytest.raises(ValueError, match="C10H22"):
        mass_fractions_from_mole_amounts(amounts, SPECIES)


def test_invalid_distance_and_atom_counts_are_rejected() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        mixing_efficiency_raw(-1.0e-3, 0.2, "parallel")
    with pytest.raises(ValueError, match="atom counts"):
        stoichiometric_fuel_air_ratio(2.5, 4)
    with pytest.raises(ValueError, match="not both zero"):
        stoichiometric_fuel_air_ratio(0, 0)
