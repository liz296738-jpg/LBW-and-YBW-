"""Lightweight contracts for the formal P10.2 grid-convergence study."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from scramjet1d.boundary import BoundaryConditions


SCRIPT = Path(__file__).parents[1] / "cases" / "verification" / "p10_2_grid_convergence.py"
SPEC = importlib.util.spec_from_file_location("p10_2_grid_convergence", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _grid_record(error: float) -> dict:
    errors = {
        variable: {
            "relative_l1": error,
            "relative_linf": 1.5 * error,
            "interior_relative_l1": 0.8 * error,
            "interior_relative_linf": error,
        }
        for variable in MODULE.VARIABLES
    }
    return {
        "N": 40,
        "dx": 0.025,
        "steps": 10,
        "pseudo_time": 0.01,
        "final_residual": 1.0e-9,
        "termination_reason": "converged",
        "converged": True,
        "physical": True,
        "branch_preserved": True,
        "state": {"min_rho": 1.0, "min_p": 1.0, "min_T": 1.0, "min_Mach": 0.2, "max_Mach": 0.8},
        "errors": errors,
        "smallest_relative_l1": 0.8 * error,
        "residual_error_ratio": 1.0e-7,
    }


def _passing_grids() -> dict:
    records = {str(n): _grid_record(error) for n, error in zip(MODULE.GRIDS, (0.04, 0.02, 0.01), strict=True)}
    for n, record in zip(MODULE.GRIDS, records.values(), strict=True):
        record["N"] = n
        record["dx"] = 1.0 / n
    return records


def test_formal_configuration_geometry_reference_scales_and_boundaries() -> None:
    assert MODULE.GRIDS == (40, 80, 160)
    assert MODULE.BRANCHES == ("subsonic", "supersonic")
    assert MODULE.SCHEMES == ("rusanov", "steger-warming")
    assert MODULE.VARIABLES == ("rho", "u", "p", "T", "Mach")
    assert MODULE.CONFIG == {
        "stagnation_pressure": 300_000.0,
        "stagnation_temperature": 500.0,
        "domain_length": 1.0,
        "area_left": 1.0,
        "area_right": 1.2,
        "subsonic_reference_mach": 0.5,
        "supersonic_reference_mach": 2.0,
        "cfl": 0.2,
        "steady_tolerance": 1.0e-8,
        "max_time": 0.10,
        "max_steps": 200_000,
        "dense_reference_points": 2001,
    }

    geometry = MODULE.build_geometry(40)
    np.testing.assert_allclose(geometry.face_area, np.linspace(1.0, 1.2, 41), rtol=0.0, atol=0.0)
    np.testing.assert_allclose(geometry.cell_area, 0.5 * (geometry.face_area[:-1] + geometry.face_area[1:]), rtol=0.0, atol=0.0)

    for branch in MODULE.BRANCHES:
        cell, face = MODULE.build_reference(40, branch)
        scale = MODULE.build_reference_scales(branch)
        assert set(scale) == set(MODULE.VARIABLES)
        assert all(np.isfinite(value) and value > 0.0 for value in scale.values())
        assert scale["p"] == MODULE.CONFIG["stagnation_pressure"]
        assert scale["T"] == MODULE.CONFIG["stagnation_temperature"]
        assert np.all(cell.Mach < 1.0) if branch == "subsonic" else np.all(cell.Mach > 1.0)
        boundary = MODULE.build_boundary(face, branch)
        assert isinstance(boundary, BoundaryConditions)
        if branch == "subsonic":
            assert boundary.inlet == "subsonic-total-inflow" and boundary.outlet == "subsonic-pressure"
            assert boundary.outlet_static_pressure == float(face.p[-1])
        else:
            assert boundary.inlet == "supersonic-inflow" and boundary.outlet == "supersonic-outflow"
            assert boundary.inlet_state is not None
            assert boundary.inlet_state.rho == float(face.rho[0])


def test_synthetic_first_order_aggregation_passes_and_records_orders() -> None:
    assessment = MODULE.assess_scheme(_passing_grids())
    assert assessment["passed"] is True
    assert all(assessment["gates"].values())
    for variable in MODULE.VARIABLES:
        assert assessment["orders"][variable]["l1"] == {"40_to_80": 1.0, "80_to_160": 1.0}
        assert assessment["orders"][variable]["linf"] == {"40_to_80": 1.0, "80_to_160": 1.0}


@pytest.mark.parametrize("failure", ("missing_grid", "missing_variable", "unconverged", "nonmonotone", "low_order", "nan", "state_nan"))
def test_synthetic_aggregation_rejects_every_required_failure(failure: str) -> None:
    grids = _passing_grids()
    if failure == "missing_grid":
        grids.pop("160")
    elif failure == "missing_variable":
        grids["80"]["errors"].pop("Mach")
    elif failure == "unconverged":
        grids["80"].update(converged=False, termination_reason="max-time")
    elif failure == "nonmonotone":
        grids["160"]["errors"]["rho"]["relative_l1"] = 0.03
    elif failure == "low_order":
        grids["160"]["errors"]["rho"]["relative_l1"] = 0.019
    elif failure == "nan":
        grids["160"]["errors"]["rho"]["relative_linf"] = float("nan")
    else:
        grids["160"]["state"]["min_p"] = float("nan")
    assert MODULE.assess_scheme(grids)["passed"] is False


def test_reduced_real_path_connects_reference_boundary_solver_and_metrics() -> None:
    record = MODULE.run_single_grid(
        8,
        "subsonic",
        "rusanov",
        max_time=1.0e-6,
        max_steps=2,
        require_convergence=False,
    )
    assert record["steps"] > 0
    assert np.isfinite(record["initial_residual"]) and record["initial_residual"] > 0.0
    assert record["termination_reason"] in {"converged", "max-time", "max-steps"}
    assert set(record["errors"]) == set(MODULE.VARIABLES)
    assert all(np.isfinite(metric) for values in record["errors"].values() for metric in values.values())
