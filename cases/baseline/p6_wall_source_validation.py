"""Generate reproducible P6.4 wall-source validation metrics and plots."""

import csv
import json
from pathlib import Path
import sys

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.geometry import constant_area_profile
from scramjet1d.solver import quasi_1d_rhs_transmissive, solve_quasi_1d
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative
from scramjet1d.verification import fanno_flow_reference, fanno_parameter, observed_order, rayleigh_flow_reference, rayleigh_t0_ratio, uniform_wall_source_reference


GAS = GasProperties()
SCHEMES = ("rusanov", "steger-warming")
COUNTS = (80, 160, 320)


def _state(rho, velocity, pressure):
    return primitive_to_conservative(rho, velocity, pressure, GAS)


def _orders(errors):
    return [None] + [float(observed_order(errors[i - 1], errors[i])) for i in range(1, len(errors))]


def _csv(path, rows, columns):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _save(path, title, xlabel, ylabel):
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def _temporal_case():
    rho, velocity, pressure, diameter, friction, heat_flux, final_time = 1.0, 600.0, 100_000.0, 0.1, 0.04, 100_000.0, 0.002
    initial = _state(np.full(12, rho), np.full(12, velocity), np.full(12, pressure))
    exact = uniform_wall_source_reference(rho, velocity, pressure, final_time, diameter, friction, heat_flux, GAS)
    records, rows, profiles = {}, [], {}
    for scheme in SCHEMES:
        velocity_errors, energy_errors = [], []
        for cfl in (0.4, 0.2, 0.1):
            result = solve_quasi_1d(initial, constant_area_profile(12), 1.0 / 12.0, final_time, GAS, NumericalConfig(cfl=cfl), flux_scheme=scheme, hydraulic_diameter=diameter, darcy_friction_factor=friction, wall_heat_flux=heat_flux)
            primitive = conservative_to_primitive(result.U, GAS)
            velocity_errors.append(float(abs(np.mean(primitive.u) - exact.primitive.u)))
            energy_errors.append(float(abs(np.mean(result.U[:, 2]) - exact.U[2])))
            rows.append({"scheme": scheme, "CFL": cfl, "velocity_error": velocity_errors[-1], "energy_error": energy_errors[-1], "steps": result.steps})
            if cfl == 0.1:
                profiles[scheme] = primitive.u
        records[scheme] = {"CFL": [0.4, 0.2, 0.1], "velocity_error": velocity_errors, "energy_error": energy_errors, "temporal_order": _orders(velocity_errors), "rho_exact": True, "energy_increment_exact": float(4.0 * heat_flux * final_time / diameter)}
    profiles["x"] = (np.arange(12) + 0.5) / 12.0
    profiles["exact"] = np.full(12, exact.primitive.u)
    return records, rows, profiles


def _fanno_case():
    records, rows, profiles = {}, [], {}
    length, diameter = 10.0, 0.1
    for scheme in SCHEMES:
        records[scheme] = {}
        for branch, inlet, outlet in (("subsonic", 0.4, 0.6), ("supersonic", 2.0, 1.5)):
            friction = float(diameter / length * (fanno_parameter(inlet, GAS) - fanno_parameter(outlet, GAS)))
            errors = []
            for count in COUNTS:
                x = (np.arange(count) + 0.5) * length / count
                reference = fanno_flow_reference(x, 1.0, 100_000.0, inlet, diameter, friction, GAS, branch)
                rhs = quasi_1d_rhs_transmissive(_state(reference.rho, reference.u, reference.p), constant_area_profile(count), length / count, GAS, flux_scheme=scheme, hydraulic_diameter=diameter, darcy_friction_factor=friction, wall_heat_flux=0.0)
                errors.append(float(np.sqrt(np.mean(rhs[4:-4, 1] ** 2))))
                if count == 320:
                    profiles[f"{scheme}_{branch}"] = reference.Mach
                    profiles["x"] = x
            orders = _orders(errors)
            records[scheme][branch] = {"N": list(COUNTS), "momentum_rms": errors, "observed_order": orders, "darcy_friction_factor": friction}
            rows.extend({"scheme": scheme, "branch": branch, "N": n, "error": e, "order": "" if o is None else o} for n, e, o in zip(COUNTS, errors, orders))
    return records, rows, profiles


def _rayleigh_setup(inlet, outlet):
    length, diameter, pressure, temperature = 10.0, 0.1, 100_000.0, 300.0
    density = pressure / (GAS.R * temperature)
    t0 = temperature * (1.0 + (GAS.gamma - 1.0) * inlet**2 / 2.0)
    t0_star = t0 / rayleigh_t0_ratio(inlet, GAS)
    delta_t0 = t0_star * rayleigh_t0_ratio(outlet, GAS) - t0
    mass_flux = density * inlet * np.sqrt(GAS.gamma * GAS.R * temperature)
    cp = GAS.gamma * GAS.R / (GAS.gamma - 1.0)
    heat_flux = mass_flux * cp * diameter * delta_t0 / (4.0 * length)
    return length, diameter, density, pressure, heat_flux


def _rayleigh_case():
    records, rows, profiles = {}, [], {}
    for scheme in SCHEMES:
        records[scheme] = {}
        for branch, inlet, outlet in (("subsonic", 0.4, 0.6), ("supersonic", 2.0, 1.5)):
            length, diameter, density, pressure, heat_flux = _rayleigh_setup(inlet, outlet)
            errors = []
            for count in COUNTS:
                x = (np.arange(count) + 0.5) * length / count
                reference = rayleigh_flow_reference(x, density, pressure, inlet, diameter, heat_flux, GAS, branch)
                rhs = quasi_1d_rhs_transmissive(_state(reference.rho, reference.u, reference.p), constant_area_profile(count), length / count, GAS, flux_scheme=scheme, hydraulic_diameter=diameter, darcy_friction_factor=0.0, wall_heat_flux=heat_flux)
                errors.append(float(np.sqrt(np.mean(rhs[4:-4, 2] ** 2))))
                if count == 320:
                    profiles[f"{scheme}_{branch}_mach"] = reference.Mach
                    profiles[f"{scheme}_{branch}_temperature"] = reference.T
                    profiles["x"] = x
            orders = _orders(errors)
            records[scheme][branch] = {"N": list(COUNTS), "energy_rms": errors, "observed_order": orders, "wall_heat_flux": float(heat_flux)}
            rows.extend({"scheme": scheme, "branch": branch, "N": n, "error": e, "order": "" if o is None else o} for n, e, o in zip(COUNTS, errors, orders))
    return records, rows, profiles


def _sensitivity_case():
    records, rows = {}, []
    initial = _state(np.full(12, 1.0), np.full(12, 600.0), np.full(12, 100_000.0))
    for label, friction, heat_flux in (("mild", 0.02, 50_000.0), ("moderate", 0.04, 100_000.0)):
        exact = uniform_wall_source_reference(1.0, 600.0, 100_000.0, 0.002, 0.1, friction, heat_flux, GAS)
        records[label] = {}
        for cfl in (0.5, 0.25):
            result = solve_quasi_1d(initial, constant_area_profile(12), 1.0 / 12.0, 0.002, GAS, NumericalConfig(cfl=cfl), hydraulic_diameter=0.1, darcy_friction_factor=friction, wall_heat_flux=heat_flux)
            primitive = conservative_to_primitive(result.U, GAS)
            error = float(abs(np.mean(primitive.u) - exact.primitive.u))
            physical = bool(np.all(primitive.rho > 0.0) and np.all(primitive.p > 0.0) and np.all(primitive.T > 0.0))
            records[label][str(cfl)] = {"exact_velocity_error": error, "physical": physical, "reached_t_final": result.time == 0.002}
            rows.append({"strength": label, "CFL": cfl, "exact_error": error, "physical": physical, "reached_t_final": result.time == 0.002})
    return records, rows


def _plots(output, temporal, temporal_profiles, fanno, fanno_profiles, rayleigh, rayleigh_profiles, sensitivity_rows):
    plt.plot(temporal_profiles["x"], temporal_profiles["exact"], "k--", label="exact")
    for scheme in SCHEMES: plt.plot(temporal_profiles["x"], temporal_profiles[scheme], label=scheme)
    _save(output / "uniform_source_velocity.png", "Uniform wall-source velocity", "x [m]", "Velocity [m/s]")
    for scheme in SCHEMES: plt.loglog(temporal[scheme]["CFL"], temporal[scheme]["velocity_error"], marker="o", label=scheme)
    _save(output / "uniform_source_cfl_convergence.png", "Uniform source temporal convergence", "CFL [-]", "Velocity error [m/s]")
    for scheme in SCHEMES:
        for branch in ("subsonic", "supersonic"): plt.plot(fanno_profiles["x"], fanno_profiles[f"{scheme}_{branch}"], label=f"{scheme} {branch}")
    _save(output / "fanno_mach_profile.png", "Fanno reference Mach profiles", "x [m]", "Mach [-]")
    for scheme in SCHEMES:
        for branch in ("subsonic", "supersonic"): plt.loglog(COUNTS, fanno[scheme][branch]["momentum_rms"], marker="o", label=f"{scheme} {branch}")
    _save(output / "fanno_residual_convergence.png", "Fanno momentum residual", "Cell count N [-]", "RMS residual [SI]")
    for field, filename, ylabel in (("mach", "rayleigh_mach_profile.png", "Mach [-]"), ("temperature", "rayleigh_temperature_profile.png", "Temperature [K]")):
        for scheme in SCHEMES:
            for branch in ("subsonic", "supersonic"): plt.plot(rayleigh_profiles["x"], rayleigh_profiles[f"{scheme}_{branch}_{field}"], label=f"{scheme} {branch}")
        _save(output / filename, f"Rayleigh reference {field}", "x [m]", ylabel)
    for scheme in SCHEMES:
        for branch in ("subsonic", "supersonic"): plt.loglog(COUNTS, rayleigh[scheme][branch]["energy_rms"], marker="o", label=f"{scheme} {branch}")
    _save(output / "rayleigh_residual_convergence.png", "Rayleigh energy residual", "Cell count N [-]", "RMS residual [W/m³]")
    for label in ("mild", "moderate"):
        rows = [row for row in sensitivity_rows if row["strength"] == label]
        plt.plot([row["CFL"] for row in rows], [row["exact_error"] for row in rows], marker="o", label=label)
    _save(output / "source_strength_cfl.png", "Wall-source CFL sensitivity", "CFL [-]", "Exact velocity error [m/s]")


def run(output_directory=None):
    """Run P6.4 controlled references and write reproducible validation artifacts."""
    output = Path("results/p6_4") if output_directory is None else Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    temporal, temporal_rows, temporal_profiles = _temporal_case()
    fanno, fanno_rows, fanno_profiles = _fanno_case()
    rayleigh, rayleigh_rows, rayleigh_profiles = _rayleigh_case()
    sensitivity, sensitivity_rows = _sensitivity_case()
    metrics = {"exact_temporal": temporal, "fanno": fanno, "rayleigh": rayleigh, "source_cfl_sensitivity": sensitivity}
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    _csv(output / "uniform_source_cfl_convergence.csv", temporal_rows, ["scheme", "CFL", "velocity_error", "energy_error", "steps"])
    _csv(output / "fanno_residual_convergence.csv", fanno_rows, ["scheme", "branch", "N", "error", "order"])
    _csv(output / "rayleigh_residual_convergence.csv", rayleigh_rows, ["scheme", "branch", "N", "error", "order"])
    _csv(output / "source_strength_cfl.csv", sensitivity_rows, ["strength", "CFL", "exact_error", "physical", "reached_t_final"])
    _plots(output, temporal, temporal_profiles, fanno, fanno_profiles, rayleigh, rayleigh_profiles, sensitivity_rows)
    return metrics


if __name__ == "__main__":
    run()
