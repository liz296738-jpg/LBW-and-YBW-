"""P11.2A source-backed public surrogate cold-flow study.

This study deliberately separates published source values, model-derived inlet
state, reduced-order geometry mapping, and numerical controls. It does not
activate fuel injection, combustion, wall friction, or wall heat transfer and
must not be presented as a reactive-engine or Cao-thesis reproduction.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
from scramjet1d.solver import SteadySolverResult, solve_quasi_1d_steady
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative

SOURCE_PATH = ROOT / "cases" / "studies" / "data" / "p11_2_public_surrogate_source.json"
DEFAULT_OUTPUT = ROOT / "results" / "p11_2a_public_surrogate"
CASE_ID_BASELINE = "P11A-PUBLIC-COLD-BASE"
CASE_ID_ISO_SHORT = "P11A-ISO-L280"
EXPECTED_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class StaticInlet:
    """Perfect-gas static inlet state derived from source total conditions."""

    Mach: float
    T_K: float
    p_Pa: float
    rho_kg_m3: float
    a_m_s: float
    u_m_s: float


@dataclass(frozen=True)
class StudyCase:
    """Complete P11.2A case definition before the solver is called."""

    case_id: str
    isolator_length_m: float
    num_cells: int
    dx_m: float
    domain_length_m: float
    geometry: AreaProfile
    x_cell_m: np.ndarray
    inlet: StaticInlet
    boundary_conditions: BoundaryConditions
    gas: GasProperties
    numerical: NumericalConfig
    max_time_s: float
    max_steps: int


def _positive(name: str, value: Any) -> float:
    scalar = np.asarray(value, dtype=float)
    if scalar.ndim != 0 or not np.isfinite(scalar) or scalar <= 0.0:
        raise ValueError(f"{name} must be a finite, strictly positive scalar")
    return float(scalar)


def load_public_surrogate_source(path: Path | str = SOURCE_PATH) -> dict[str, Any]:
    """Load and validate the tracked source ledger used by P11.2A."""

    source_path = Path(path)
    with source_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if data.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        raise ValueError(
            f"unsupported source schema_version={data.get('schema_version')!r}; "
            f"expected {EXPECTED_SCHEMA_VERSION}"
        )
    if data.get("case_family") != "P11.2_PUBLIC_SURROGATE_SOURCE":
        raise ValueError("unexpected source case_family")

    primary = data.get("primary_source")
    if not isinstance(primary, dict) or not primary.get("doi") or not primary.get("citation"):
        raise ValueError("primary_source must contain citation and doi")

    inflow = data.get("inflow_total_conditions_si")
    geometry = data.get("geometry_si")
    if not isinstance(inflow, dict) or not isinstance(geometry, dict):
        raise ValueError("source ledger must contain inflow_total_conditions_si and geometry_si")

    for key in ("Mach", "T0_K", "P0_Pa"):
        _positive(f"inflow.{key}", inflow.get(key))
    for key in (
        "L1_isolator_m",
        "L2_pre_cavity_m",
        "L3_combustor_m",
        "width_W_m",
        "height_H1_m",
        "height_H2_m",
        "cavity_length_Lc_m",
        "cavity_depth_Dc_m",
        "cavity_ramp_height_Hc_m",
        "injector_distance_d1_m",
        "injector_distance_d2_m",
        "injector_distance_d3_m",
    ):
        _positive(f"geometry.{key}", geometry.get(key))

    mass_fractions = inflow.get("mass_fractions")
    if not isinstance(mass_fractions, dict) or not mass_fractions:
        raise ValueError("inflow mass_fractions must be a nonempty mapping")
    fraction_total = 0.0
    for species, fraction in mass_fractions.items():
        value = np.asarray(fraction, dtype=float)
        if value.ndim != 0 or not np.isfinite(value) or value < 0.0:
            raise ValueError(f"mass fraction {species} must be finite and nonnegative")
        fraction_total += float(value)
    if not math.isclose(fraction_total, 1.0, rel_tol=0.0, abs_tol=1.0e-6):
        raise ValueError(f"inflow mass fractions must sum to 1; got {fraction_total}")

    operating_conditions = data.get("operating_conditions")
    if not isinstance(operating_conditions, list) or not operating_conditions:
        raise ValueError("operating_conditions must be a nonempty list")
    for index, condition in enumerate(operating_conditions):
        if not isinstance(condition, dict):
            raise ValueError(f"operating_conditions[{index}] must be a mapping")
        for key in ("equivalence_ratio", "injector_total_pressure_Pa", "ethylene_mass_flow_kg_s"):
            value = np.asarray(condition.get(key), dtype=float)
            if value.ndim != 0 or not np.isfinite(value) or value < 0.0:
                raise ValueError(f"operating_conditions[{index}].{key} must be finite and nonnegative")

    return data


def total_to_static_inlet(
    Mach: object,
    T0_K: object,
    P0_Pa: object,
    gas: GasProperties,
) -> StaticInlet:
    """Convert source total conditions to a perfect-gas primitive inlet state."""

    M = _positive("Mach", Mach)
    T0 = _positive("T0_K", T0_K)
    P0 = _positive("P0_Pa", P0_Pa)
    beta = 0.5 * (gas.gamma - 1.0)
    ratio = 1.0 + beta * M**2
    temperature = T0 / ratio
    pressure = P0 / ratio ** (gas.gamma / (gas.gamma - 1.0))
    density = pressure / (gas.R * temperature)
    sound_speed = math.sqrt(gas.gamma * gas.R * temperature)
    velocity = M * sound_speed
    return StaticInlet(M, temperature, pressure, density, sound_speed, velocity)


def source_inlet(source: dict[str, Any], gas: GasProperties) -> StaticInlet:
    """Derive the primitive inlet from the tracked source ledger."""

    inflow = source["inflow_total_conditions_si"]
    return total_to_static_inlet(inflow["Mach"], inflow["T0_K"], inflow["P0_Pa"], gas)


def _core_height(
    x_m: np.ndarray,
    *,
    isolator_length_m: float,
    pre_cavity_length_m: float,
    combustor_length_m: float,
    H1_m: float,
    H2_m: float,
) -> np.ndarray:
    """Return the documented reduced-order core-flow height mapping.

    Mapping policy: the isolator and pre-cavity main-flow passage use H1. The
    combustor main-flow passage then varies linearly from H1 at combustor entry
    to H2 at the downstream end. This is an explicit reduced-order mapping of
    the dimensioned H1/H2 endpoints; cavity recirculation volume is excluded.
    """

    start = isolator_length_m + pre_cavity_length_m
    xi = np.clip((x_m - start) / combustor_length_m, 0.0, 1.0)
    return H1_m + (H2_m - H1_m) * xi


def build_public_surrogate_geometry(
    source: dict[str, Any],
    num_cells: int,
    *,
    isolator_length_m: float | None = None,
) -> tuple[AreaProfile, np.ndarray, float]:
    """Build the P11.2A core-flow AreaProfile from source-backed dimensions.

    The paper supplies lengths, width, H1 and H2 but no quasi-1D cavity closure.
    P11.2A therefore uses a transparent reduced-order mapping: constant H1
    through isolator + pre-cavity section and linear main-passage expansion from
    H1 to H2 across L3. The cavity depth/volume is metadata only and is not added
    to the core-flow area.
    """

    if isinstance(num_cells, (bool, np.bool_)) or not isinstance(num_cells, (int, np.integer)):
        raise ValueError("num_cells must be a positive integer")
    if int(num_cells) < 2:
        raise ValueError("num_cells must be at least 2")

    g = source["geometry_si"]
    L1 = _positive("isolator_length_m", g["L1_isolator_m"] if isolator_length_m is None else isolator_length_m)
    L2 = _positive("L2_pre_cavity_m", g["L2_pre_cavity_m"])
    L3 = _positive("L3_combustor_m", g["L3_combustor_m"])
    width = _positive("width_W_m", g["width_W_m"])
    H1 = _positive("height_H1_m", g["height_H1_m"])
    H2 = _positive("height_H2_m", g["height_H2_m"])

    length = L1 + L2 + L3
    faces = np.linspace(0.0, length, int(num_cells) + 1)
    cells = 0.5 * (faces[:-1] + faces[1:])
    face_height = _core_height(
        faces,
        isolator_length_m=L1,
        pre_cavity_length_m=L2,
        combustor_length_m=L3,
        H1_m=H1,
        H2_m=H2,
    )
    cell_height = _core_height(
        cells,
        isolator_length_m=L1,
        pre_cavity_length_m=L2,
        combustor_length_m=L3,
        H1_m=H1,
        H2_m=H2,
    )
    profile = AreaProfile(cell_area=width * cell_height, face_area=width * face_height)
    return profile, cells, length


def _git_sha() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def build_case(
    source: dict[str, Any],
    *,
    case_id: str = CASE_ID_BASELINE,
    isolator_length_m: float | None = None,
    target_dx_m: float = 0.005,
    gas: GasProperties | None = None,
    cfl: float = 0.2,
    tolerance: float = 1.0e-8,
    max_time_s: float = 0.02,
    max_steps: int = 200_000,
) -> StudyCase:
    """Build one cold-flow P11.2A case with approximately fixed axial resolution."""

    gas_model = GasProperties() if gas is None else gas
    target_dx = _positive("target_dx_m", target_dx_m)
    g = source["geometry_si"]
    L1 = _positive("isolator_length_m", g["L1_isolator_m"] if isolator_length_m is None else isolator_length_m)
    length = L1 + _positive("L2_pre_cavity_m", g["L2_pre_cavity_m"]) + _positive("L3_combustor_m", g["L3_combustor_m"])
    num_cells = max(2, int(round(length / target_dx)))
    geometry, x_cell, checked_length = build_public_surrogate_geometry(
        source, num_cells, isolator_length_m=L1
    )
    dx = checked_length / num_cells
    inlet = source_inlet(source, gas_model)
    conditions = BoundaryConditions(
        inlet="supersonic-inflow",
        outlet="supersonic-outflow",
        inlet_state=PrimitiveBoundaryState(inlet.rho_kg_m3, inlet.u_m_s, inlet.p_Pa),
    )
    numerical = NumericalConfig(cfl=cfl, tolerance=tolerance)
    return StudyCase(
        case_id=case_id,
        isolator_length_m=L1,
        num_cells=num_cells,
        dx_m=dx,
        domain_length_m=checked_length,
        geometry=geometry,
        x_cell_m=x_cell,
        inlet=inlet,
        boundary_conditions=conditions,
        gas=gas_model,
        numerical=numerical,
        max_time_s=_positive("max_time_s", max_time_s),
        max_steps=int(max_steps),
    )


def run_case(case: StudyCase) -> SteadySolverResult:
    """Run one non-reactive P11.2A steady case with all optional sources disabled."""

    inlet = case.inlet
    U_single = primitive_to_conservative(inlet.rho_kg_m3, inlet.u_m_s, inlet.p_Pa, case.gas)
    U0 = np.broadcast_to(U_single, (case.num_cells, 3)).copy()
    return solve_quasi_1d_steady(
        U0,
        case.geometry,
        case.dx_m,
        case.max_time_s,
        case.gas,
        case.numerical,
        max_steps=case.max_steps,
        flux_scheme="steger-warming",
        boundary_conditions=case.boundary_conditions,
        hydraulic_diameter=None,
        darcy_friction_factor=0.0,
        wall_heat_flux=0.0,
        fuel_mass_flow_rate_per_length=0.0,
        fuel_axial_velocity=0.0,
        fuel_specific_total_enthalpy=0.0,
        fuel_burn_rate_per_length=0.0,
        fuel_lower_heating_value=None,
    )


def summarize_case(case: StudyCase, result: SteadySolverResult, source: dict[str, Any]) -> dict[str, Any]:
    """Return traceable metrics and metadata for one completed P11.2A case."""

    primitive = conservative_to_primitive(result.U, case.gas)
    mass_flow = primitive.rho * primitive.u * case.geometry.cell_area
    mean_mass_flow = float(np.mean(mass_flow))
    mass_flow_span = float((np.max(mass_flow) - np.min(mass_flow)) / abs(mean_mass_flow))
    inflow = source["inflow_total_conditions_si"]
    primary = source["primary_source"]
    metrics = {
        "Mach_in": float(primitive.Mach[0]),
        "Mach_out": float(primitive.Mach[-1]),
        "Mach_min": float(np.min(primitive.Mach)),
        "Mach_max": float(np.max(primitive.Mach)),
        "p_in_Pa": float(primitive.p[0]),
        "p_out_Pa": float(primitive.p[-1]),
        "p_min_Pa": float(np.min(primitive.p)),
        "p_max_Pa": float(np.max(primitive.p)),
        "T_in_K": float(primitive.T[0]),
        "T_out_K": float(primitive.T[-1]),
        "T_min_K": float(np.min(primitive.T)),
        "T_max_K": float(np.max(primitive.T)),
        "mass_flow_in_kg_s": float(mass_flow[0]),
        "mass_flow_out_kg_s": float(mass_flow[-1]),
        "mass_flow_mean_kg_s": mean_mass_flow,
        "mass_flow_relative_span": mass_flow_span,
    }
    return {
        "case_id": case.case_id,
        "claim_level": "PHYSICAL-SCALE PUBLIC SURROGATE — NON-REACTIVE REDUCED-ORDER MODEL",
        "converged": bool(result.converged),
        "termination_reason": result.termination_reason,
        "steps": int(result.steps),
        "final_time_s": float(result.time),
        "final_residual": float(result.residual),
        "source": {
            "citation": primary["citation"],
            "doi": primary["doi"],
            "locators": primary["locators"],
            "source_values": {
                "Mach": inflow["Mach"],
                "T0_K": inflow["T0_K"],
                "P0_Pa": inflow["P0_Pa"],
                "isolator_length_m": case.isolator_length_m,
            },
        },
        "model_derived": asdict(case.inlet),
        "model_assumptions": {
            "gas": {"gamma": case.gas.gamma, "R_J_kgK": case.gas.R},
            "geometry_mapping": "H=H1 through L1+L2; linear H1->H2 across L3; cavity recirculation volume excluded",
            "reactive_sources": "disabled: source paper does not provide solver-ready axial injection/burn distributions",
        },
        "numerical_controls": {
            "scheme": "steger-warming",
            "N": case.num_cells,
            "dx_m": case.dx_m,
            "CFL": case.numerical.cfl,
            "tolerance": case.numerical.tolerance,
            "max_time_s": case.max_time_s,
            "max_steps": case.max_steps,
            "inlet_bc": "supersonic-inflow",
            "outlet_bc": "supersonic-outflow",
        },
        "metrics": metrics,
        "git_sha": _git_sha(),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def write_artifacts(
    output_dir: Path,
    case: StudyCase,
    result: SteadySolverResult,
    summary: dict[str, Any],
) -> None:
    """Write JSON/CSV/PNG artifacts for one completed case."""

    case_dir = output_dir / case.case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    primitive = conservative_to_primitive(result.U, case.gas)
    mass_flow = primitive.rho * primitive.u * case.geometry.cell_area

    (case_dir / "case_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    with (case_dir / "profile.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["x_m", "A_m2", "rho_kg_m3", "u_m_s", "p_Pa", "T_K", "Mach", "mass_flow_kg_s"])
        writer.writerows(
            zip(
                case.x_cell_m,
                case.geometry.cell_area,
                primitive.rho,
                primitive.u,
                primitive.p,
                primitive.T,
                primitive.Mach,
                mass_flow,
            )
        )
    with (case_dir / "residual.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["pseudo_time_s", "normalized_residual"])
        writer.writerows(zip(result.time_history, result.residual_history))

    plots = {
        "pressure_profile.png": (primitive.p, "Static pressure [Pa]"),
        "temperature_profile.png": (primitive.T, "Static temperature [K]"),
        "mach_profile.png": (primitive.Mach, "Mach [-]"),
        "mass_flow_profile.png": (mass_flow, "Mass flow [kg/s]"),
    }
    for filename, (values, ylabel) in plots.items():
        fig, ax = plt.subplots()
        ax.plot(case.x_cell_m, values, label=case.case_id)
        ax.set_xlabel("x [m]")
        ax.set_ylabel(ylabel)
        ax.set_title(case.case_id)
        ax.grid(True, alpha=0.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(case_dir / filename, dpi=160)
        plt.close(fig)


def formal_cases(source: dict[str, Any]) -> list[StudyCase]:
    """Return baseline and source-backed isolator-length OFAT cases."""

    alternate = source["published_ofat_levels"]["isolator_length"]["alternate_m"]
    return [
        build_case(source, case_id=CASE_ID_BASELINE),
        build_case(source, case_id=CASE_ID_ISO_SHORT, isolator_length_m=alternate),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formal", action="store_true", help="run the baseline and isolator-length OFAT")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    source = load_public_surrogate_source()

    if not args.formal:
        inlet = source_inlet(source, GasProperties())
        print(json.dumps({"source": str(SOURCE_PATH), "derived_inlet": asdict(inlet)}, indent=2))
        return 0

    overall: dict[str, Any] = {"study": "P11.2A", "cases": []}
    for case in formal_cases(source):
        result = run_case(case)
        summary = summarize_case(case, result, source)
        write_artifacts(args.output_dir, case, result, summary)
        overall["cases"].append(summary)
        if not result.converged:
            (args.output_dir / "study_summary.json").parent.mkdir(parents=True, exist_ok=True)
            (args.output_dir / "study_summary.json").write_text(
                json.dumps(overall, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            raise RuntimeError(
                f"formal case {case.case_id} did not converge: {result.termination_reason}, residual={result.residual}"
            )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "study_summary.json").write_text(
        json.dumps(overall, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
