import json
from pathlib import Path


RECORD = Path("cases/studies/data/p12_thermal_throat_grid_sensitivity_acceptance.json")


def test_grid_sensitivity_acceptance_preserves_scientific_boundaries():
    data = json.loads(RECORD.read_text(encoding="utf-8"))

    assert data["classification"] == "P12_PROJECT_DEFINED_THERMAL_THROAT_GRID_SENSITIVITY_ACCEPTANCE"
    assert data["not_a_source_reproduction"] is True
    assert data["grid_levels"] == [20, 40, 80]
    assert data["teacher_steady_tolerance"] == 2e-5

    acceptance = data["acceptance"]
    assert acceptance["all_grid_jobs_completed"] is True
    assert acceptance["all_converged_points_meet_teacher_eq_11_46_gate"] is True
    assert acceptance["all_converged_points_meet_existing_mass_inventory_0.5_percent_gate"] is True
    assert acceptance["momentum_and_energy_inventory_are_diagnostics_only"] is True
    assert acceptance["transition_equivalence_ratio_bracketed"] is False
    assert acceptance["formal_grid_independence_claimed"] is False

    phi024 = data["target_points"]["phi_0.24"]
    assert [p["cells"] for p in phi024] == [20, 40, 80]
    assert all(p["state"] == "SCRAM_SIDE" for p in phi024)
    assert all(p["density_change"] <= data["teacher_steady_tolerance"] for p in phi024)
    assert all(p["mass_inventory_relative_to_inlet"] <= 5e-3 for p in phi024)

    phi026 = data["target_points"]["phi_0.26"]
    assert [p["cells"] for p in phi026] == [20, 40, 80]
    assert all(p["status"] == "FORWARD_FLOW_GUARD_TRIGGERED" for p in phi026)
    assert all(p["state"] is None for p in phi026)
