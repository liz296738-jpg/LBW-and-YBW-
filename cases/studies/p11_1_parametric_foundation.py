"""Run the P11.1 controlled pressure-similarity framework pilot."""

import argparse
import csv
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, replace
from pathlib import Path

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
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative


BASELINE_SHA = "cac804a30f325ddf1875ab5188353cdbbf9e5de6"
P10_CLOSURE_EVIDENCE = {
    "accepted_sha": BASELINE_SHA,
    "standard_ci_run": 34832765660,
    "p10_4_dedicated_run": 34833172796,
    "artifact_id": 10343052217,
    "artifact_sha256": "4e930fc5747822281c382d53919161f3f2c35d0f12fcfcb56bf16fa9b8684f9e",
}
FORMAL_CASE_IDS = (
    "SUB-SW-P080", "SUB-SW-P100", "SUB-SW-P120", "SUB-SW-P100-REPEAT",
    "SUP-SW-P080", "SUP-SW-P100", "SUP-SW-P120",
)
BRANCHES = ("subsonic", "supersonic")
PRESSURE_SCALES = (0.8, 1.0, 1.2)
FACTOR_CATEGORIES = ("framework-control", "physical-input", "numerical-control")
SIMILARITY_VARIABLES = ("rho_scaled", "p_scaled", "mass_flow_scaled", "u", "T", "Mach")
SIMILARITY_TOLERANCE = 1.0e-6
SOURCE_TOTAL_NAMES = ("injected_fuel_total", "burned_fuel_total", "combustion_power", "wall_heat_power")
GAS = GasProperties()
REQUIRED_METRIC_NAMES = (
    "rho_min", "rho_max", "u_min", "u_max", "p_in", "p_out", "p_min", "p_max",
    "exit_to_inlet_pressure_ratio", "max_to_inlet_pressure_ratio", "x_max_pressure",
    "T_in", "T_out", "T_min", "T_max", "max_to_inlet_temperature_ratio", "x_max_temperature",
    "Mach_in", "Mach_out", "Mach_min", "Mach_max", "Mach_mean",
    "subsonic_fraction", "supersonic_fraction", "sonic_fraction", "minimum_sonic_margin",
    "sonic_crossing_count", "x_min_Mach", "x_max_Mach",
    "mass_flow_in", "mass_flow_out", "mass_flow_mean", "mass_flow_min", "mass_flow_max",
    "mass_flow_relative_span", "T0_in", "T0_out", "T0_min", "T0_max",
    "p0_in", "p0_out", "p0_min", "p0_max", "total_pressure_recovery",
)
CASE_RESULT_FIELDS = (
    "case_id", "branch", "pressure_scale", "P0", "T0", "scheme", "N", "CFL", "tolerance",
    "success", "converged", "termination_reason", "steps", "pseudo_time", "final_residual",
    "physical", "framework_branch_preserved", "physics_input_hash", "run_configuration_hash",
    *REQUIRED_METRIC_NAMES, *SOURCE_TOTAL_NAMES,
    "mode_classification_status", "mode_label", "failure_status", "failure_type", "failure_message",
)
METRIC_DEFINITION_FIELDS = ("metric_name", "symbol", "units", "definition", "interpretation", "hard_gate", "scope")
REQUIRED_ARTIFACT_NAMES = (
    "p11_1_foundation.json", "p11_1_case_manifest.json", "p11_1_case_results.csv",
    "p11_1_metric_definitions.csv", "p11_1_fields.npz", "p11_1_summary.md",
    "p11_1_mach_similarity.png", "p11_1_pressure_similarity.png", "p11_1_density_similarity.png",
)
SCIENTIFIC_LIMITATIONS = (
    "framework pilot only", "not a calibrated engine case", "no LBW/YBW criterion yet",
    "no real fuel sweep", "no real heat-release sweep", "no experimental comparison",
    "quasi-1D", "perfect gas", "prescribed source models", "no finite-rate chemistry",
    "no species transport",
)


@dataclass(frozen=True)
class StudyFactor:
    name: str
    value: float
    units: str
    category: str
    baseline_value: float

    def __post_init__(self):
        if not self.name or not self.units:
            raise ValueError("factor name and units must be nonempty")
        if self.category not in FACTOR_CATEGORIES:
            raise ValueError(f"factor category must be one of {FACTOR_CATEGORIES}")
        if not math.isfinite(float(self.value)) or float(self.value) <= 0.0:
            raise ValueError("factor value must be finite and positive")
        if not math.isfinite(float(self.baseline_value)) or float(self.baseline_value) <= 0.0:
            raise ValueError("factor baseline_value must be finite and positive")


@dataclass(frozen=True)
class StudyCase:
    case_id: str
    family: str
    purpose: str
    branch: str
    factor: StudyFactor
    flux_scheme: str = "steger-warming"
    num_cells: int = 80
    domain_length: float = 1.0
    cfl: float = 0.2
    steady_tolerance: float = 1.0e-8
    max_time: float = 0.10
    max_steps: int = 200_000
    scientific_claim_level: str = "framework-only"

    def __post_init__(self):
        if not self.case_id:
            raise ValueError("case_id must be nonempty")
        if self.branch not in BRANCHES:
            raise ValueError(f"branch must be one of {BRANCHES}")
        if self.factor.name != "stagnation_pressure_scale" or self.factor.value not in PRESSURE_SCALES:
            raise ValueError("pressure scale must be one of 0.8, 1.0, 1.2")
        if self.flux_scheme != "steger-warming" or self.scientific_claim_level != "framework-only":
            raise ValueError("P11.1 formal cases use Steger-Warming at framework-only claim level")
        if self.num_cells < 2 or self.max_steps <= 0:
            raise ValueError("num_cells and max_steps must be positive")


def make_case(case_id, branch, pressure_scale, **overrides):
    prefix = "SUB" if branch == "subsonic" else "SUP"
    factor = StudyFactor("stagnation_pressure_scale", pressure_scale, "1", "framework-control", 1.0)
    return StudyCase(case_id, f"{prefix}-smooth-isentropic", "controlled pressure-similarity framework verification", branch, factor, **overrides)


def build_formal_manifest():
    cases = (
        make_case("SUB-SW-P080", "subsonic", 0.8),
        make_case("SUB-SW-P100", "subsonic", 1.0),
        make_case("SUB-SW-P120", "subsonic", 1.2),
        make_case("SUB-SW-P100-REPEAT", "subsonic", 1.0),
        make_case("SUP-SW-P080", "supersonic", 0.8),
        make_case("SUP-SW-P100", "supersonic", 1.0),
        make_case("SUP-SW-P120", "supersonic", 1.2),
    )
    validate_manifest(cases)
    return cases


def validate_manifest(cases):
    ids = [case.case_id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case_id in study manifest")
    return tuple(cases)


def resolve_head_sha(explicit=None):
    head = explicit or os.environ.get("GITHUB_SHA")
    if head is None:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if re.fullmatch(r"[0-9a-fA-F]{40}", head) is None:
        raise ValueError("head SHA must contain exactly 40 hexadecimal characters")
    return head.lower()


def p10_is_ancestor(head="HEAD"):
    return subprocess.run(["git", "merge-base", "--is-ancestor", BASELINE_SHA, head], cwd=ROOT, check=False).returncode == 0


def production_files_changed(head="HEAD"):
    output = subprocess.check_output(["git", "diff", "--name-only", BASELINE_SHA, head, "--", "src/scramjet1d/"], cwd=ROOT, text=True)
    return [line for line in output.splitlines() if line]


def _hash_update(hasher, value):
    if isinstance(value, np.ndarray):
        array = np.ascontiguousarray(value)
        header = json.dumps({"dtype": array.dtype.str, "shape": array.shape}, sort_keys=True, separators=(",", ":"), allow_nan=False)
        hasher.update(b"array:"); hasher.update(header.encode()); hasher.update(b":"); hasher.update(array.tobytes())
    elif isinstance(value, dict):
        hasher.update(b"{")
        for key in sorted(value):
            _hash_update(hasher, str(key)); _hash_update(hasher, value[key])
        hasher.update(b"}")
    elif isinstance(value, (list, tuple)):
        hasher.update(b"[")
        for item in value:
            _hash_update(hasher, item)
        hasher.update(b"]")
    elif isinstance(value, np.generic):
        _hash_update(hasher, value.item())
    else:
        hasher.update(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def canonical_hash(value):
    hasher = hashlib.sha256()
    _hash_update(hasher, value)
    return hasher.hexdigest()


def zero_source_inputs(num_cells):
    zeros = np.zeros(int(num_cells), dtype=float)
    return {
        "hydraulic_diameter": None, "darcy_friction_factor": zeros.copy(), "wall_heat_flux": zeros.copy(),
        "fuel_mass_flow_rate_per_length": zeros.copy(), "fuel_axial_velocity": zeros.copy(),
        "fuel_specific_total_enthalpy": zeros.copy(), "fuel_burn_rate_per_length": zeros.copy(),
        "fuel_lower_heating_value": None,
    }


def _broadcast(value, shape, name):
    try:
        array = np.broadcast_to(np.asarray(value, dtype=float), shape)
    except ValueError as error:
        raise ValueError(f"{name} must broadcast to the case grid") from error
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must be finite")
    return array


def calculate_source_totals(sources, area, dx):
    area = np.asarray(area, dtype=float)
    shape = area.shape
    injection = _broadcast(sources["fuel_mass_flow_rate_per_length"], shape, "fuel injection")
    burned = _broadcast(sources["fuel_burn_rate_per_length"], shape, "burned fuel")
    lhv_value = sources["fuel_lower_heating_value"]
    lhv = np.zeros(shape) if lhv_value is None else _broadcast(lhv_value, shape, "LHV")
    heat = _broadcast(sources["wall_heat_flux"], shape, "wall heat flux")
    diameter_value = sources["hydraulic_diameter"]
    if diameter_value is None:
        if np.any(heat != 0.0):
            raise ValueError("hydraulic diameter is required for nonzero wall heat flux")
        wall_power = 0.0
    else:
        diameter = _broadcast(diameter_value, shape, "hydraulic diameter")
        if np.any(diameter <= 0.0):
            raise ValueError("hydraulic diameter must be positive")
        wall_power = float(np.sum(4.0 * heat / diameter * area * dx))
    return {
        "injected_fuel_total": float(np.sum(injection * dx)),
        "burned_fuel_total": float(np.sum(burned * dx)),
        "combustion_power": float(np.sum(burned * lhv * dx)),
        "wall_heat_power": wall_power,
    }


def _geometry(num_cells):
    face_area = np.linspace(1.0, 1.2, num_cells + 1)
    return AreaProfile(0.5 * (face_area[:-1] + face_area[1:]), face_area)


def _reference(area, branch, pressure_scale):
    return isentropic_nozzle_reference(
        area, reference_area=1.0, reference_mach=0.5 if branch == "subsonic" else 2.0,
        stagnation_pressure=300_000.0 * pressure_scale, stagnation_temperature=500.0,
        gas=GAS, branch=branch,
    )


def prepare_case(case):
    geometry = _geometry(case.num_cells)
    cell_reference = _reference(geometry.cell_area, case.branch, case.factor.value)
    face_reference = _reference(geometry.face_area, case.branch, case.factor.value)
    U0 = primitive_to_conservative(cell_reference.rho, cell_reference.u, cell_reference.p, GAS)
    p0 = 300_000.0 * case.factor.value
    if case.branch == "subsonic":
        boundary = BoundaryConditions(inlet="subsonic-total-inflow", outlet="subsonic-pressure", inlet_total_pressure=p0, inlet_total_temperature=500.0, outlet_static_pressure=float(face_reference.p[-1]))
    else:
        boundary = BoundaryConditions(inlet="supersonic-inflow", outlet="supersonic-outflow", inlet_state=PrimitiveBoundaryState(float(face_reference.rho[0]), float(face_reference.u[0]), float(face_reference.p[0])))
    sources = zero_source_inputs(case.num_cells)
    boundary_payload = asdict(boundary)
    physics_payload = {
        "branch": case.branch, "pressure_scale": case.factor.value, "P0": p0, "T0": 500.0,
        "gas": asdict(GAS), "geometry": {"cell_area": geometry.cell_area, "face_area": geometry.face_area},
        "initial_primitive": {name: np.asarray(getattr(cell_reference, name)) for name in ("rho", "u", "p", "T", "Mach")},
        "initial_conservative": U0, "boundary": boundary_payload, "sources": sources,
    }
    physics_hash = canonical_hash(physics_payload)
    run_payload = {
        "physics_input_hash": physics_hash, "N": case.num_cells, "CFL": case.cfl,
        "tolerance": case.steady_tolerance, "max_time": case.max_time,
        "max_steps": case.max_steps, "flux_scheme": case.flux_scheme,
    }
    return {
        "geometry": geometry, "reference": cell_reference, "U0": U0, "boundary": boundary,
        "sources": sources, "P0": p0, "T0": 500.0, "physics_hash_payload": physics_payload,
        "physics_input_hash": physics_hash, "run_configuration_hash": canonical_hash(run_payload),
    }


def calculate_metrics(primitive, area, x, dx, sources):
    arrays = {name: np.asarray(primitive[name], dtype=float) for name in ("rho", "u", "p", "T", "Mach")}
    area = np.asarray(area, dtype=float); x = np.asarray(x, dtype=float)
    if any(values.shape != area.shape for values in arrays.values()) or x.shape != area.shape:
        raise ValueError("primitive, area, and x arrays must share one shape")
    mass_flow = arrays["rho"] * arrays["u"] * area
    factor = 1.0 + 0.5 * (GAS.gamma - 1.0) * arrays["Mach"] ** 2
    local_t0 = arrays["T"] * factor
    local_p0 = arrays["p"] * factor ** (GAS.gamma / (GAS.gamma - 1.0))
    mean_flow = float(np.mean(mass_flow))
    metrics = {
        "rho_min": float(np.min(arrays["rho"])), "rho_max": float(np.max(arrays["rho"])),
        "u_min": float(np.min(arrays["u"])), "u_max": float(np.max(arrays["u"])),
        "p_in": float(arrays["p"][0]), "p_out": float(arrays["p"][-1]), "p_min": float(np.min(arrays["p"])), "p_max": float(np.max(arrays["p"])),
        "exit_to_inlet_pressure_ratio": float(arrays["p"][-1] / arrays["p"][0]), "max_to_inlet_pressure_ratio": float(np.max(arrays["p"]) / arrays["p"][0]), "x_max_pressure": float(x[np.argmax(arrays["p"])]),
        "T_in": float(arrays["T"][0]), "T_out": float(arrays["T"][-1]), "T_min": float(np.min(arrays["T"])), "T_max": float(np.max(arrays["T"])),
        "max_to_inlet_temperature_ratio": float(np.max(arrays["T"]) / arrays["T"][0]), "x_max_temperature": float(x[np.argmax(arrays["T"])]),
        "Mach_in": float(arrays["Mach"][0]), "Mach_out": float(arrays["Mach"][-1]), "Mach_min": float(np.min(arrays["Mach"])), "Mach_max": float(np.max(arrays["Mach"])), "Mach_mean": float(np.mean(arrays["Mach"])),
        "subsonic_fraction": float(np.count_nonzero(arrays["Mach"] < 1.0) / arrays["Mach"].size), "supersonic_fraction": float(np.count_nonzero(arrays["Mach"] > 1.0) / arrays["Mach"].size), "sonic_fraction": float(np.count_nonzero(arrays["Mach"] == 1.0) / arrays["Mach"].size),
        "minimum_sonic_margin": float(np.min(np.abs(arrays["Mach"] - 1.0))), "sonic_crossing_count": int(np.count_nonzero((arrays["Mach"][:-1] - 1.0) * (arrays["Mach"][1:] - 1.0) < 0.0)),
        "x_min_Mach": float(x[np.argmin(arrays["Mach"])]), "x_max_Mach": float(x[np.argmax(arrays["Mach"])]),
        "mass_flow_in": float(mass_flow[0]), "mass_flow_out": float(mass_flow[-1]), "mass_flow_mean": mean_flow,
        "mass_flow_min": float(np.min(mass_flow)), "mass_flow_max": float(np.max(mass_flow)), "mass_flow_relative_span": float((np.max(mass_flow) - np.min(mass_flow)) / abs(mean_flow)),
        "T0_in": float(local_t0[0]), "T0_out": float(local_t0[-1]), "T0_min": float(np.min(local_t0)), "T0_max": float(np.max(local_t0)),
        "p0_in": float(local_p0[0]), "p0_out": float(local_p0[-1]), "p0_min": float(np.min(local_p0)), "p0_max": float(np.max(local_p0)), "total_pressure_recovery": float(local_p0[-1] / local_p0[0]),
    }
    totals = calculate_source_totals(sources, area, dx)
    fields = {**arrays, "mass_flow": mass_flow, "local_total_pressure": local_p0, "local_total_temperature": local_t0}
    return metrics, fields | {"source_totals": totals}


def _failure_result(case, prepared, started, error):
    message = str(error)
    status = "boundary-inapplicable" if "boundary" in message.lower() else "solver-error"
    return {
        "case_id": case.case_id, "branch": case.branch, "pressure_scale": case.factor.value,
        "P0": prepared.get("P0"), "T0": prepared.get("T0"), "scheme": case.flux_scheme,
        "N": case.num_cells, "CFL": case.cfl, "tolerance": case.steady_tolerance,
        "success": False, "converged": False, "termination_reason": status, "steps": 0,
        "pseudo_time": 0.0, "final_residual": None, "physical": False,
        "framework_branch_preserved": False, "physics_input_hash": prepared.get("physics_input_hash"),
        "run_configuration_hash": prepared.get("run_configuration_hash"), "source_totals": {},
        "mode_classification_status": "not-defined", "mode_label": None, "mode_criterion_id": None,
        "scientific_claim_level": "framework-only", "metrics": {}, "fields": {},
        "failure": {"status": status, "type": type(error).__name__, "message": message},
        "wall_clock_seconds": time.perf_counter() - started,
    }


def run_study_case(case, require_convergence=True):
    started = time.perf_counter(); prepared = {}
    try:
        prepared = prepare_case(case)
        geometry = prepared["geometry"]; sources = prepared["sources"]
        result = solve_quasi_1d_steady(
            prepared["U0"], geometry, case.domain_length / case.num_cells, case.max_time,
            GAS, NumericalConfig(cfl=case.cfl, tolerance=case.steady_tolerance), max_steps=case.max_steps,
            flux_scheme=case.flux_scheme, boundary_conditions=prepared["boundary"], **sources,
        )
        primitive = conservative_to_primitive(result.U, GAS)
        values = {name: np.asarray(getattr(primitive, name), dtype=float) for name in ("rho", "u", "p", "T", "Mach")}
        physical = bool(all(np.all(np.isfinite(value)) for value in values.values()) and np.all(values["rho"] > 0.0) and np.all(values["p"] > 0.0) and np.all(values["T"] > 0.0) and np.all(values["u"] > 0.0))
        branch_ok = bool(np.all((values["Mach"] > 0.0) & (values["Mach"] < 1.0))) if case.branch == "subsonic" else bool(np.all(values["Mach"] > 1.0))
        dx = case.domain_length / case.num_cells; x = (np.arange(case.num_cells) + 0.5) * dx
        metrics, derived = calculate_metrics(values, geometry.cell_area, x, dx, sources)
        source_totals = derived.pop("source_totals")
        converged = bool(result.converged and result.termination_reason == "converged" and result.residual <= case.steady_tolerance)
        if not physical: failure_status = "nonphysical"
        elif not branch_ok: failure_status = "framework-branch-violation"
        elif not converged: failure_status = result.termination_reason
        else: failure_status = None
        success = bool(converged and physical and branch_ok)
        record = {
            "case_id": case.case_id, "branch": case.branch, "pressure_scale": case.factor.value,
            "P0": prepared["P0"], "T0": prepared["T0"], "scheme": case.flux_scheme,
            "N": case.num_cells, "CFL": case.cfl, "tolerance": case.steady_tolerance,
            "success": success, "converged": converged, "termination_reason": result.termination_reason,
            "steps": int(result.steps), "pseudo_time": float(result.time), "final_residual": float(result.residual),
            "physical": physical, "framework_branch_preserved": branch_ok,
            "physics_input_hash": prepared["physics_input_hash"], "run_configuration_hash": prepared["run_configuration_hash"],
            "source_totals": source_totals, "mode_classification_status": "not-defined",
            "mode_label": None, "mode_criterion_id": None, "scientific_claim_level": "framework-only",
            "metrics": metrics, "fields": {"x": x.tolist(), "area": geometry.cell_area.tolist(), "U": np.asarray(result.U).tolist(), **{name: np.asarray(value).tolist() for name, value in values.items()}, **{name: np.asarray(value).tolist() for name, value in derived.items()}},
            "failure": None if success else {"status": failure_status, "type": None, "message": f"case ended with {failure_status}"},
            "wall_clock_seconds": time.perf_counter() - started,
        }
        if require_convergence and not success:
            return record
        return record
    except Exception as error:
        return _failure_result(case, prepared, started, error)


def _relative_errors(candidate, baseline):
    baseline = np.asarray(baseline, dtype=float); candidate = np.asarray(candidate, dtype=float)
    scale = float(np.max(np.abs(baseline)))
    if not np.isfinite(scale) or scale <= 0.0:
        raise ValueError("similarity normalization must be finite and positive")
    difference = np.abs(candidate - baseline)
    return float(np.mean(difference) / scale), float(np.max(difference) / scale)


def assess_similarity(baseline, scaled):
    scale = float(scaled["pressure_scale"])
    transforms = {
        "rho_scaled": (np.asarray(scaled["fields"]["rho"]) / scale, baseline["fields"]["rho"]),
        "p_scaled": (np.asarray(scaled["fields"]["p"]) / scale, baseline["fields"]["p"]),
        "mass_flow_scaled": (np.asarray(scaled["fields"]["mass_flow"]) / scale, baseline["fields"]["mass_flow"]),
        "u": (scaled["fields"]["u"], baseline["fields"]["u"]),
        "T": (scaled["fields"]["T"], baseline["fields"]["T"]),
        "Mach": (scaled["fields"]["Mach"], baseline["fields"]["Mach"]),
    }
    metrics = []
    for variable in SIMILARITY_VARIABLES:
        l1, linf = _relative_errors(*transforms[variable])
        metrics.append({"variable": variable, "relative_l1": l1, "relative_linf": linf, "passed": bool(np.isfinite(l1) and np.isfinite(linf) and l1 <= SIMILARITY_TOLERANCE and linf <= SIMILARITY_TOLERANCE)})
    return {
        "branch": scaled["branch"], "case_id": scaled["case_id"], "pressure_scale": scale,
        "metrics": metrics, "max_relative_l1": max(row["relative_l1"] for row in metrics),
        "max_relative_linf": max(row["relative_linf"] for row in metrics),
        "similarity_passed": all(row["passed"] for row in metrics),
    }


def assess_reproducibility(original, repeat):
    checks = {
        "state_exact_match": bool(np.array_equal(np.asarray(original["fields"]["U"]), np.asarray(repeat["fields"]["U"]))),
        "steps_exact_match": original["steps"] == repeat["steps"],
        "termination_reason_exact_match": original["termination_reason"] == repeat["termination_reason"],
        "pseudo_time_exact_match": original["pseudo_time"] == repeat["pseudo_time"],
        "residual_exact_match": original["final_residual"] == repeat["final_residual"],
        "input_hash_match": original["physics_input_hash"] == repeat["physics_input_hash"],
        "run_hash_match": original["run_configuration_hash"] == repeat["run_configuration_hash"],
    }
    return {**checks, "reproducibility_passed": all(checks.values())}


def metric_definitions():
    definitions = []
    for name in REQUIRED_METRIC_NAMES:
        scope = "diagnostic only; not an LBW/YBW classifier" if name in ("subsonic_fraction", "supersonic_fraction", "sonic_fraction", "minimum_sonic_margin", "sonic_crossing_count") else "controlled P11.1 framework case"
        definitions.append({"metric_name": name, "symbol": name, "units": "1" if "ratio" in name or "fraction" in name or "Mach" in name or "recovery" in name or "span" in name else "SI", "definition": name.replace("_", " "), "interpretation": "recorded study diagnostic", "hard_gate": "false", "scope": scope})
    return definitions


def parse_pytest_xml(path):
    root = ET.parse(path).getroot()
    if root.tag == "testsuites" and "tests" not in root.attrib:
        suites = list(root.findall("testsuite")); counts = {key: sum(int(suite.attrib.get(key, 0)) for suite in suites) for key in ("tests", "failures", "errors", "skipped")}
    else:
        counts = {key: int(root.attrib.get(key, 0)) for key in ("tests", "failures", "errors", "skipped")}
    return {"pytest_tests": counts["tests"], "pytest_failures": counts["failures"], "pytest_errors": counts["errors"], "pytest_skipped": counts["skipped"], "pytest_passed": counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]}


def assemble_artifact(head_sha, case_results, similarity_results, reproducibility_results, regression_summary, p10_ancestor, production_files_changed, artifact_kind="exact-sha-p11-parametric-foundation", baseline_sha=BASELINE_SHA):
    head = resolve_head_sha(head_sha)
    ids = [row.get("case_id") for row in case_results]
    by_id = {row.get("case_id"): row for row in case_results}
    case_set = ids == list(FORMAL_CASE_IDS) and len(by_id) == len(FORMAL_CASE_IDS)
    all_converged = case_set and all(row.get("converged") is True and row.get("termination_reason") == "converged" and row.get("final_residual", np.inf) <= 1e-8 for row in case_results)
    all_physical = case_set and all(row.get("physical") is True for row in case_results)
    branches = case_set and all(row.get("framework_branch_preserved") is True for row in case_results)
    sources_zero = case_set and all(set(row.get("source_totals", {})) == set(SOURCE_TOTAL_NAMES) and all(value == 0.0 for value in row["source_totals"].values()) for row in case_results)
    metrics_complete = case_set and all(set(row.get("metrics", {})) == set(REQUIRED_METRIC_NAMES) for row in case_results)
    modes_undefined = case_set and all(row.get("mode_classification_status") == "not-defined" and row.get("mode_label") is None and row.get("mode_criterion_id") is None for row in case_results)
    claim_level = case_set and all(row.get("scientific_claim_level") == "framework-only" for row in case_results)
    hashes_valid = case_set and all(re.fullmatch(r"[0-9a-f]{64}", str(row.get(name, ""))) for row in case_results for name in ("physics_input_hash", "run_configuration_hash"))
    if case_set:
        original, repeat = by_id["SUB-SW-P100"], by_id["SUB-SW-P100-REPEAT"]
        repeat_hashes = original["physics_input_hash"] == repeat["physics_input_hash"] and original["run_configuration_hash"] == repeat["run_configuration_hash"]
        unique_scales = all(len({by_id[f"{prefix}-SW-P{code}"]["physics_input_hash"] for code in ("080", "100", "120")}) == 3 for prefix in ("SUB", "SUP"))
    else:
        repeat_hashes = unique_scales = False
    similarity_complete = len(similarity_results) == 4 and {(row.get("branch"), row.get("pressure_scale")) for row in similarity_results} == {(branch, scale) for branch in BRANCHES for scale in (0.8, 1.2)}
    similarity_passed = similarity_complete and all(row.get("similarity_passed") is True for row in similarity_results)
    pytest_passed = regression_summary.get("pytest_step_passed") is True and regression_summary.get("pytest_failures") == 0 and regression_summary.get("pytest_errors") == 0 and isinstance(regression_summary.get("pytest_passed"), int) and regression_summary["pytest_passed"] >= 754
    gates = {
        "artifact_kind_valid": artifact_kind == "exact-sha-p11-parametric-foundation",
        "baseline_sha_valid": baseline_sha == BASELINE_SHA,
        "p10_baseline_ancestor": p10_ancestor is True,
        "production_freeze_passed": not production_files_changed,
        "pytest_passed": pytest_passed,
        "formal_case_set_complete": case_set,
        "all_formal_cases_converged": all_converged,
        "all_formal_states_physical": all_physical,
        "all_framework_branches_preserved": branches,
        "all_source_totals_zero": sources_zero,
        "similarity_passed": similarity_passed,
        "reproducibility_passed": reproducibility_results.get("reproducibility_passed") is True,
        "input_hashes_valid": bool(hashes_valid), "repeat_hashes_identical": bool(repeat_hashes),
        "unique_scale_hashes_distinct": bool(unique_scales), "metric_schema_complete": bool(metrics_complete),
        "mode_classification_undefined": bool(modes_undefined), "scientific_claim_level_framework_only": bool(claim_level),
        "artifact_structural_integrity": len(metric_definitions()) == len(REQUIRED_METRIC_NAMES),
    }
    return {
        "schema_version": 1, "stage": "P11.1", "artifact_kind": artifact_kind,
        "baseline_sha": baseline_sha, "head_sha": head, "workflow_sha": os.environ.get("GITHUB_SHA", head),
        "p10_closure_evidence": dict(P10_CLOSURE_EVIDENCE),
        "production_freeze": {"baseline_sha": BASELINE_SHA, "production_files_changed": list(production_files_changed), "production_freeze_passed": not production_files_changed},
        "regression_summary": dict(regression_summary), "formal_case_ids": ids,
        "case_results": list(case_results), "similarity_results": list(similarity_results),
        "reproducibility_results": dict(reproducibility_results), "metric_definitions": metric_definitions(),
        "mode_policy": {"lbw_ybw_classification_defined": False, "mode_criterion_id": None, "mode_label": None},
        "scientific_claim_level": "framework-only", "scientific_limitations": list(SCIENTIFIC_LIMITATIONS),
        "gates": gates, "all_passed": all(gates.values()),
    }


def run_formal_study():
    results = [run_study_case(case) for case in build_formal_manifest()]
    by_id = {row["case_id"]: row for row in results}
    similarity = []
    for prefix, branch in (("SUB", "subsonic"), ("SUP", "supersonic")):
        baseline = by_id[f"{prefix}-SW-P100"]
        for code in ("080", "120"):
            candidate = by_id[f"{prefix}-SW-P{code}"]
            if baseline["success"] and candidate["success"]:
                similarity.append(assess_similarity(baseline, candidate))
            else:
                similarity.append({"branch": branch, "case_id": candidate["case_id"], "pressure_scale": candidate["pressure_scale"], "metrics": [], "max_relative_l1": None, "max_relative_linf": None, "similarity_passed": False})
    if by_id["SUB-SW-P100"]["success"] and by_id["SUB-SW-P100-REPEAT"]["success"]:
        reproducibility = assess_reproducibility(by_id["SUB-SW-P100"], by_id["SUB-SW-P100-REPEAT"])
    else:
        reproducibility = {"reproducibility_passed": False}
    return results, similarity, reproducibility


def _flat_result(row):
    failure = row.get("failure") or {}
    values = {key: row.get(key, "") for key in CASE_RESULT_FIELDS}
    values.update(row.get("metrics", {})); values.update(row.get("source_totals", {}))
    values.update({"failure_status": failure.get("status", ""), "failure_type": failure.get("type", ""), "failure_message": failure.get("message", "")})
    return values


def _case_manifest(artifact):
    cases = build_formal_manifest()
    by_id = {row["case_id"]: row for row in artifact["case_results"]}
    return {
        "schema_version": 1, "stage": "P11.1", "study_kind": "controlled-pressure-similarity-framework-pilot",
        "head_sha": artifact["head_sha"], "baseline_sha": BASELINE_SHA,
        "gas": asdict(GAS), "geometry": {"domain_length": 1.0, "num_cells": 80, "face_area_left": 1.0, "face_area_right": 1.2, "distribution": "linear"},
        "numerical_controls": {"scheme": "steger-warming", "CFL": 0.2, "steady_tolerance": 1e-8, "max_time": 0.10, "max_steps": 200000},
        "formal_case_ids": list(FORMAL_CASE_IDS), "factor_definition": asdict(cases[0].factor),
        "case_inputs": [asdict(case) for case in cases],
        "input_hashes": {case_id: {"physics_input_hash": by_id[case_id]["physics_input_hash"], "run_configuration_hash": by_id[case_id]["run_configuration_hash"]} for case_id in FORMAL_CASE_IDS},
        "mode_classification_policy": artifact["mode_policy"], "scientific_claim_policy": {"level": "framework-only"},
    }


def _summary(artifact):
    return f"""# P11.1 Parametric Study Foundation

## Purpose

Verify a deterministic, traceable parameter-study framework.

## P10 Accepted Baseline

`{BASELINE_SHA}`

## Study Scope

Framework pilot only; not a calibrated engine case.

## Controlled Pressure-Similarity Experiment

The 0.8/1.0/1.2 stagnation-pressure scales are framework controls, not engine operating conditions.

## Formal Case Matrix

{', '.join(FORMAL_CASE_IDS)}

## Study Metrics

Mass-flow, total-state, pressure, temperature, Mach, sonic observables, and source-input totals are recorded.

## Similarity Results

Numerical L1/Linf gates: {'PASS' if artifact['gates']['similarity_passed'] else 'FAIL'}.

## Reproducibility

Exact repeat gate: {'PASS' if artifact['gates']['reproducibility_passed'] else 'FAIL'}.

## Mode-Classification Policy

LBW/YBW classification is not defined; Mach observables are diagnostics only.

## Scientific Limitations

{'; '.join(SCIENTIFIC_LIMITATIONS)}.

## Inputs Still Required Before P11.2

Authoritative physical inputs, factor ranges, LBW/YBW definitions, criterion provenance, and comparison data remain NOT FROZEN.

## Formal Status

{'The P11.1 study framework executes deterministic, traceable parameter points and reproduces the expected pressure-similarity relations on the controlled verified quasi-1D benchmark.' if artifact['all_passed'] else 'P11.1 formal gates did not all pass.'}
"""


def _write_plots(artifact, target):
    by_id = {row["case_id"]: row for row in artifact["case_results"]}
    specs = (("Mach", "Mach", False), ("p", "p / pressure scale [Pa]", True), ("rho", "rho / pressure scale [kg/m^3]", True))
    paths = []
    for variable, ylabel, scale_value in specs:
        figure, axes = plt.subplots(1, 2, figsize=(10, 4))
        for axis, (prefix, branch) in zip(axes, (("SUB", "subsonic"), ("SUP", "supersonic")), strict=True):
            for code in ("080", "100", "120"):
                row = by_id[f"{prefix}-SW-P{code}"]
                if row.get("fields"):
                    values = np.asarray(row["fields"][variable], dtype=float)
                    if scale_value: values = values / row["pressure_scale"]
                    axis.plot(row["fields"]["x"], values, label=f"s={row['pressure_scale']:.1f}")
            axis.set_title(branch); axis.set_xlabel("x [m]"); axis.set_ylabel(ylabel); axis.grid(True); axis.legend()
        figure.tight_layout()
        path = target / f"p11_1_{'mach' if variable == 'Mach' else 'pressure' if variable == 'p' else 'density'}_similarity.png"
        figure.savefig(path, dpi=160); plt.close(figure); paths.append(path)
    return paths


def write_artifacts(artifact, output_dir=ROOT / "artifacts" / "p11_1"):
    target = Path(output_dir); target.mkdir(parents=True, exist_ok=True)
    json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False)
    foundation = target / "p11_1_foundation.json"
    try:
        manifest = target / "p11_1_case_manifest.json"; manifest.write_text(json.dumps(_case_manifest(artifact), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        results_csv = target / "p11_1_case_results.csv"
        with results_csv.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=CASE_RESULT_FIELDS); writer.writeheader(); writer.writerows(_flat_result(row) for row in artifact["case_results"])
        definitions_csv = target / "p11_1_metric_definitions.csv"
        with definitions_csv.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=METRIC_DEFINITION_FIELDS); writer.writeheader(); writer.writerows(artifact["metric_definitions"])
        arrays = {}
        for row in artifact["case_results"]:
            safe = re.sub(r"[^A-Za-z0-9]+", "_", row["case_id"]).strip("_")
            for name in ("rho", "u", "p", "T", "Mach", "mass_flow", "local_total_pressure", "local_total_temperature"):
                if name in row.get("fields", {}): arrays[f"{safe}__{name}"] = np.asarray(row["fields"][name], dtype=float)
        first = next((row for row in artifact["case_results"] if row.get("fields")), None)
        if first is not None:
            arrays["x"] = np.asarray(first["fields"]["x"]); arrays["area"] = np.asarray(first["fields"]["area"])
        fields_path = target / "p11_1_fields.npz"; np.savez(fields_path, **arrays)
        summary = target / "p11_1_summary.md"; summary.write_text(_summary(artifact), encoding="utf-8")
        plots = _write_plots(artifact, target)
        outputs = [foundation, manifest, results_csv, definitions_csv, fields_path, summary, *plots]
        if {path.name for path in outputs} != set(REQUIRED_ARTIFACT_NAMES) or not all(path.is_file() for path in outputs if path != foundation):
            raise RuntimeError("P11.1 artifact set is incomplete")
    except Exception:
        artifact["gates"]["artifact_structural_integrity"] = False
        artifact["all_passed"] = False
        foundation.write_text(json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        raise
    foundation.write_text(json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return outputs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--head-sha"); parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts" / "p11_1"); parser.add_argument("--pytest-xml", type=Path, default=ROOT / "artifacts" / "p11_1" / "pytest.xml"); args = parser.parse_args(argv)
    regression = parse_pytest_xml(args.pytest_xml); regression["pytest_step_passed"] = os.environ.get("P11_1_PYTEST_OUTCOME", "success") == "success"
    results, similarity, reproducibility = run_formal_study()
    head = resolve_head_sha(args.head_sha)
    artifact = assemble_artifact(head, results, similarity, reproducibility, regression, p10_is_ancestor(head), production_files_changed(head))
    write_artifacts(artifact, args.output_dir)
    print(json.dumps({"head_sha": head, "gates": artifact["gates"], "all_passed": artifact["all_passed"]}, indent=2, allow_nan=False))
    return 0 if artifact["all_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
