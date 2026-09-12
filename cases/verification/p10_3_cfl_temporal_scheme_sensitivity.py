"""Generate exact-SHA P10.3 CFL, RK3 temporal, and scheme evidence."""

from __future__ import annotations

import csv
import json
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Mapping

import matplotlib
import numpy as np

matplotlib.use("Agg")
from matplotlib import pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from cases.verification.p10_2_grid_convergence import (
    GAS,
    VARIABLES,
    build_boundary,
    build_geometry,
    build_reference,
    build_reference_scales,
    compute_error_metrics,
)
from scramjet1d.config import NumericalConfig
from scramjet1d.solver import solve_quasi_1d_steady
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative
from scramjet1d.time_integration import ssp_rk3_step
from scramjet1d.verification import observed_order, relative_l1_error, relative_linf_error


BASELINE_SHA = "ce27e3fd841362432791f45f3c8ad53a3002ecf4"
FORMAL_GRID = 80
BRANCHES = ("subsonic", "supersonic")
SCHEMES = ("rusanov", "steger-warming")
CFLS = (0.1, 0.2, 0.4)
BASELINE_CFL = 0.2
STEADY_TOLERANCE = 1.0e-8
MAX_TIME = 0.10
MAX_STEPS = 200_000
CFL_L1_RATIO_LIMIT = 0.02
CFL_LINF_RATIO_LIMIT = 0.05
RK3_FINAL_TIME = 1.0
RK3_DTS = (0.1, 0.05, 0.025, 0.0125)
RK3_ALL_ORDER_GATE = 2.5
RK3_FINAL_ORDER_GATE = 2.8


def resolve_head_sha(explicit: str | None = None) -> str:
    """Resolve explicit, Actions, or local Git exact-SHA provenance."""
    head = explicit or os.environ.get("GITHUB_SHA")
    if head is None:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if re.fullmatch(r"[0-9a-fA-F]{40}", head) is None:
        raise ValueError("head SHA must contain exactly 40 hexadecimal characters")
    return head.lower()


def cfl_key(cfl: float) -> str:
    """Return the canonical JSON key for a formal CFL value."""
    return f"{float(cfl):.1f}"


def _finite_number(value: object, *, positive: bool = False, nonnegative: bool = False) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    if not np.isfinite(number):
        return False
    return number > 0.0 if positive else (number >= 0.0 if nonnegative else True)


def run_single_steady(
    num_cells: int,
    branch: str,
    scheme: str,
    cfl: float,
    *,
    max_time: float = MAX_TIME,
    max_steps: int = MAX_STEPS,
    require_convergence: bool = False,
) -> dict:
    """Run one real physical-boundary steady case and retain comparison fields."""
    if branch not in BRANCHES or scheme not in SCHEMES or float(cfl) not in CFLS:
        raise ValueError("branch, scheme, and CFL must belong to the formal P10.3 sets")
    geometry = build_geometry(num_cells)
    analytical, face = build_reference(num_cells, branch)
    initial = primitive_to_conservative(analytical.rho, analytical.u, analytical.p, GAS)
    started = time.perf_counter()
    result = solve_quasi_1d_steady(
        initial,
        geometry,
        1.0 / num_cells,
        max_time,
        GAS,
        NumericalConfig(cfl=float(cfl), tolerance=STEADY_TOLERANCE),
        max_steps=max_steps,
        flux_scheme=scheme,
        boundary_conditions=build_boundary(face, branch),
    )
    wall_seconds = time.perf_counter() - started
    numerical = conservative_to_primitive(result.U, GAS)
    errors = compute_error_metrics(numerical, analytical, build_reference_scales(branch))
    fields = {variable: np.asarray(getattr(numerical, variable), dtype=float) for variable in VARIABLES}
    finite = bool(all(np.all(np.isfinite(values)) for values in fields.values()))
    positive = bool(np.all(numerical.rho > 0.0) and np.all(numerical.p > 0.0) and np.all(numerical.T > 0.0))
    branch_preserved = bool(np.all((numerical.Mach > 0.0) & (numerical.Mach < 1.0))) if branch == "subsonic" else bool(np.all(numerical.Mach > 1.0))
    record = {
        "branch": branch,
        "scheme": scheme,
        "CFL": float(cfl),
        "N": int(num_cells),
        "dx": float(1.0 / num_cells),
        "steps": int(result.steps),
        "pseudo_time": float(result.time),
        "wall_seconds": float(wall_seconds),
        "initial_residual": float(result.residual_history[0]),
        "final_residual": float(result.residual),
        "termination_reason": result.termination_reason,
        "converged": bool(result.converged),
        "physical": bool(finite and positive),
        "branch_preserved": branch_preserved,
        "state": {
            "min_rho": float(np.min(numerical.rho)),
            "min_p": float(np.min(numerical.p)),
            "min_T": float(np.min(numerical.T)),
            "min_Mach": float(np.min(numerical.Mach)),
            "max_Mach": float(np.max(numerical.Mach)),
        },
        "analytical_errors": {
            variable: {"relative_l1": values["relative_l1"], "relative_linf": values["relative_linf"]}
            for variable, values in errors.items()
        },
        "numerical_fields": {variable: values.tolist() for variable, values in fields.items()},
    }
    if require_convergence and not (result.converged and result.termination_reason == "converged" and result.residual <= STEADY_TOLERANCE):
        raise RuntimeError(f"{branch}/{scheme}/CFL={cfl} failed steady convergence")
    return record


def assess_rk3_errors(errors: list[float] | tuple[float, ...]) -> dict:
    """Apply the independent scalar-ODE temporal convergence gates."""
    finite_positive = len(errors) == len(RK3_DTS) and all(_finite_number(error, positive=True) for error in errors)
    monotone = finite_positive and all(errors[index] > errors[index + 1] for index in range(len(errors) - 1))
    orders = [observed_order(errors[index], errors[index + 1]) for index in range(len(errors) - 1)] if finite_positive else []
    all_orders = len(orders) == 3 and all(order > RK3_ALL_ORDER_GATE for order in orders)
    final_order = len(orders) == 3 and orders[-1] >= RK3_FINAL_ORDER_GATE
    return {
        "orders": orders,
        "rk3_errors_finite_positive": bool(finite_positive),
        "rk3_errors_monotone": bool(monotone),
        "rk3_all_orders_gt_2_5": bool(all_orders),
        "rk3_final_order_ge_2_8": bool(final_order),
        "rk3_passed": bool(finite_positive and monotone and all_orders and final_order),
    }


def run_rk3_temporal_verification() -> dict:
    """Advance y'=-y with the existing SSP-RK3 and compare with exp(-1)."""
    exact = math.exp(-RK3_FINAL_TIME)
    records: list[dict] = []
    errors: list[float] = []
    for dt in RK3_DTS:
        steps = round(RK3_FINAL_TIME / dt)
        if steps * dt != RK3_FINAL_TIME:
            raise RuntimeError("RK3 dt sequence must land exactly on final time")
        state = np.array([1.0])
        for _ in range(steps):
            state = ssp_rk3_step(state, dt, lambda value: -value)
        error = abs(float(state[0]) - exact)
        errors.append(error)
        records.append({"dt": dt, "steps": steps, "final_time": steps * dt, "numerical_y": float(state[0]), "exact_y": exact, "absolute_error": error, "relative_error": error / exact})
    return {"ode": "dy/dt=-y; y(0)=1", "records": records, **assess_rk3_errors(errors)}


def _fields_complete(record: Mapping[str, object]) -> bool:
    fields = record.get("numerical_fields", {})
    errors = record.get("analytical_errors", {})
    if not isinstance(fields, Mapping) or not isinstance(errors, Mapping) or set(fields) != set(VARIABLES) or set(errors) != set(VARIABLES):
        return False
    try:
        arrays = [np.asarray(fields[variable], dtype=float) for variable in VARIABLES]
    except (TypeError, ValueError):
        return False
    if any(array.ndim != 1 or array.size == 0 or not np.all(np.isfinite(array)) for array in arrays):
        return False
    if len({array.shape for array in arrays}) != 1:
        return False
    return all(
        _finite_number(errors[variable].get(norm), positive=True)
        for variable in VARIABLES
        for norm in ("relative_l1", "relative_linf")
    )


def assess_cfl_group(records: Mapping[str, dict], scales: Mapping[str, float]) -> dict:
    """Assess one branch/scheme CFL triplet against its CFL=0.2 steady state."""
    expected_keys = {cfl_key(cfl) for cfl in CFLS}
    exact_cfls = set(records) == expected_keys
    ordered = [records.get(cfl_key(cfl), {}) for cfl in CFLS]
    identity = exact_cfls and all(record.get("CFL") == cfl and record.get("N") == FORMAL_GRID and record.get("dx") == 1.0 / FORMAL_GRID for cfl, record in zip(CFLS, ordered, strict=True))
    fields_complete = exact_cfls and set(scales) == set(VARIABLES) and all(_fields_complete(record) for record in ordered) and all(_finite_number(scales[variable], positive=True) for variable in VARIABLES)
    all_converged = exact_cfls and all(record.get("converged") is True and record.get("termination_reason") == "converged" and _finite_number(record.get("final_residual"), nonnegative=True) and record["final_residual"] <= STEADY_TOLERANCE and isinstance(record.get("steps"), int) and record["steps"] > 0 for record in ordered)
    state_stats = exact_cfls and all(
        _finite_number(record.get("state", {}).get(name), positive=name in ("min_rho", "min_p", "min_T"))
        for record in ordered for name in ("min_rho", "min_p", "min_T", "min_Mach", "max_Mach")
    )
    all_physical = exact_cfls and state_stats and all(record.get("physical") is True for record in ordered)
    branch_ranges = exact_cfls and state_stats and all(
        (
            record.get("branch") == "subsonic"
            and record["state"]["min_Mach"] > 0.0
            and record["state"]["max_Mach"] < 1.0
        )
        or (
            record.get("branch") == "supersonic"
            and record["state"]["min_Mach"] > 1.0
            and record["state"]["max_Mach"] >= record["state"]["min_Mach"]
        )
        for record in ordered
    )
    all_branch_preserved = exact_cfls and branch_ranges and all(record.get("branch_preserved") is True for record in ordered)
    sensitivity: dict[str, dict[str, dict[str, float | bool | None]]] = {}
    pairwise: dict[str, dict[str, float | None]] = {variable: {"relative_l1": None, "relative_linf": None} for variable in VARIABLES}
    metrics_finite = fields_complete
    l1_pass = fields_complete
    linf_pass = fields_complete
    if fields_complete:
        baseline = records[cfl_key(BASELINE_CFL)]
        for cfl in (0.1, 0.4):
            candidate = records[cfl_key(cfl)]
            sensitivity[cfl_key(cfl)] = {}
            for variable in VARIABLES:
                scale = float(scales[variable])
                candidate_values = candidate["numerical_fields"][variable]
                baseline_values = baseline["numerical_fields"][variable]
                difference_l1 = relative_l1_error(candidate_values, baseline_values, scale)
                difference_linf = relative_linf_error(candidate_values, baseline_values, scale)
                spatial_l1 = float(baseline["analytical_errors"][variable]["relative_l1"])
                spatial_linf = float(baseline["analytical_errors"][variable]["relative_linf"])
                ratio_l1 = difference_l1 / spatial_l1
                ratio_linf = difference_linf / spatial_linf
                finite = all(np.isfinite(value) for value in (difference_l1, difference_linf, spatial_l1, spatial_linf, ratio_l1, ratio_linf)) and spatial_l1 > 0.0 and spatial_linf > 0.0
                metrics_finite = metrics_finite and finite
                l1_pass = l1_pass and finite and ratio_l1 <= CFL_L1_RATIO_LIMIT
                linf_pass = linf_pass and finite and ratio_linf <= CFL_LINF_RATIO_LIMIT
                sensitivity[cfl_key(cfl)][variable] = {
                    "relative_l1_difference": difference_l1,
                    "relative_linf_difference": difference_linf,
                    "baseline_spatial_l1_error": spatial_l1,
                    "baseline_spatial_linf_error": spatial_linf,
                    "l1_ratio": ratio_l1,
                    "linf_ratio": ratio_linf,
                    "passed": bool(finite and ratio_l1 <= CFL_L1_RATIO_LIMIT and ratio_linf <= CFL_LINF_RATIO_LIMIT),
                }
        low, high = records["0.1"], records["0.4"]
        for variable in VARIABLES:
            pairwise[variable] = {
                "relative_l1": relative_l1_error(low["numerical_fields"][variable], high["numerical_fields"][variable], scales[variable]),
                "relative_linf": relative_linf_error(low["numerical_fields"][variable], high["numerical_fields"][variable], scales[variable]),
            }
    gates = {
        "exact_cfls": bool(exact_cfls),
        "formal_grid_and_cfl_identity": bool(identity),
        "exact_variables_and_finite_metrics": bool(metrics_finite),
        "all_runs_converged": bool(all_converged),
        "all_states_physical": bool(all_physical),
        "all_branches_preserved": bool(all_branch_preserved),
        "all_cfl_l1_ratios_pass": bool(l1_pass),
        "all_cfl_linf_ratios_pass": bool(linf_pass),
    }
    return {"sensitivity": sensitivity, "pairwise_0.1_to_0.4": pairwise, "gates": gates, "failure_reasons": [name for name, passed in gates.items() if not passed], "passed": all(gates.values())}


def build_scheme_comparison(steady: Mapping[str, object], scales: Mapping[str, Mapping[str, float]]) -> tuple[dict, bool]:
    """Build complete benchmark-specific Rusanov/SW comparisons without ranking gates."""
    comparison: dict[str, dict] = {}
    complete = set(steady) == set(BRANCHES) and set(scales) == set(BRANCHES)
    for branch in BRANCHES:
        comparison[branch] = {}
        branch_data = steady.get(branch, {}) if isinstance(steady, Mapping) else {}
        for cfl in CFLS:
            key = cfl_key(cfl)
            comparison[branch][key] = {}
            try:
                rusanov = branch_data["rusanov"][key]
                sw = branch_data["steger-warming"][key]
                for variable in VARIABLES:
                    r_l1 = float(rusanov["analytical_errors"][variable]["relative_l1"])
                    r_linf = float(rusanov["analytical_errors"][variable]["relative_linf"])
                    sw_l1 = float(sw["analytical_errors"][variable]["relative_l1"])
                    sw_linf = float(sw["analytical_errors"][variable]["relative_linf"])
                    scale = scales[branch][variable]
                    diff_l1 = relative_l1_error(rusanov["numerical_fields"][variable], sw["numerical_fields"][variable], scale)
                    diff_linf = relative_linf_error(rusanov["numerical_fields"][variable], sw["numerical_fields"][variable], scale)
                    values = (r_l1, r_linf, sw_l1, sw_linf, diff_l1, diff_linf)
                    finite = all(_finite_number(value, nonnegative=True) for value in values) and r_l1 > 0.0 and r_linf > 0.0
                    complete = complete and finite
                    comparison[branch][key][variable] = {
                        "rusanov_l1_error": r_l1,
                        "rusanov_linf_error": r_linf,
                        "steger_warming_l1_error": sw_l1,
                        "steger_warming_linf_error": sw_linf,
                        "steger_warming_to_rusanov_l1_ratio": sw_l1 / r_l1,
                        "steger_warming_to_rusanov_linf_ratio": sw_linf / r_linf,
                        "scheme_relative_l1_difference": diff_l1,
                        "scheme_relative_linf_difference": diff_linf,
                        "rusanov_steps": rusanov["steps"],
                        "steger_warming_steps": sw["steps"],
                    }
            except (KeyError, TypeError, ValueError, ZeroDivisionError):
                complete = False
    return comparison, bool(complete)


def assemble_artifact(head_sha: str, steady: Mapping[str, object], rk3: Mapping[str, object], *, scales: Mapping[str, Mapping[str, float]] | None = None) -> dict:
    """Recompute all mandatory gates and assemble the exact-SHA artifact."""
    head = resolve_head_sha(head_sha)
    normalization = dict(scales) if scales is not None else {branch: build_reference_scales(branch) for branch in BRANCHES}
    exact_branches = set(steady) == set(BRANCHES)
    exact_schemes = exact_branches and all(set(steady[branch]) == set(SCHEMES) for branch in BRANCHES)
    record_identity = exact_schemes and all(
        set(steady[branch][scheme]) == {cfl_key(cfl) for cfl in CFLS}
        and all(
            steady[branch][scheme][cfl_key(cfl)].get("branch") == branch
            and steady[branch][scheme][cfl_key(cfl)].get("scheme") == scheme
            and steady[branch][scheme][cfl_key(cfl)].get("CFL") == cfl
            for cfl in CFLS
        )
        for branch in BRANCHES
        for scheme in SCHEMES
    )
    cfl_assessment: dict[str, dict] = {branch: {} for branch in BRANCHES}
    if exact_branches:
        for branch in BRANCHES:
            for scheme in SCHEMES:
                if scheme in steady[branch]:
                    cfl_assessment[branch][scheme] = assess_cfl_group(steady[branch][scheme], normalization[branch])
    all_groups_passed = exact_schemes and all(cfl_assessment[branch].get(scheme, {}).get("passed") is True for branch in BRANCHES for scheme in SCHEMES)
    scheme_comparison, scheme_complete = build_scheme_comparison(steady, normalization)
    try:
        rk3_errors = [float(row["absolute_error"]) for row in rk3["records"]]
    except (KeyError, TypeError, ValueError):
        rk3_errors = []
    rk3_assessment = assess_rk3_errors(rk3_errors)
    rk3_record = dict(rk3)
    rk3_record.update(rk3_assessment)
    gates = {
        "exact_branches": bool(exact_branches),
        "exact_schemes": bool(exact_schemes),
        "record_identity": bool(record_identity),
        "all_steady_groups_passed": bool(all_groups_passed),
        "rk3_temporal_passed": bool(rk3_assessment["rk3_passed"]),
        "scheme_comparison_complete": bool(scheme_complete),
    }
    return {
        "schema_version": 1,
        "stage": "P10.3",
        "artifact_kind": "exact-sha-runtime",
        "baseline_sha": BASELINE_SHA,
        "head_sha": head,
        "formal_grid": FORMAL_GRID,
        "branches": list(BRANCHES),
        "schemes": list(SCHEMES),
        "cfls": list(CFLS),
        "baseline_cfl": BASELINE_CFL,
        "steady_tolerance": STEADY_TOLERANCE,
        "max_time": MAX_TIME,
        "max_steps": MAX_STEPS,
        "variables": list(VARIABLES),
        "cfl_l1_ratio_limit": CFL_L1_RATIO_LIMIT,
        "cfl_linf_ratio_limit": CFL_LINF_RATIO_LIMIT,
        "rk3_ode": "dy/dt=-y; y(0)=1; y(t)=exp(-t)",
        "rk3_final_time": RK3_FINAL_TIME,
        "rk3_dt_sequence": list(RK3_DTS),
        "rk3_order_gate": {"all_orders_gt": RK3_ALL_ORDER_GATE, "final_order_at_least": RK3_FINAL_ORDER_GATE},
        "normalization_scales": normalization,
        "steady_runs": dict(steady),
        "cfl_assessment": cfl_assessment,
        "rk3_temporal": rk3_record,
        "scheme_comparison": scheme_comparison,
        "gates": gates,
        "all_passed": all(gates.values()),
    }


def _failure_record(branch: str, scheme: str, cfl: float, error: Exception) -> dict:
    return {
        "branch": branch, "scheme": scheme, "CFL": cfl, "N": FORMAL_GRID, "dx": 1.0 / FORMAL_GRID,
        "steps": 0, "pseudo_time": 0.0, "wall_seconds": 0.0, "initial_residual": None, "final_residual": None,
        "termination_reason": "exception", "converged": False, "physical": False, "branch_preserved": False,
        "state": {}, "analytical_errors": {}, "numerical_fields": {},
        "exception": {"type": type(error).__name__, "message": str(error)},
    }


def run_p10_3(*, head_sha: str) -> dict:
    """Execute all twelve steady cases plus the independent RK3 study once."""
    steady: dict[str, dict[str, dict[str, dict]]] = {}
    for branch in BRANCHES:
        steady[branch] = {}
        for scheme in SCHEMES:
            steady[branch][scheme] = {}
            for cfl in CFLS:
                try:
                    record = run_single_steady(FORMAL_GRID, branch, scheme, cfl)
                except Exception as error:  # preserve exact failing-case evidence, then continue the formal matrix
                    record = _failure_record(branch, scheme, cfl, error)
                steady[branch][scheme][cfl_key(cfl)] = record
                print(f"{branch} / {scheme} / CFL={cfl} / steps={record['steps']} / residual={record['final_residual']} / {record['termination_reason']}", flush=True)
    return assemble_artifact(head_sha, steady, run_rk3_temporal_verification())


def _cfl_rows(artifact: Mapping[str, object]) -> list[dict]:
    rows = []
    assessment = artifact["cfl_assessment"]
    for branch in BRANCHES:
        for scheme in SCHEMES:
            for key in ("0.1", "0.4"):
                for variable in VARIABLES:
                    metric = assessment[branch][scheme]["sensitivity"].get(key, {}).get(variable, {})
                    rows.append({"branch": branch, "scheme": scheme, "CFL": key, "variable": variable, **metric})
    return rows


def _write_cfl_plot(artifact: Mapping[str, object], path: Path) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    for axis, branch in zip(axes, BRANCHES, strict=True):
        for scheme in SCHEMES:
            for variable in VARIABLES:
                values = [artifact["cfl_assessment"][branch][scheme]["sensitivity"][key][variable]["l1_ratio"] for key in ("0.1", "0.4")]
                axis.semilogy((0.1, 0.4), values, marker="o", label=f"{scheme}: {variable}")
        axis.axhline(CFL_L1_RATIO_LIMIT, color="black", linestyle="--", label="L1 ratio gate")
        axis.set(title=branch, xlabel="pseudo-time CFL", ylabel="steady difference / spatial L1 error")
        axis.grid(True, which="both", alpha=0.3); axis.legend(fontsize=7, ncol=2)
    figure.savefig(path, dpi=160); plt.close(figure)


def _write_rk3_plot(artifact: Mapping[str, object], path: Path) -> None:
    rows = artifact["rk3_temporal"]["records"]
    dts = np.array([row["dt"] for row in rows]); errors = np.array([row["absolute_error"] for row in rows])
    figure, axis = plt.subplots(figsize=(6.5, 5), constrained_layout=True)
    axis.loglog(dts, errors, "o-", label="existing SSP-RK3")
    axis.loglog(dts, errors[0] * (dts / dts[0]) ** 3, "--", label="O(dt^3) reference")
    axis.set(xlabel="dt", ylabel="endpoint absolute error", title="SSP-RK3 on y'=-y")
    axis.grid(True, which="both", alpha=0.3); axis.legend(); axis.invert_xaxis()
    figure.savefig(path, dpi=160); plt.close(figure)


def _write_scheme_plot(artifact: Mapping[str, object], path: Path) -> None:
    labels = [f"{branch}\n{variable}" for branch in BRANCHES for variable in VARIABLES]
    rusanov = [artifact["scheme_comparison"][branch]["0.2"][variable]["rusanov_l1_error"] for branch in BRANCHES for variable in VARIABLES]
    sw = [artifact["scheme_comparison"][branch]["0.2"][variable]["steger_warming_l1_error"] for branch in BRANCHES for variable in VARIABLES]
    x = np.arange(len(labels)); width = 0.4
    figure, axis = plt.subplots(figsize=(12, 5), constrained_layout=True)
    axis.bar(x - width / 2, rusanov, width, label="Rusanov"); axis.bar(x + width / 2, sw, width, label="Steger-Warming")
    axis.set_yscale("log"); axis.set_xticks(x, labels); axis.set(ylabel="analytical relative L1 error", title="N=80, CFL=0.2 benchmark-specific scheme comparison")
    axis.grid(True, axis="y", which="both", alpha=0.3); axis.legend()
    figure.savefig(path, dpi=160); plt.close(figure)


def write_artifacts(artifact: Mapping[str, object], output_dir: Path | str = ROOT / "artifacts" / "p10_3") -> list[Path]:
    """Write strict JSON, two CSV tables, and three explanatory plots."""
    serialized = json.dumps(artifact, indent=2, allow_nan=False) + "\n"
    directory = Path(output_dir); directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "p10_3_sensitivity.json"
    cfl_csv = directory / "p10_3_cfl_results.csv"
    rk3_csv = directory / "p10_3_rk3_temporal.csv"
    cfl_plot = directory / "p10_3_cfl_invariance.png"
    rk3_plot = directory / "p10_3_rk3_temporal_convergence.png"
    scheme_plot = directory / "p10_3_scheme_comparison.png"
    json_path.write_text(serialized, encoding="utf-8")
    cfl_rows = _cfl_rows(artifact)
    cfl_fields = ["branch", "scheme", "CFL", "variable", "relative_l1_difference", "relative_linf_difference", "baseline_spatial_l1_error", "baseline_spatial_linf_error", "l1_ratio", "linf_ratio", "passed"]
    with cfl_csv.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=cfl_fields); writer.writeheader(); writer.writerows(cfl_rows)
    with rk3_csv.open("w", newline="", encoding="utf-8") as stream:
        fields = ["dt", "steps", "final_time", "numerical_y", "exact_y", "absolute_error", "relative_error"]
        writer = csv.DictWriter(stream, fieldnames=fields); writer.writeheader(); writer.writerows(artifact["rk3_temporal"]["records"])
    _write_cfl_plot(artifact, cfl_plot); _write_rk3_plot(artifact, rk3_plot); _write_scheme_plot(artifact, scheme_plot)
    return [json_path, cfl_csv, rk3_csv, cfl_plot, rk3_plot, scheme_plot]


def print_summary(artifact: Mapping[str, object]) -> None:
    """Print concise formal run and hard-gate summaries."""
    for branch in BRANCHES:
        for scheme in SCHEMES:
            for cfl in CFLS:
                record = artifact["steady_runs"][branch][scheme][cfl_key(cfl)]
                print(f"{branch} | {scheme} | {cfl} | {record['steps']} | {record['pseudo_time']} | {record['final_residual']} | {record['termination_reason']}")
    groups = [artifact["cfl_assessment"][branch][scheme] for branch in BRANCHES for scheme in SCHEMES]
    rk3 = artifact["rk3_temporal"]
    print(f"all steady runs converged: {all(group['gates']['all_runs_converged'] for group in groups)}")
    print(f"all physical: {all(group['gates']['all_states_physical'] for group in groups)}")
    print(f"all branch-preserved: {all(group['gates']['all_branches_preserved'] for group in groups)}")
    print(f"all CFL L1 ratios <= 0.02: {all(group['gates']['all_cfl_l1_ratios_pass'] for group in groups)}")
    print(f"all CFL Linf ratios <= 0.05: {all(group['gates']['all_cfl_linf_ratios_pass'] for group in groups)}")
    print(f"RK3 temporal errors monotone: {rk3['rk3_errors_monotone']}")
    print(f"RK3 final order >= 2.8: {rk3['rk3_final_order_ge_2_8']}")
    print(f"scheme comparison complete: {artifact['gates']['scheme_comparison_complete']}")
    print(f"all_passed: {artifact['all_passed']}")


def main() -> None:
    artifact = run_p10_3(head_sha=resolve_head_sha())
    outputs = write_artifacts(artifact)
    print_summary(artifact)
    print("artifacts:", *(str(path.relative_to(ROOT)) for path in outputs), sep="\n  ")
    if artifact["all_passed"] is not True:
        raise SystemExit("P10.3 hard gates failed")


if __name__ == "__main__":
    main()
