"""Executable NASA Burrows-Kurkov reduced-order heated candidate case.

The reduced domain begins at the hydrogen-injection station x=0, so its inlet
is a conservative moment match to the NASA reference section there rather than
a silent reuse of the upstream freestream.  Signed energy and momentum histories
are derived only from the public NASA Wind-US reference solution.  Experimental
exit profiles remain independent benchmark observations and are never used to
tune these sources or the inlet state.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from cases.studies.p11_2b_nasa_bk_energy_reduction import (
    cell_net_energy_rate_per_length,
    conservation_diagnostic as energy_conservation_diagnostic,
    load_energy_reduction,
)
from cases.studies.p11_2b_nasa_bk_geometry import sample_cell_and_face_areas
from cases.studies.p11_2b_nasa_bk_momentum_reduction import (
    cell_net_momentum_rate_per_length,
    conservation_diagnostic as momentum_conservation_diagnostic,
    load_momentum_reduction,
)
from cases.studies.p11_2b_nasa_bk_reference_inlet import effective_inlet_for_gas
from cases.studies.p11_2b_nasa_bk_thermo import reference_effective_gas
from scramjet1d.boundary import BoundaryConditions, PrimitiveBoundaryState
from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.geometry import AreaProfile
from scramjet1d.net_energy import solve_quasi_1d_steady_with_net_energy
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative


REFERENCE_EXIT_DIAGNOSTIC = {
    "classification": "NASA_REFERENCE_SOLUTION_DERIVED_NOT_EXPERIMENT",
    "mass_flux_weighted_Mach": 2.2849362704413,
    "mass_flux_weighted_static_temperature_K": 1312.51519653549,
    "area_weighted_static_pressure_Pa": 104938.645610725,
}


def _build_case(num_cells: int, gamma: float | None) -> dict[str, Any]:
    if not isinstance(num_cells, int) or isinstance(num_cells, bool) or num_cells < 20:
        raise ValueError("num_cells must be an integer >= 20")

    thermo = reference_effective_gas()
    gamma_run = thermo.gamma if gamma is None else float(gamma)
    gas = GasProperties(gamma=gamma_run, R=thermo.R_J_per_kg_K)

    mesh = sample_cell_and_face_areas(num_cells)
    geometry = AreaProfile(mesh["area_cell_m2"], mesh["area_face_m2"])
    x_face = mesh["x_face_m"]
    x_cell = mesh["x_cell_m"]
    dx = float(x_face[1] - x_face[0])

    inlet = effective_inlet_for_gas(gas)
    rho_in = inlet.rho_kg_per_m3
    u_in = inlet.u_m_per_s
    p_in = inlet.p_Pa
    T_in = inlet.T_K
    M_in = inlet.Mach
    mass_flow = inlet.mass_flow_kg_s

    state0 = primitive_to_conservative(
        np.full(num_cells, rho_in),
        np.full(num_cells, u_in),
        np.full(num_cells, p_in),
        gas,
    )
    boundaries = BoundaryConditions(
        inlet="supersonic-inflow",
        outlet="supersonic-outflow",
        inlet_state=PrimitiveBoundaryState(rho_in, u_in, p_in),
    )
    line_energy = cell_net_energy_rate_per_length(x_face, mass_flow)
    line_momentum = cell_net_momentum_rate_per_length(x_face, mass_flow)
    energy_check = energy_conservation_diagnostic(x_face, mass_flow)
    momentum_check = momentum_conservation_diagnostic(x_face, mass_flow)

    return {
        "gas": gas,
        "geometry": geometry,
        "x_face": x_face,
        "x_cell": x_cell,
        "dx": dx,
        "rho_in": rho_in,
        "u_in": u_in,
        "p_in": p_in,
        "T_in": T_in,
        "M_in": M_in,
        "mass_flow": mass_flow,
        "inlet_h0": inlet.specific_total_enthalpy_J_per_kg,
        "state0": state0,
        "boundaries": boundaries,
        "line_energy": line_energy,
        "line_momentum": line_momentum,
        "energy_check": energy_check,
        "momentum_check": momentum_check,
    }


def run_candidate(
    *,
    num_cells: int = 80,
    gamma: float | None = None,
    cfl: float = 0.35,
    tolerance: float = 1.0e-7,
    max_time: float = 0.02,
    max_steps: int = 60_000,
) -> tuple[dict[str, Any], list[dict[str, float]]]:
    """Run one reduced-order candidate and return summary plus axial profile."""

    case = _build_case(num_cells, gamma)
    gas: GasProperties = case["gas"]
    numerical = NumericalConfig(cfl=cfl, tolerance=tolerance)
    result = solve_quasi_1d_steady_with_net_energy(
        case["state0"],
        case["geometry"],
        case["dx"],
        max_time,
        gas,
        numerical,
        net_energy_rate_per_length=case["line_energy"],
        net_momentum_rate_per_length=case["line_momentum"],
        max_steps=max_steps,
        flux_scheme="rusanov",
        boundary_conditions=case["boundaries"],
    )
    primitive = conservative_to_primitive(result.U, gas)
    total_temperature = primitive.T * (
        1.0 + 0.5 * (gas.gamma - 1.0) * primitive.Mach**2
    )
    h0 = gas.cp * primitive.T + 0.5 * primitive.u**2
    predicted_delta_h0 = float(h0[-1] - case["inlet_h0"])
    reference_delta_h0 = float(load_energy_reduction()["delta_h0_J_per_kg"][-1])
    reference_delta_momentum = float(
        load_momentum_reduction()["delta_specific_momentum_m_per_s"][-1]
    )

    exit_mach = float(primitive.Mach[-1])
    exit_temperature = float(primitive.T[-1])
    exit_pressure = float(primitive.p[-1])
    reference_exit = REFERENCE_EXIT_DIAGNOSTIC

    profile: list[dict[str, float]] = []
    for index, x in enumerate(case["x_cell"]):
        profile.append(
            {
                "x_m": float(x),
                "Mach": float(primitive.Mach[index]),
                "temperature_K": float(primitive.T[index]),
                "pressure_Pa": float(primitive.p[index]),
                "total_temperature_K": float(total_temperature[index]),
                "specific_total_enthalpy_J_per_kg": float(h0[index]),
                "net_energy_rate_per_length_W_per_m": float(case["line_energy"][index]),
                "net_momentum_rate_per_length_N_per_m": float(case["line_momentum"][index]),
            }
        )

    summary = {
        "schema_version": 3,
        "case_id": "P11.2B-NASA-BK-HEATED-CANDIDATE",
        "status": "CANDIDATE_NOT_FORMAL_UNTIL_REVIEWED",
        "source_class": "NASA_REFERENCE_SOLUTION_DERIVED",
        "num_cells": num_cells,
        "gas": {"gamma": gas.gamma, "R_J_per_kg_K": gas.R, "cp_J_per_kg_K": gas.cp},
        "reduced_domain_inlet": {
            "classification": "NASA_REFERENCE_SOLUTION_DERIVED_CONSERVATIVE_MOMENT_MATCH",
            "Mach": case["M_in"],
            "temperature_K": case["T_in"],
            "pressure_Pa": case["p_in"],
            "density_kg_per_m3": case["rho_in"],
            "velocity_m_per_s": case["u_in"],
            "mass_flow_kg_s": case["mass_flow"],
            "specific_total_enthalpy_J_per_kg": case["inlet_h0"],
        },
        "solver": {
            "cfl": cfl,
            "tolerance": tolerance,
            "max_time_s": max_time,
            "max_steps": max_steps,
            "converged": result.converged,
            "termination_reason": result.termination_reason,
            "steps": result.steps,
            "final_time_s": result.time,
            "final_residual": result.residual,
        },
        "flow_scope": {
            "minimum_Mach": float(np.min(primitive.Mach)),
            "maximum_Mach": float(np.max(primitive.Mach)),
            "exit_Mach": exit_mach,
            "exit_temperature_K": exit_temperature,
            "exit_pressure_Pa": exit_pressure,
            "exit_total_temperature_K": float(total_temperature[-1]),
        },
        "energy_closure": {
            **case["energy_check"],
            "reference_delta_h0_eff_J_per_kg": reference_delta_h0,
            "predicted_exit_minus_inlet_h0_J_per_kg": predicted_delta_h0,
            "specific_energy_error_J_per_kg": predicted_delta_h0 - reference_delta_h0,
        },
        "momentum_closure": {
            **case["momentum_check"],
            "reference_delta_specific_momentum_m_per_s": reference_delta_momentum,
            "interpretation": "Effective axial residual after the quasi-1D pressure-area term; not a friction coefficient or measured wall shear."
        },
        "reference_solution_exit_diagnostic": {
            **reference_exit,
            "candidate_minus_reference_Mach": exit_mach - float(reference_exit["mass_flux_weighted_Mach"]),
            "candidate_minus_reference_static_temperature_K": exit_temperature - float(reference_exit["mass_flux_weighted_static_temperature_K"]),
            "candidate_minus_reference_static_pressure_Pa": exit_pressure - float(reference_exit["area_weighted_static_pressure_Pa"]),
            "acceptance_role": "diagnostic_only_not_tuned_acceptance_target",
        },
        "claim_boundary": [
            "The reduced domain starts at x=0, so its inlet is a NASA_REFERENCE_SOLUTION_DERIVED conservative moment match rather than the upstream freestream state.",
            "Signed net energy and axial momentum residuals are both NASA_REFERENCE_SOLUTION_DERIVED.",
            "The momentum residual is added independently of the net-energy source; no extra u*F energy term is added because the energy history is prescribed independently from the same reference solution.",
            "It is not finite-rate chemistry validation and does not validate species profiles.",
            "Experimental exit profiles are not used to tune the inlet or either source and remain independent benchmark context.",
            "Burrows-Kurkov does not authorize LBW/YBW classification."
        ],
    }
    return summary, profile


def write_outputs(output_dir: Path, summary: dict[str, Any], profile: list[dict[str, float]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8"
    )
    with (output_dir / "profile.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(profile[0]))
        writer.writeheader()
        writer.writerows(profile)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cells", type=int, default=80)
    parser.add_argument("--gamma", type=float, default=None)
    args = parser.parse_args()
    summary, profile = run_candidate(num_cells=args.cells, gamma=args.gamma)
    write_outputs(args.output_dir, summary, profile)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
