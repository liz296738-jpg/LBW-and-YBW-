"""Generate a strict V1-V8 P10.1 conservation artifact."""
import json
import subprocess
from pathlib import Path
import numpy as np
from scramjet1d.boundary import BoundaryConditions
from scramjet1d.config import GasProperties
from scramjet1d.geometry import AreaProfile, constant_area_profile
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative
from scramjet1d.verification import quasi_1d_conservation_balance

EXPECTED_CASE_IDS = {"V1_uniform_constant_area", "V2_nonuniform_constant_area", "V3_variable_area_geometry", "V4_wall_source", "V5_fuel_injection", "V6_combustion_heat_release", "V7_combined_source_ledger", "V8_physical_boundary_ledger"}
EXPECTED_SCHEMES = {"rusanov", "steger-warming"}; GAS = GasProperties(); N = 8; DX = .1


def state(nonuniform=False):
    x = np.linspace(0., 1., N)
    rho = 1.2 + (.01*np.sin(x) if nonuniform else np.zeros(N)); velocity = 200. + (2*np.cos(x) if nonuniform else np.zeros(N)); pressure = 100000. + (100*np.sin(x) if nonuniform else np.zeros(N))
    return primitive_to_conservative(rho, velocity, pressure, GAS)


def physical_bc(U):
    q = conservative_to_primitive(U, GAS); beta = (GAS.gamma-1)/2
    return BoundaryConditions(inlet="subsonic-total-inflow", outlet="subsonic-pressure", inlet_total_pressure=float(q.p[0]*(1+beta*q.Mach[0]**2)**(GAS.gamma/(GAS.gamma-1))), inlet_total_temperature=float(q.T[0]*(1+beta*q.Mach[0]**2)), outlet_static_pressure=float(q.p[0]))


def record(U, geometry, **kwargs):
    schemes = {}
    for scheme in EXPECTED_SCHEMES:
        b = quasi_1d_conservation_balance(U, geometry, DX, GAS, flux_scheme=scheme, **kwargs)
        schemes[scheme] = {key: getattr(b, key).tolist() for key in ("rhs_integral", "boundary_flux", "source_integral", "closure_error", "area_source_integral", "wall_source_integral", "fuel_source_integral", "combustion_source_integral")}
        schemes[scheme]["passed"] = bool(np.allclose(b.closure_error, 0., rtol=0., atol=1e-8))
    return {"schemes": schemes, "passed": set(schemes) == EXPECTED_SCHEMES and all(v["passed"] for v in schemes.values())}


def build_artifact(head_sha):
    U, V = state(), state(True); faces = np.linspace(1., 1.05, N+1); expanding = AreaProfile((faces[:-1]+faces[1:])/2, faces); fuel = np.linspace(.0001,.0002,N); burn = np.linspace(.00001,.00002,N); constant = constant_area_profile(N)
    cases = {
        "V1_uniform_constant_area": record(U, constant), "V2_nonuniform_constant_area": record(V, constant), "V3_variable_area_geometry": record(U, expanding),
        "V4_wall_source": record(U, constant, hydraulic_diameter=.1, darcy_friction_factor=.002, wall_heat_flux=1000.),
        "V5_fuel_injection": record(U, constant, fuel_mass_flow_rate_per_length=fuel, fuel_axial_velocity=np.linspace(90.,110.,N), fuel_specific_total_enthalpy=np.linspace(9e5,1.1e6,N)),
        "V6_combustion_heat_release": record(U, constant, fuel_burn_rate_per_length=burn, fuel_lower_heating_value=40e6),
        "V7_combined_source_ledger": record(U, expanding, hydraulic_diameter=.1, darcy_friction_factor=.001, wall_heat_flux=1000., fuel_mass_flow_rate_per_length=fuel, fuel_axial_velocity=np.linspace(90.,110.,N), fuel_specific_total_enthalpy=np.linspace(9e5,1.1e6,N), fuel_burn_rate_per_length=burn, fuel_lower_heating_value=40e6),
        "V8_physical_boundary_ledger": record(U, constant, boundary_conditions=physical_bc(U)),}
    return {"baseline_sha": "4d2df6ab08649bc8701b229561b349985c410614", "head_sha": head_sha, "cases": cases, "all_passed": bool(set(cases) == EXPECTED_CASE_IDS and all(c["passed"] for c in cases.values()))}


if __name__ == "__main__":
    artifact = build_artifact(subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()); path = Path("artifacts/p10_1/p10_1_conservation_metrics.json"); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(artifact, indent=2, allow_nan=False) + "\n", encoding="utf-8")
