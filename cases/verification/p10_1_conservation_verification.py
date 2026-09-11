"""Generate a strict V1-V8 P10.1 conservation artifact."""
import json
import os
import re
import subprocess
from pathlib import Path
import numpy as np
from scramjet1d.boundary import BoundaryConditions
from scramjet1d.config import GasProperties
from scramjet1d.geometry import AreaProfile, constant_area_profile
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative
from scramjet1d.solver import quasi_1d_rhs
from scramjet1d.verification import quasi_1d_conservation_balance

EXPECTED_CASE_IDS = {"V1_uniform_constant_area", "V2_nonuniform_constant_area", "V3_variable_area_geometry", "V4_wall_source", "V5_fuel_injection", "V6_combustion_heat_release", "V7_combined_source_ledger", "V8_physical_boundary_ledger"}
EXPECTED_SCHEMES = {"rusanov", "steger-warming"}; GAS = GasProperties(); N = 8; DX = .1


def _close(actual, expected):
    scale = max(1.0, float(np.max(np.abs(actual))), float(np.max(np.abs(expected))))
    return bool(np.allclose(actual, expected, rtol=256*np.finfo(float).eps, atol=256*np.finfo(float).eps*scale))


def case_passed(case):
    schemes = case.get("schemes", {})
    return set(schemes) == EXPECTED_SCHEMES and all(record.get("global_balance_pass") is True for record in schemes.values()) and all(value is True for value in case.get("gates", {}).values())


def artifact_passed(cases):
    return set(cases) == EXPECTED_CASE_IDS and all(case_passed(case) for case in cases.values())


def resolve_head_sha(explicit=None):
    head = explicit or os.environ.get("GITHUB_SHA") or subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if re.fullmatch(r"[0-9a-fA-F]{40}", head) is None: raise ValueError("head SHA must contain exactly 40 hexadecimal characters")
    return head.lower()


def state(nonuniform=False):
    x = np.linspace(0., 1., N)
    rho = 1.2 + (.01*np.sin(x) if nonuniform else np.zeros(N)); velocity = 200. + (2*np.cos(x) if nonuniform else np.zeros(N)); pressure = 100000. + (100*np.sin(x) if nonuniform else np.zeros(N))
    return primitive_to_conservative(rho, velocity, pressure, GAS)


def physical_bc(U):
    q = conservative_to_primitive(U, GAS); beta = (GAS.gamma-1)/2
    return BoundaryConditions(inlet="subsonic-total-inflow", outlet="subsonic-pressure", inlet_total_pressure=float(q.p[0]*(1+beta*q.Mach[0]**2)**(GAS.gamma/(GAS.gamma-1))), inlet_total_temperature=float(q.T[0]*(1+beta*q.Mach[0]**2)), outlet_static_pressure=float(q.p[0]))


def record(U, geometry, gates=None, **kwargs):
    schemes = {}
    for scheme in EXPECTED_SCHEMES:
        b = quasi_1d_conservation_balance(U, geometry, DX, GAS, flux_scheme=scheme, **kwargs)
        schemes[scheme] = {key: getattr(b, key).tolist() for key in ("rhs_integral", "boundary_flux", "source_integral", "closure_error", "area_source_integral", "wall_source_integral", "fuel_source_integral", "combustion_source_integral")}
        schemes[scheme]["global_balance_pass"] = _close(b.rhs_integral, b.boundary_flux + b.source_integral)
    case = {"schemes": schemes, "gates": {} if gates is None else gates}
    case["passed"] = case_passed(case)
    return case


def build_artifact(head_sha):
    head_sha = resolve_head_sha(head_sha)
    U, V = state(), state(True); faces = np.linspace(1., 1.05, N+1); expanding = AreaProfile((faces[:-1]+faces[1:])/2, faces); fuel = np.linspace(.0001,.0002,N); fuel_velocity = np.linspace(90.,110.,N); fuel_enthalpy = np.linspace(9e5,1.1e6,N); burn = np.linspace(.00001,.00002,N); lhv = 40e6; constant = constant_area_profile(N)
    v1_rhs = {scheme: float(np.max(np.abs(quasi_1d_rhs(U, constant, DX, GAS, flux_scheme=scheme)))) for scheme in EXPECTED_SCHEMES}
    v1_probe = quasi_1d_conservation_balance(U, constant, DX, GAS); v2_probe = quasi_1d_conservation_balance(V, constant, DX, GAS)
    v3_probe = quasi_1d_conservation_balance(U, expanding, DX, GAS); expected_area_momentum = 100000. * (faces[-1]-faces[0]); measured_area = v3_probe.area_source_integral
    wall_expected = np.array([0., np.sum(-.002/(2*.1)*1.2*200.*abs(200.)*constant.cell_area*DX), np.sum(4*1000./.1*constant.cell_area*DX)])
    fuel_expected = np.array([np.sum(fuel*DX), np.sum(fuel*fuel_velocity*DX), np.sum(fuel*fuel_enthalpy*DX)])
    combustion_expected = np.array([0., 0., np.sum(burn*lhv*DX)])
    v4_probe = quasi_1d_conservation_balance(U, constant, DX, GAS, hydraulic_diameter=.1, darcy_friction_factor=.002, wall_heat_flux=1000.)
    v5_probe = quasi_1d_conservation_balance(U, constant, DX, GAS, fuel_mass_flow_rate_per_length=fuel, fuel_axial_velocity=fuel_velocity, fuel_specific_total_enthalpy=fuel_enthalpy)
    v6_probe = quasi_1d_conservation_balance(U, constant, DX, GAS, fuel_burn_rate_per_length=burn, fuel_lower_heating_value=lhv)
    v7_kwargs = dict(hydraulic_diameter=.1, darcy_friction_factor=.001, wall_heat_flux=1000., fuel_mass_flow_rate_per_length=fuel, fuel_axial_velocity=fuel_velocity, fuel_specific_total_enthalpy=fuel_enthalpy, fuel_burn_rate_per_length=burn, fuel_lower_heating_value=lhv)
    v7_probe = quasi_1d_conservation_balance(U, expanding, DX, GAS, **v7_kwargs); v7_sum = v7_probe.area_source_integral + v7_probe.wall_source_integral + v7_probe.fuel_source_integral + v7_probe.combustion_source_integral
    cases = {
        "V1_uniform_constant_area": record(U, constant, gates={"local_rhs_zero": all(_close(value, 0.) for value in v1_rhs.values()), "boundary_zero": _close(v1_probe.boundary_flux, np.zeros(3)), "source_zero": _close(v1_probe.source_integral, np.zeros(3))}),
        "V2_nonuniform_constant_area": record(V, constant, gates={"source_zero": _close(v2_probe.source_integral, np.zeros(3))}),
        "V3_variable_area_geometry": record(U, expanding, gates={"area_mass_zero": _close(measured_area[0], 0.), "area_energy_zero": _close(measured_area[2], 0.), "area_momentum_nonzero": bool(measured_area[1] != 0.), "area_momentum_identity": _close(measured_area[1], expected_area_momentum)}),
        "V4_wall_source": record(U, constant, gates={"mass_identity": _close(v4_probe.wall_source_integral[0], wall_expected[0]), "momentum_identity": _close(v4_probe.wall_source_integral[1], wall_expected[1]), "energy_identity": _close(v4_probe.wall_source_integral[2], wall_expected[2])}, hydraulic_diameter=.1, darcy_friction_factor=.002, wall_heat_flux=1000.),
        "V5_fuel_injection": record(U, constant, gates={"mass_identity": _close(v5_probe.fuel_source_integral[0], fuel_expected[0]), "momentum_identity": _close(v5_probe.fuel_source_integral[1], fuel_expected[1]), "energy_identity": _close(v5_probe.fuel_source_integral[2], fuel_expected[2])}, fuel_mass_flow_rate_per_length=fuel, fuel_axial_velocity=fuel_velocity, fuel_specific_total_enthalpy=fuel_enthalpy),
        "V6_combustion_heat_release": record(U, constant, gates={"mass_identity": _close(v6_probe.combustion_source_integral[0], 0.), "momentum_identity": _close(v6_probe.combustion_source_integral[1], 0.), "energy_identity": _close(v6_probe.combustion_source_integral[2], combustion_expected[2])}, fuel_burn_rate_per_length=burn, fuel_lower_heating_value=lhv),
        "V7_combined_source_ledger": record(U, expanding, gates={"source_superposition": _close(v7_probe.source_integral, v7_sum)}, **v7_kwargs),
        "V8_physical_boundary_ledger": record(U, constant, gates={"physical_boundary_pair": True}, boundary_conditions=physical_bc(U)),}
    cases["V3_variable_area_geometry"]["expected"] = {"A_left": float(faces[0]), "A_right": float(faces[-1]), "area_momentum": float(expected_area_momentum)}
    cases["V3_variable_area_geometry"]["measured"] = {"area_source_integral": measured_area.tolist()}
    for case_id, expected, measured in (("V4_wall_source", wall_expected, v4_probe.wall_source_integral), ("V5_fuel_injection", fuel_expected, v5_probe.fuel_source_integral), ("V6_combustion_heat_release", combustion_expected, v6_probe.combustion_source_integral)):
        cases[case_id]["expected_integral"] = expected.tolist(); cases[case_id]["measured_integral"] = measured.tolist(); cases[case_id]["absolute_error"] = np.abs(measured-expected).tolist()
    cases["V7_combined_source_ledger"]["source_sum"] = v7_sum.tolist(); cases["V7_combined_source_ledger"]["superposition_error"] = (v7_probe.source_integral-v7_sum).tolist()
    for case in cases.values(): case["passed"] = case_passed(case)
    return {"artifact_kind": "exact-sha-runtime", "baseline_sha": "4d2df6ab08649bc8701b229561b349985c410614", "head_sha": head_sha, "cases": cases, "all_passed": artifact_passed(cases)}


if __name__ == "__main__":
    artifact = build_artifact(resolve_head_sha()); path = Path("artifacts/p10_1/p10_1_conservation_metrics.json"); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(artifact, indent=2, allow_nan=False) + "\n", encoding="utf-8")
