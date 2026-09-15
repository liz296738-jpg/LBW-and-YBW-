"""Regression tests for the source-backed P11.3B thermochemistry database."""

import pytest

from cases.studies.teacher_thermochemistry_database import (
    build_readiness,
    build_species_database,
    load_source_record,
    validate_berkeley_cp_298,
    validate_switch_continuity,
)
from scramjet1d.thermochemistry import (
    PiecewiseSpeciesThermo,
    SpeciesThermoPolynomial,
    mixture_thermo_state,
)


def test_core_database_freezes_teacher_hydrogen_and_ethylene_species() -> None:
    database = build_species_database()

    assert set(database) == {"H2", "O2", "N2", "AR", "H2O", "C2H4", "CO2"}
    assert all(isinstance(model, PiecewiseSpeciesThermo) for model in database.values())
    assert database["H2"].switch_temperature_K == 1000.0
    assert database["C2H4"].temperature_min_K == 200.0
    assert database["N2"].temperature_max_K == 5000.0


def test_low_and_high_intervals_are_continuous_at_source_switch() -> None:
    diagnostics = validate_switch_continuity()

    assert set(diagnostics) == {"H2", "O2", "N2", "AR", "H2O", "C2H4", "CO2"}
    assert max(row["cp_relative_jump"] for row in diagnostics.values()) < 1.0e-5
    assert max(row["h_relative_jump"] for row in diagnostics.values()) < 1.0e-5


def test_polynomials_reproduce_berkeley_rounded_298K_cp_table() -> None:
    diagnostics = validate_berkeley_cp_298()

    for row in diagnostics.values():
        assert abs(row["difference_cal_per_mol_K"]) < 0.03
    assert diagnostics["C2H4"]["computed_cp_cal_per_mol_K"] == pytest.approx(10.25, abs=0.03)
    assert diagnostics["H2"]["computed_cp_cal_per_mol_K"] == pytest.approx(6.89, abs=0.03)


def test_piecewise_database_is_usable_in_teacher_mixture_relations_across_switch() -> None:
    database = build_species_database()
    composition = {"O2": 0.233, "N2": 0.767}

    low = mixture_thermo_state(900.0, composition, database)
    high = mixture_thermo_state(1100.0, composition, database)

    assert low.cp_J_per_kg_K > 0.0
    assert high.cp_J_per_kg_K > low.cp_J_per_kg_K
    assert 1.0 < low.gamma < 1.5
    assert 1.0 < high.gamma < 1.5
    assert high.specific_enthalpy_J_per_kg > low.specific_enthalpy_J_per_kg


def test_piecewise_species_selects_high_interval_only_above_switch() -> None:
    database = build_species_database()
    model = database["C2H4"]

    assert model.cp(1000.0) == pytest.approx(model.low.cp(1000.0))
    assert model.cp(1000.001) == pytest.approx(model.high.cp(1000.001))
    with pytest.raises(ValueError, match="outside C2H4 validity range"):
        model.cp(199.0)


def test_piecewise_model_rejects_mismatched_species_or_switch() -> None:
    low = SpeciesThermoPolynomial(
        "A", 28.0, 200.0, 1000.0, (3.5, 0.0, 0.0, 0.0, 0.0, 0.0)
    )
    wrong_name = SpeciesThermoPolynomial(
        "B", 28.0, 1000.0, 3000.0, (3.5, 0.0, 0.0, 0.0, 0.0, 0.0)
    )
    with pytest.raises(ValueError, match="same species"):
        PiecewiseSpeciesThermo(low, wrong_name, 1000.0)

    high = SpeciesThermoPolynomial(
        "A", 28.0, 1100.0, 3000.0, (3.5, 0.0, 0.0, 0.0, 0.0, 0.0)
    )
    with pytest.raises(ValueError, match="begin at switch"):
        PiecewiseSpeciesThermo(low, high, 1000.0)


def test_kerosene_branch_remains_explicitly_blocked_and_solver_not_promoted() -> None:
    record = load_source_record()
    readiness = build_readiness()

    assert record["teacher_fuel_branch_coverage"]["C10H22"].startswith("BLOCKED")
    assert readiness["core_species_database_ready"] is True
    assert readiness["supported_thermo_fuel_branches"] == ["H2", "C2H4"]
    assert readiness["kerosene_C10H22_thermo_ready"] is False
    assert readiness["solver_integration_ready"] is False
