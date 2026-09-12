"""Lightweight scientific and aggregation gates for P10.3."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest


SCRIPT = Path(__file__).parents[1] / "cases" / "verification" / "p10_3_cfl_temporal_scheme_sensitivity.py"
SPEC = importlib.util.spec_from_file_location("p10_3_sensitivity", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _record(cfl: float, difference: float = 0.001) -> dict:
    value = 1.0 if cfl == 0.2 else 1.0 + difference
    return {
        "branch": "subsonic", "scheme": "rusanov", "CFL": cfl, "N": 80, "dx": 0.0125,
        "steps": 100, "pseudo_time": 0.05, "initial_residual": 0.04, "final_residual": 9.9e-9,
        "termination_reason": "converged", "converged": True, "physical": True, "branch_preserved": True,
        "state": {"min_rho": 1.0, "min_p": 1.0, "min_T": 1.0, "min_Mach": 0.2, "max_Mach": 0.8},
        "analytical_errors": {variable: {"relative_l1": 0.1, "relative_linf": 0.1} for variable in MODULE.VARIABLES},
        "numerical_fields": {variable: [value, value] for variable in MODULE.VARIABLES},
    }


def _records() -> dict:
    return {MODULE.cfl_key(cfl): _record(cfl) for cfl in MODULE.CFLS}


def test_existing_ssp_rk3_exhibits_third_order_on_independent_ode() -> None:
    result = MODULE.run_rk3_temporal_verification()
    assert [row["steps"] for row in result["records"]] == [10, 20, 40, 80]
    assert all(row["final_time"] == 1.0 for row in result["records"])
    assert result["rk3_errors_monotone"] is True
    assert result["rk3_all_orders_gt_2_5"] is True
    assert result["rk3_final_order_ge_2_8"] is True
    assert result["rk3_passed"] is True
    assert result["orders"] == pytest.approx([3.0578255193509354, 3.0288865949946873, 3.014435458873415])


def test_reduced_real_steady_path_records_reference_boundary_solver_and_metrics() -> None:
    record = MODULE.run_single_steady(8, "subsonic", "rusanov", 0.2, max_time=1e-6, max_steps=2, require_convergence=False)
    assert record["steps"] > 0 and record["initial_residual"] > 0.0
    assert set(record["analytical_errors"]) == set(MODULE.VARIABLES)
    assert set(record["numerical_fields"]) == set(MODULE.VARIABLES)
    assert record["N"] == 8 and record["CFL"] == 0.2


def test_complete_synthetic_cfl_group_passes_with_invariance_metrics() -> None:
    assessment = MODULE.assess_cfl_group(_records(), {variable: 1.0 for variable in MODULE.VARIABLES})
    assert assessment["passed"] is True
    assert all(assessment["gates"].values())
    assert assessment["sensitivity"]["0.1"]["rho"]["l1_ratio"] == pytest.approx(0.01)
    assert assessment["pairwise_0.1_to_0.4"]["rho"]["relative_l1"] == 0.0


@pytest.mark.parametrize("failure", ("missing_cfl", "missing_variable", "unconverged", "max_time", "rho", "pressure", "branch", "mach_range", "nan", "l1_ratio", "linf_ratio"))
def test_cfl_group_rejects_each_required_failure(failure: str) -> None:
    records = _records()
    if failure == "missing_cfl": records.pop("0.4")
    elif failure == "missing_variable": records["0.1"]["numerical_fields"].pop("Mach")
    elif failure == "unconverged": records["0.1"]["converged"] = False
    elif failure == "max_time": records["0.1"]["termination_reason"] = "max-time"
    elif failure == "rho": records["0.1"]["state"]["min_rho"] = -1.0
    elif failure == "pressure": records["0.1"]["state"]["min_p"] = -1.0
    elif failure == "branch": records["0.1"]["branch_preserved"] = False
    elif failure == "mach_range": records["0.1"]["state"]["max_Mach"] = 1.1
    elif failure == "nan": records["0.1"]["numerical_fields"]["rho"][0] = float("nan")
    elif failure == "l1_ratio": records["0.1"]["numerical_fields"]["rho"] = [1.003, 1.003]
    else: records["0.1"]["numerical_fields"]["rho"] = [1.006, 1.0]
    assert MODULE.assess_cfl_group(records, {variable: 1.0 for variable in MODULE.VARIABLES})["passed"] is False


def test_rk3_assessment_rejects_nonmonotone_low_and_low_final_order() -> None:
    good = [1.0e-3, 1.2e-4, 1.4e-5, 1.7e-6]
    assert MODULE.assess_rk3_errors(good)["rk3_passed"] is True
    assert MODULE.assess_rk3_errors([1e-3, 1.2e-4, 1.3e-4, 1e-5])["rk3_passed"] is False
    assert MODULE.assess_rk3_errors([1e-3, 2e-4, 4e-5, 8e-6])["rk3_passed"] is False
    assert MODULE.assess_rk3_errors([1e-3, 1e-4, 1e-5, 1.5e-6])["rk3_passed"] is False
