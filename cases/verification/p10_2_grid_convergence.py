"""Run the formal P10.2 smooth isentropic steady grid-convergence study.

The twelve production-sized steady solves are intentionally kept out of the
standard pytest workflow.  Lightweight tests exercise these builders and the
strict aggregation gates; this module is executed by the dedicated long-run
integration workflow to generate exact-SHA evidence.
"""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Mapping

import matplotlib
import numpy as np

matplotlib.use("Agg")
from matplotlib import pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scramjet1d.boundary import BoundaryConditions, PrimitiveBoundaryState
from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.geometry import AreaProfile
from scramjet1d.isentropic import isentropic_nozzle_reference
from scramjet1d.solver import solve_quasi_1d_steady
from scramjet1d.state import PrimitiveVariables, conservative_to_primitive, primitive_to_conservative
from scramjet1d.verification import observed_order, relative_l1_error, relative_linf_error


BASELINE_SHA = "32eb50cd687da6e23a4cb2269bc31120fbff2b3e"
GRIDS = (40, 80, 160)
BRANCHES = ("subsonic", "supersonic")
SCHEMES = ("rusanov", "steger-warming")
VARIABLES = ("rho", "u", "p", "T", "Mach")
CONFIG = {
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
GAS = GasProperties()


def resolve_head_sha(explicit: str | None = None) -> str:
    """Resolve and validate exact runtime provenance."""
    head = explicit or os.environ.get("GITHUB_SHA")
    if head is None:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if re.fullmatch(r"[0-9a-fA-F]{40}", head) is None:
        raise ValueError("head SHA must contain exactly 40 hexadecimal characters")
    return head.lower()


def _reference_mach(branch: str) -> float:
    if branch not in BRANCHES:
        raise ValueError(f"branch must be one of {BRANCHES}")
    return float(CONFIG[f"{branch}_reference_mach"])


def build_geometry(num_cells: int) -> AreaProfile:
    """Build the same linear continuous area profile on every uniform grid."""
    if isinstance(num_cells, (bool, np.bool_)) or not isinstance(num_cells, (int, np.integer)) or num_cells < 5:
        raise ValueError("num_cells must be an integer of at least five")
    face_area = np.linspace(CONFIG["area_left"], CONFIG["area_right"], int(num_cells) + 1)
    return AreaProfile(0.5 * (face_area[:-1] + face_area[1:]), face_area)


def _reference(area: np.ndarray, branch: str) -> PrimitiveVariables:
    return isentropic_nozzle_reference(
        area,
        reference_area=CONFIG["area_left"],
        reference_mach=_reference_mach(branch),
        stagnation_pressure=CONFIG["stagnation_pressure"],
        stagnation_temperature=CONFIG["stagnation_temperature"],
        gas=GAS,
        branch=branch,
    )


def build_reference(num_cells: int, branch: str) -> tuple[PrimitiveVariables, PrimitiveVariables]:
    """Return independent analytical cell-centre and face references."""
    geometry = build_geometry(num_cells)
    return _reference(geometry.cell_area, branch), _reference(geometry.face_area, branch)


@lru_cache(maxsize=2)
def _dense_reference(branch: str) -> tuple[np.ndarray, PrimitiveVariables]:
    area = np.linspace(CONFIG["area_left"], CONFIG["area_right"], CONFIG["dense_reference_points"])
    reference = _reference(area, branch)
    area.setflags(write=False)
    for field in reference:
        field.setflags(write=False)
    return area, reference


@lru_cache(maxsize=2)
def _reference_scale_items(branch: str) -> tuple[tuple[str, float], ...]:
    _, dense = _dense_reference(branch)
    scales = {
        "rho": float(np.max(np.abs(dense.rho))),
        "u": float(np.max(np.abs(dense.u))),
        "p": float(CONFIG["stagnation_pressure"]),
        "T": float(CONFIG["stagnation_temperature"]),
        "Mach": float(np.max(np.abs(dense.Mach))),
    }
    if set(scales) != set(VARIABLES) or not all(np.isfinite(value) and value > 0.0 for value in scales.values()):
        raise RuntimeError("analytical reference produced invalid normalization scales")
    return tuple(scales.items())


def build_reference_scales(branch: str) -> dict[str, float]:
    """Return fixed branch-specific scales from a 2001-point analytical reference."""
    return dict(_reference_scale_items(branch))


def build_boundary(reference_face: PrimitiveVariables, branch: str) -> BoundaryConditions:
    """Construct the accepted physical boundary pair from analytical face data."""
    _reference_mach(branch)
    if branch == "subsonic":
        return BoundaryConditions(
            inlet="subsonic-total-inflow",
            outlet="subsonic-pressure",
            inlet_total_pressure=CONFIG["stagnation_pressure"],
            inlet_total_temperature=CONFIG["stagnation_temperature"],
            outlet_static_pressure=float(reference_face.p[-1]),
        )
    return BoundaryConditions(
        inlet="supersonic-inflow",
        outlet="supersonic-outflow",
        inlet_state=PrimitiveBoundaryState(
            rho=float(reference_face.rho[0]),
            u=float(reference_face.u[0]),
            p=float(reference_face.p[0]),
        ),
    )


@lru_cache(maxsize=2)
def _reference_sanity_items(branch: str) -> tuple[tuple[str, float | bool], ...]:
    area, reference = _dense_reference(branch)
    fields = [np.asarray(getattr(reference, variable), dtype=float) for variable in VARIABLES]
    mass_flow = reference.rho * reference.u * area
    variation = float((np.max(mass_flow) - np.min(mass_flow)) / abs(np.mean(mass_flow)))
    finite = bool(all(np.all(np.isfinite(field)) for field in fields))
    positive = bool(np.all(reference.rho > 0.0) and np.all(reference.p > 0.0) and np.all(reference.T > 0.0))
    branch_correct = bool(np.all((reference.Mach > 0.0) & (reference.Mach < 1.0))) if branch == "subsonic" else bool(np.all(reference.Mach > 1.0))
    return tuple({
        "finite": finite,
        "positive": positive,
        "branch_correct": branch_correct,
        "mass_flow_relative_variation": variation,
        "mass_flow_constant": bool(np.isfinite(variation) and variation <= 1.0e-12),
        "mach_min": float(np.min(reference.Mach)),
        "mach_max": float(np.max(reference.Mach)),
    }.items())


def reference_sanity(branch: str) -> dict[str, float | bool]:
    """Evaluate branch, positivity, finiteness, and mass-flow consistency."""
    return dict(_reference_sanity_items(branch))


def compute_error_metrics(
    numerical: PrimitiveVariables,
    analytical: PrimitiveVariables,
    scales: Mapping[str, float],
) -> dict[str, dict[str, float]]:
    """Compute full-domain primary and [2:-2] diagnostic relative norms."""
    if set(scales) != set(VARIABLES):
        raise ValueError("scales must contain the exact P10.2 variable set")
    metrics: dict[str, dict[str, float]] = {}
    for variable in VARIABLES:
        computed = np.asarray(getattr(numerical, variable), dtype=float)
        exact = np.asarray(getattr(analytical, variable), dtype=float)
        scale = float(scales[variable])
        metrics[variable] = {
            "relative_l1": relative_l1_error(computed, exact, scale),
            "relative_linf": relative_linf_error(computed, exact, scale),
            "interior_relative_l1": relative_l1_error(computed[2:-2], exact[2:-2], scale),
            "interior_relative_linf": relative_linf_error(computed[2:-2], exact[2:-2], scale),
        }
    return metrics


def run_single_grid(
    num_cells: int,
    branch: str,
    scheme: str,
    *,
    max_time: float | None = None,
    max_steps: int | None = None,
    require_convergence: bool = False,
) -> dict:
    """Run one real steady solve and return all formal metrics and diagnostics."""
    if scheme not in SCHEMES:
        raise ValueError(f"scheme must be one of {SCHEMES}")
    geometry = build_geometry(num_cells)
    analytical, face = build_reference(num_cells, branch)
    boundary = build_boundary(face, branch)
    initial = primitive_to_conservative(analytical.rho, analytical.u, analytical.p, GAS)
    result = solve_quasi_1d_steady(
        initial,
        geometry,
        CONFIG["domain_length"] / num_cells,
        CONFIG["max_time"] if max_time is None else max_time,
        GAS,
        NumericalConfig(cfl=CONFIG["cfl"], tolerance=CONFIG["steady_tolerance"]),
        max_steps=CONFIG["max_steps"] if max_steps is None else max_steps,
        flux_scheme=scheme,
        boundary_conditions=boundary,
    )
    numerical = conservative_to_primitive(result.U, GAS)
    metrics = compute_error_metrics(numerical, analytical, build_reference_scales(branch))
    fields = [np.asarray(getattr(numerical, variable), dtype=float) for variable in VARIABLES]
    finite = bool(all(np.all(np.isfinite(field)) for field in fields))
    positive = bool(np.all(numerical.rho > 0.0) and np.all(numerical.p > 0.0) and np.all(numerical.T > 0.0))
    branch_preserved = bool(np.all((numerical.Mach > 0.0) & (numerical.Mach < 1.0))) if branch == "subsonic" else bool(np.all(numerical.Mach > 1.0))
    smallest_l1 = float(min(values["relative_l1"] for values in metrics.values()))
    record = {
        "N": int(num_cells),
        "dx": float(CONFIG["domain_length"] / num_cells),
        "steps": int(result.steps),
        "pseudo_time": float(result.time),
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
        "errors": metrics,
        "smallest_relative_l1": smallest_l1,
        "residual_error_ratio": float(result.residual / smallest_l1),
    }
    if require_convergence and not (result.converged and result.termination_reason == "converged"):
        raise RuntimeError(
            f"{branch}/{scheme}/N={num_cells} did not converge: "
            f"{result.termination_reason}, residual={result.residual:.6e}"
        )
    return record


def _finite_number(value: object, *, positive: bool = False, nonnegative: bool = False) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    if not np.isfinite(number):
        return False
    return (number > 0.0) if positive else ((number >= 0.0) if nonnegative else True)


def assess_scheme(grids: Mapping[str, dict]) -> dict:
    """Apply every formal per-scheme completeness, physics, and order gate."""
    exact_grids = set(grids) == {str(grid) for grid in GRIDS}
    exact_variables = exact_grids and all(set(grids[str(grid)].get("errors", {})) == set(VARIABLES) for grid in GRIDS)
    records = [grids.get(str(grid), {}) for grid in GRIDS]
    all_converged = exact_grids and all(record.get("converged") is True and record.get("termination_reason") == "converged" for record in records)
    all_steps_positive = exact_grids and all(isinstance(record.get("steps"), int) and not isinstance(record.get("steps"), bool) and record["steps"] > 0 for record in records)
    all_physical = exact_grids and all(record.get("physical") is True for record in records)
    all_branches_preserved = exact_grids and all(record.get("branch_preserved") is True for record in records)
    grid_identity = exact_grids and all(record.get("N") == grid and record.get("dx") == 1.0 / grid for grid, record in zip(GRIDS, records, strict=True))
    finite_state_statistics = exact_grids and all(
        _finite_number(record.get("state", {}).get(name), positive=name in ("min_rho", "min_p", "min_T"))
        for record in records
        for name in ("min_rho", "min_p", "min_T", "min_Mach", "max_Mach")
    )
    finite_run_metrics = exact_grids and all(
        _finite_number(record.get(name), nonnegative=True)
        for record in records
        for name in ("pseudo_time", "final_residual", "smallest_relative_l1", "residual_error_ratio")
    )
    finite_error_metrics = exact_variables and all(
        _finite_number(records[index]["errors"][variable].get(metric), positive=metric in ("relative_l1", "relative_linf"), nonnegative=metric.startswith("interior_"))
        for index in range(len(GRIDS))
        for variable in VARIABLES
        for metric in ("relative_l1", "relative_linf", "interior_relative_l1", "interior_relative_linf")
    )
    orders: dict[str, dict[str, dict[str, float | None]]] = {}
    if exact_variables and finite_error_metrics:
        for variable in VARIABLES:
            l1 = [float(record["errors"][variable]["relative_l1"]) for record in records]
            linf = [float(record["errors"][variable]["relative_linf"]) for record in records]
            orders[variable] = {
                "l1": {"40_to_80": observed_order(l1[0], l1[1]), "80_to_160": observed_order(l1[1], l1[2])},
                "linf": {"40_to_80": observed_order(linf[0], linf[1]), "80_to_160": observed_order(linf[1], linf[2])},
            }
    else:
        for variable in VARIABLES:
            orders[variable] = {"l1": {"40_to_80": None, "80_to_160": None}, "linf": {"40_to_80": None, "80_to_160": None}}

    l1_monotone = finite_error_metrics and all(
        records[0]["errors"][variable]["relative_l1"] > records[1]["errors"][variable]["relative_l1"] > records[2]["errors"][variable]["relative_l1"] > 0.0
        for variable in VARIABLES
    )
    linf_monotone = finite_error_metrics and all(
        records[0]["errors"][variable]["relative_linf"] > records[1]["errors"][variable]["relative_linf"] > records[2]["errors"][variable]["relative_linf"] > 0.0
        for variable in VARIABLES
    )
    final_l1_order = finite_error_metrics and all(orders[variable]["l1"]["80_to_160"] >= 0.75 for variable in VARIABLES)
    final_linf_order = finite_error_metrics and all(orders[variable]["linf"]["80_to_160"] >= 0.5 for variable in VARIABLES)
    coarse_l1_positive = finite_error_metrics and all(orders[variable]["l1"]["40_to_80"] > 0.0 for variable in VARIABLES)
    gates = {
        "exact_grids": bool(exact_grids),
        "grid_identity": bool(grid_identity),
        "exact_variables": bool(exact_variables),
        "all_runs_converged": bool(all_converged),
        "all_steps_positive": bool(all_steps_positive),
        "all_states_physical": bool(all_physical and finite_state_statistics),
        "all_branches_preserved": bool(all_branches_preserved),
        "all_metrics_finite": bool(finite_run_metrics and finite_error_metrics),
        "all_l1_monotone": bool(l1_monotone),
        "all_linf_monotone": bool(linf_monotone),
        "all_coarse_l1_orders_positive": bool(coarse_l1_positive),
        "all_final_l1_orders_at_least_0_75": bool(final_l1_order),
        "all_final_linf_orders_at_least_0_5": bool(final_linf_order),
    }
    warnings: list[str] = []
    if finite_error_metrics:
        if any(orders[variable][norm][pair] > 1.5 for variable in VARIABLES for norm in ("l1", "linf") for pair in ("40_to_80", "80_to_160")):
            warnings.append("observed order > 1.5; inspect cancellation or pre-asymptotic behavior")
        if any(orders[variable]["l1"]["40_to_80"] < 0.5 for variable in VARIABLES):
            warnings.append("coarse pair is pre-asymptotic for at least one L1 variable")
    return {
        "orders": orders,
        "gates": gates,
        "warnings": warnings,
        "failure_reasons": [name for name, passed in gates.items() if not passed],
        "passed": all(gates.values()),
    }


def assemble_artifact(head_sha: str, branches: Mapping[str, Mapping[str, dict]], *, sanity: Mapping[str, dict] | None = None) -> dict:
    """Assemble a strict, exact-set, machine-readable P10.2 artifact."""
    head = resolve_head_sha(head_sha)
    exact_branches = set(branches) == set(BRANCHES)
    exact_schemes = exact_branches and all(set(branches[branch]) == set(SCHEMES) for branch in BRANCHES)
    branch_passed = {
        branch: bool(branch in branches and set(branches[branch]) == set(SCHEMES) and all(branches[branch][scheme].get("passed") is True for scheme in SCHEMES))
        for branch in BRANCHES
    }
    sanity_records = dict(sanity) if sanity is not None else {branch: reference_sanity(branch) for branch in BRANCHES}
    reference_passed = set(sanity_records) == set(BRANCHES) and all(
        record.get("finite") is True and record.get("positive") is True and record.get("branch_correct") is True and record.get("mass_flow_constant") is True
        for record in sanity_records.values()
    )
    all_passed = bool(exact_branches and exact_schemes and reference_passed and all(branch_passed.values()))
    return {
        "schema_version": 1,
        "stage": "P10.2",
        "artifact_kind": "exact-sha-runtime",
        "baseline_sha": BASELINE_SHA,
        "head_sha": head,
        "grids": list(GRIDS),
        "expected_branches": list(BRANCHES),
        "expected_schemes": list(SCHEMES),
        "expected_variables": list(VARIABLES),
        "configuration": dict(CONFIG),
        "normalization_scales": {branch: build_reference_scales(branch) for branch in BRANCHES},
        "reference_sanity": sanity_records,
        "branches": dict(branches),
        "gates": {
            "exact_branches": exact_branches,
            "exact_schemes": exact_schemes,
            "reference_sanity": reference_passed,
            "all_branches_passed": all(branch_passed.values()),
        },
        "all_passed": all_passed,
    }


def run_grid_convergence(*, head_sha: str) -> dict:
    """Execute the full immutable 2 x 2 x 3 formal matrix exactly once."""
    sanity = {branch: reference_sanity(branch) for branch in BRANCHES}
    if not all(record["finite"] and record["positive"] and record["branch_correct"] and record["mass_flow_constant"] for record in sanity.values()):
        raise RuntimeError(f"analytical reference sanity failed: {sanity}")
    branches: dict[str, dict[str, dict]] = {}
    for branch in BRANCHES:
        branches[branch] = {}
        for scheme in SCHEMES:
            grids: dict[str, dict] = {}
            for grid in GRIDS:
                record = run_single_grid(grid, branch, scheme)
                grids[str(grid)] = record
                print(
                    f"{branch} / {scheme} / N={grid} / residual={record['final_residual']:.6e} / "
                    f"steps={record['steps']} / {record['termination_reason']}",
                    flush=True,
                )
            branches[branch][scheme] = {"grids": grids, **assess_scheme(grids)}
    return assemble_artifact(head_sha, branches, sanity=sanity)


def _csv_rows(artifact: Mapping[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    branches = artifact["branches"]
    assert isinstance(branches, Mapping)
    for branch in BRANCHES:
        schemes = branches.get(branch, {})
        for scheme in SCHEMES:
            scheme_record = schemes.get(scheme, {})
            for grid in GRIDS:
                record = scheme_record.get("grids", {}).get(str(grid), {})
                for variable in VARIABLES:
                    metrics = record.get("errors", {}).get(variable, {})
                    rows.append({
                        "branch": branch,
                        "scheme": scheme,
                        "N": grid,
                        "dx": record.get("dx"),
                        "variable": variable,
                        "relative_l1": metrics.get("relative_l1"),
                        "relative_linf": metrics.get("relative_linf"),
                        "interior_relative_l1": metrics.get("interior_relative_l1"),
                        "interior_relative_linf": metrics.get("interior_relative_linf"),
                        "steps": record.get("steps"),
                        "residual": record.get("final_residual"),
                    })
    return rows


def _write_plot(artifact: Mapping[str, object], path: Path, norm: str) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    branches = artifact["branches"]
    assert isinstance(branches, Mapping)
    for axis, branch in zip(axes, BRANCHES, strict=True):
        for scheme in SCHEMES:
            scheme_record = branches.get(branch, {}).get(scheme, {})
            for variable in VARIABLES:
                x_values, y_values = [], []
                for grid in GRIDS:
                    record = scheme_record.get("grids", {}).get(str(grid), {})
                    value = record.get("errors", {}).get(variable, {}).get(norm)
                    dx = record.get("dx")
                    if _finite_number(dx, positive=True) and _finite_number(value, positive=True):
                        x_values.append(float(dx)); y_values.append(float(value))
                if len(x_values) == len(GRIDS):
                    axis.loglog(x_values, y_values, marker="o", label=f"{scheme}: {variable}")
        axis.set_title(branch)
        axis.set_xlabel("dx [m]")
        axis.set_ylabel(f"relative {norm.removeprefix('relative_').upper()} error")
        axis.grid(True, which="both", alpha=0.3)
        axis.legend(fontsize=7, ncol=2)
        axis.invert_xaxis()
    figure.savefig(path, dpi=160)
    plt.close(figure)


def write_artifacts(artifact: Mapping[str, object], output_dir: Path | str = ROOT / "artifacts" / "p10_2") -> list[Path]:
    """Write strict JSON, auxiliary CSV, and explanatory convergence plots."""
    serialized = json.dumps(artifact, indent=2, allow_nan=False) + "\n"
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "p10_2_grid_convergence.json"
    csv_path = directory / "p10_2_grid_errors.csv"
    l1_path = directory / "p10_2_l1_convergence.png"
    linf_path = directory / "p10_2_linf_convergence.png"
    json_path.write_text(serialized, encoding="utf-8")
    fieldnames = ["branch", "scheme", "N", "dx", "variable", "relative_l1", "relative_linf", "interior_relative_l1", "interior_relative_linf", "steps", "residual"]
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(_csv_rows(artifact))
    _write_plot(artifact, l1_path, "relative_l1")
    _write_plot(artifact, linf_path, "relative_linf")
    return [json_path, csv_path, l1_path, linf_path]


def print_summary(artifact: Mapping[str, object]) -> None:
    """Print concise run, order, and top-level gate summaries."""
    branches = artifact["branches"]
    assert isinstance(branches, Mapping)
    for branch in BRANCHES:
        for scheme in SCHEMES:
            block = branches.get(branch, {}).get(scheme, {})
            print(f"\n{branch} / {scheme}")
            for grid in GRIDS:
                record = block.get("grids", {}).get(str(grid), {})
                print(f"N={grid} residual={record.get('final_residual')} steps={record.get('steps')} convergence={record.get('termination_reason')}")
            for variable in VARIABLES:
                errors = [block.get("grids", {}).get(str(grid), {}).get("errors", {}).get(variable, {}).get("relative_l1") for grid in GRIDS]
                order = block.get("orders", {}).get(variable, {}).get("l1", {})
                print(f"{variable} / E40={errors[0]} / E80={errors[1]} / E160={errors[2]} / p40-80={order.get('40_to_80')} / p80-160={order.get('80_to_160')}")
    scheme_blocks = [branches.get(branch, {}).get(scheme, {}) for branch in BRANCHES for scheme in SCHEMES]
    print("\nArtifact summary")
    print(f"expected branches: {len(BRANCHES)}")
    print(f"expected schemes: {len(SCHEMES)}")
    print(f"expected grids: {len(GRIDS)}")
    print(f"all runs converged: {all(block.get('gates', {}).get('all_runs_converged') is True for block in scheme_blocks)}")
    print(f"all L1 monotone: {all(block.get('gates', {}).get('all_l1_monotone') is True for block in scheme_blocks)}")
    print(f"all Linf monotone: {all(block.get('gates', {}).get('all_linf_monotone') is True for block in scheme_blocks)}")
    print(f"all final L1 order >= 0.75: {all(block.get('gates', {}).get('all_final_l1_orders_at_least_0_75') is True for block in scheme_blocks)}")
    print(f"all final Linf order >= 0.5: {all(block.get('gates', {}).get('all_final_linf_orders_at_least_0_5') is True for block in scheme_blocks)}")
    print(f"all_passed: {artifact.get('all_passed')}")


def main() -> None:
    artifact = run_grid_convergence(head_sha=resolve_head_sha())
    outputs = write_artifacts(artifact)
    print_summary(artifact)
    print("artifacts:", *(str(path.relative_to(ROOT)) for path in outputs), sep="\n  ")
    if artifact["all_passed"] is not True:
        raise SystemExit("P10.2 hard gates failed")


if __name__ == "__main__":
    main()
