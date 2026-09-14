"""Study-layer behavior tests for the P11.1 controlled pilot."""

import copy
import importlib.util
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "cases" / "studies" / "p11_1_parametric_foundation.py"
SPEC = importlib.util.spec_from_file_location("p11_1_foundation", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _result(case_id: str, branch: str, scale: float, *, shift: tuple[str, float] | None = None) -> dict:
    base = {
        "rho": np.array([1.0, 2.0]) * scale,
        "u": np.array([3.0, 4.0]),
        "p": np.array([5.0, 6.0]) * scale,
        "T": np.array([7.0, 8.0]),
        "Mach": np.array([0.4, 0.5]) if branch == "subsonic" else np.array([2.0, 2.1]),
        "mass_flow": np.array([9.0, 10.0]) * scale,
        "U": np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]) * scale,
    }
    if shift:
        base[shift[0]] = base[shift[0]] + shift[1]
    return {
        "case_id": case_id, "branch": branch, "pressure_scale": scale,
        "success": True, "converged": True, "physical": True,
        "framework_branch_preserved": True, "termination_reason": "converged",
        "steps": 10, "pseudo_time": 0.01, "final_residual": 1e-9,
        "physics_input_hash": "a" * 64, "run_configuration_hash": "b" * 64,
        "source_totals": {name: 0.0 for name in MODULE.SOURCE_TOTAL_NAMES},
        "mode_classification_status": "not-defined", "mode_label": None,
        "mode_criterion_id": None, "scientific_claim_level": "framework-only",
        "fields": {name: value.tolist() for name, value in base.items()},
        "metrics": {name: 0.0 for name in MODULE.REQUIRED_METRIC_NAMES},
    }


def test_study_factor_validation_and_formal_manifest_order() -> None:
    factor = MODULE.StudyFactor("stagnation_pressure_scale", 0.8, "1", "framework-control", 1.0)
    assert factor.value == 0.8
    for kwargs in (
        {"value": float("nan")}, {"value": -1.0}, {"category": "physical"},
        {"name": ""}, {"baseline_value": 0.0},
    ):
        values = {"name": "stagnation_pressure_scale", "value": 1.0, "units": "1", "category": "framework-control", "baseline_value": 1.0}
        values.update(kwargs)
        with pytest.raises(ValueError):
            MODULE.StudyFactor(**values)
    manifest = MODULE.build_formal_manifest()
    assert [case.case_id for case in manifest] == list(MODULE.FORMAL_CASE_IDS)
    assert all(case.factor.category == "framework-control" for case in manifest)
    assert all(case.scientific_claim_level == "framework-only" for case in manifest)


def test_manifest_rejects_duplicate_id_and_invalid_pressure_scale() -> None:
    cases = list(MODULE.build_formal_manifest())
    with pytest.raises(ValueError, match="duplicate"):
        MODULE.validate_manifest([cases[0], cases[0]])
    with pytest.raises(ValueError, match="pressure scale"):
        MODULE.make_case("BAD", "subsonic", 0.9)


def test_hashes_are_deterministic_repeat_equal_and_scale_distinct() -> None:
    cases = {case.case_id: case for case in MODULE.build_formal_manifest()}
    a = MODULE.prepare_case(cases["SUB-SW-P100"])
    repeat = MODULE.prepare_case(cases["SUB-SW-P100-REPEAT"])
    scaled = MODULE.prepare_case(cases["SUB-SW-P080"])
    assert a["physics_input_hash"] == repeat["physics_input_hash"]
    assert a["run_configuration_hash"] == repeat["run_configuration_hash"]
    assert a["physics_input_hash"] != scaled["physics_input_hash"]
    assert MODULE.canonical_hash(a["physics_hash_payload"]) == a["physics_input_hash"]


def test_metric_formulas_and_mode_observables_use_exact_sonic_definition() -> None:
    primitive = {"rho": [2.0, 2.0, 2.0], "u": [3.0, 4.0, 5.0], "p": [10.0, 11.0, 12.0], "T": [300.0, 310.0, 320.0], "Mach": [0.5, 1.0, 1.5]}
    metrics, fields = MODULE.calculate_metrics(primitive, np.array([1.0, 1.5, 2.0]), np.array([0.5, 1.5, 2.5]), 1.0, MODULE.zero_source_inputs(3))
    np.testing.assert_array_equal(fields["mass_flow"], [6.0, 12.0, 20.0])
    assert metrics["mass_flow_mean"] == pytest.approx(38.0 / 3.0)
    assert metrics["subsonic_fraction"] == pytest.approx(1 / 3)
    assert metrics["supersonic_fraction"] == pytest.approx(1 / 3)
    assert metrics["sonic_fraction"] == pytest.approx(1 / 3)
    assert metrics["minimum_sonic_margin"] == 0.0
    assert metrics["sonic_crossing_count"] == 0
    assert metrics["x_min_Mach"] == 0.5 and metrics["x_max_Mach"] == 2.5
    expected_p0 = 10.0 * (1.0 + 0.2 * 0.5**2) ** 3.5
    assert fields["local_total_pressure"][0] == pytest.approx(expected_p0)


def test_source_totals_preserve_independent_injection_and_burn_semantics() -> None:
    sources = MODULE.zero_source_inputs(2)
    sources.update({
        "hydraulic_diameter": np.array([2.0, 4.0]), "wall_heat_flux": np.array([10.0, 20.0]),
        "fuel_mass_flow_rate_per_length": np.array([1.0, 2.0]),
        "fuel_burn_rate_per_length": np.array([0.25, 0.5]),
        "fuel_lower_heating_value": np.array([100.0, 200.0]),
    })
    totals = MODULE.calculate_source_totals(sources, np.array([1.0, 2.0]), 0.5)
    assert totals == pytest.approx({"injected_fuel_total": 1.5, "burned_fuel_total": 0.375, "combustion_power": 62.5, "wall_heat_power": 30.0})
    assert "combustion_efficiency" not in totals


def test_similarity_synthetic_pass_and_failures() -> None:
    baseline = _result("SUB-SW-P100", "subsonic", 1.0)
    for scale in (0.8, 1.2):
        result = MODULE.assess_similarity(baseline, _result("scaled", "subsonic", scale))
        assert result["similarity_passed"] is True
        assert result["max_relative_l1"] <= 1e-15
        assert result["max_relative_linf"] <= 1e-15
    for variable in ("Mach", "p", "rho", "mass_flow"):
        result = MODULE.assess_similarity(baseline, _result("bad", "subsonic", 0.8, shift=(variable, 1e-4)))
        assert result["similarity_passed"] is False
    both_norms = MODULE.assess_similarity(baseline, _result("bad", "subsonic", 0.8, shift=("u", 5.0e-6)))
    assert both_norms["max_relative_l1"] > 0.0 and both_norms["max_relative_linf"] > 1e-6


@pytest.mark.parametrize("mutation", ["U", "steps", "final_residual", "pseudo_time", "physics_input_hash", "run_configuration_hash"])
def test_reproducibility_rejects_each_mismatch(mutation: str) -> None:
    original = _result("SUB-SW-P100", "subsonic", 1.0)
    repeat = copy.deepcopy(original); repeat["case_id"] = "SUB-SW-P100-REPEAT"
    assert MODULE.assess_reproducibility(original, repeat)["reproducibility_passed"] is True
    if mutation == "U":
        repeat["fields"]["U"][0][0] += 1.0
    elif mutation in ("steps",):
        repeat[mutation] += 1
    elif mutation in ("final_residual", "pseudo_time"):
        repeat[mutation] += 1e-12
    else:
        repeat[mutation] = "c" * 64
    assert MODULE.assess_reproducibility(original, repeat)["reproducibility_passed"] is False


def test_reduced_real_solver_case_exercises_plumbing_without_convergence_requirement() -> None:
    case = MODULE.make_case("REDUCED", "subsonic", 1.0, num_cells=8, max_steps=2)
    result = MODULE.run_study_case(case, require_convergence=False)
    assert result["case_id"] == "REDUCED"
    assert result["steps"] == 2
    assert result["mode_label"] is None
    assert result["mode_classification_status"] == "not-defined"
    assert set(result["metrics"]) == set(MODULE.REQUIRED_METRIC_NAMES)


def test_metric_registry_has_exact_required_order_and_no_generic_units() -> None:
    definitions = MODULE.metric_definitions()
    assert [row["metric_name"] for row in definitions] == list(MODULE.REQUIRED_METRIC_NAMES)
    assert set(MODULE.METRIC_DEFINITION_REGISTRY) == set(MODULE.REQUIRED_METRIC_NAMES)
    assert all(row["units"] != "SI" for row in definitions)
    assert all(isinstance(row["hard_gate"], bool) and row["hard_gate"] is False for row in definitions)
    assert MODULE.validate_metric_definitions(definitions)["passed"] is True


def test_metric_registry_uses_canonical_dimensions_and_cell_center_semantics() -> None:
    definitions = {row["metric_name"]: row for row in MODULE.metric_definitions()}
    for name in ("x_max_pressure", "x_max_temperature", "x_min_Mach", "x_max_Mach"):
        assert definitions[name]["units"] == "m"
    for name in ("Mach_in", "Mach_out", "Mach_min", "Mach_max", "Mach_mean", "subsonic_fraction", "supersonic_fraction", "sonic_fraction", "minimum_sonic_margin", "mass_flow_relative_span", "exit_to_inlet_pressure_ratio", "max_to_inlet_pressure_ratio", "max_to_inlet_temperature_ratio", "total_pressure_recovery"):
        assert definitions[name]["units"] == "1"
    assert definitions["sonic_crossing_count"]["units"] == "count"
    for name in ("mass_flow_in", "mass_flow_out", "mass_flow_mean", "mass_flow_min", "mass_flow_max"):
        assert definitions[name]["units"] == "kg/s"
    for name in ("p_in", "p_out", "p_min", "p_max", "p0_in", "p0_out", "p0_min", "p0_max"):
        assert definitions[name]["units"] == "Pa"
    for name in ("T_in", "T_out", "T_min", "T_max", "T0_in", "T0_out", "T0_min", "T0_max"):
        assert definitions[name]["units"] == "K"
    assert definitions["rho_min"]["units"] == definitions["rho_max"]["units"] == "kg/m^3"
    assert definitions["u_min"]["units"] == definitions["u_max"]["units"] == "m/s"
    for name in ("p_in", "p_out", "T_in", "T_out", "Mach_in", "Mach_out", "mass_flow_in", "mass_flow_out", "T0_in", "T0_out", "p0_in", "p0_out"):
        assert "cell center" in (definitions[name]["definition"] + definitions[name]["interpretation"]).lower()
    for name in ("subsonic_fraction", "supersonic_fraction", "sonic_fraction", "minimum_sonic_margin", "sonic_crossing_count", "x_min_Mach", "x_max_Mach"):
        assert "not an lbw/ybw classifier" in (definitions[name]["scope"] + definitions[name]["interpretation"]).lower()


def test_metric_registry_freezes_sonic_formula_semantics() -> None:
    definitions = {row["metric_name"]: row for row in MODULE.metric_definitions()}
    assert definitions["minimum_sonic_margin"]["definition"] == "min_i abs(Mach_i - 1)"
    assert definitions["sonic_crossing_count"]["definition"] == "count adjacent pairs satisfying (Mach_i - 1)(Mach_{i+1} - 1) < 0"


def test_metric_registry_freezes_mass_flow_relative_span_formula() -> None:
    definitions = {row["metric_name"]: row for row in MODULE.metric_definitions()}
    assert definitions["mass_flow_relative_span"]["units"] == "1"
    assert definitions["mass_flow_relative_span"]["definition"] == "(max_i mass_flow_i - min_i mass_flow_i) / abs(mean_i mass_flow_i)"
