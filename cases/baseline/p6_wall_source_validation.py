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
from scramjet1d.source_terms import wall_friction_source, wall_heat_transfer_source
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative
from scramjet1d.verification import assess_residual_convergence, fanno_flow_reference, fanno_parameter, observed_order, rayleigh_flow_reference, rayleigh_t0_ratio, uniform_wall_source_reference

GAS = GasProperties()
SCHEMES = ("rusanov", "steger-warming")
COUNTS = (80, 160, 320)


def _state(rho, velocity, pressure):
    return primitive_to_conservative(rho, velocity, pressure, GAS)


def _rms(values):
    return float(np.sqrt(np.mean(np.asarray(values, dtype=float) ** 2)))


def _orders(errors):
    return [None] + [float(observed_order(errors[index - 1], errors[index])) for index in range(1, len(errors))]


def _csv(path, rows, columns):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _save(path, title, xlabel, ylabel, logarithmic=False):
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if logarithmic:
        plt.xscale("log")
        plt.yscale("log")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def _temporal_case():
    rho, velocity, pressure, diameter, friction, heat_flux, final_time = 1.0, 600.0, 100_000.0, 0.1, 0.04, 100_000.0, 0.002
    cfls = (0.4, 0.2, 0.1)
    initial = _state(np.full(12, rho), np.full(12, velocity), np.full(12, pressure))
    initial_energy = float(np.mean(initial[:, 2]))
    exact = uniform_wall_source_reference(rho, velocity, pressure, final_time, diameter, friction, heat_flux, GAS)
    data, rows, profiles = {}, [], {"x": (np.arange(12) + 0.5) / 12.0, "exact": np.full(12, exact.primitive.u)}
    for scheme in SCHEMES:
        runs = []
        velocity_errors = []
        for cfl in cfls:
            result = solve_quasi_1d(initial, constant_area_profile(12), 1.0 / 12.0, final_time, GAS, NumericalConfig(cfl=cfl), flux_scheme=scheme, hydraulic_diameter=diameter, darcy_friction_factor=friction, wall_heat_flux=heat_flux)
            primitive = conservative_to_primitive(result.U, GAS)
            actual_increment = float(np.mean(result.U[:, 2]) - initial_energy)
            expected_increment = float(4.0 * heat_flux * final_time / diameter)
            physical = bool(np.all(np.isfinite(result.U)) and np.all(primitive.rho > 0.0) and np.all(primitive.p > 0.0) and np.all(primitive.T > 0.0))
            run = {
                "CFL": cfl,
                "density_error": float(np.max(np.abs(primitive.rho - exact.primitive.rho))),
                "velocity_error": float(np.max(np.abs(primitive.u - exact.primitive.u))),
                "energy_density_error": float(np.max(np.abs(result.U[:, 2] - exact.U[2]))),
                "actual_energy_increment": actual_increment,
                "expected_energy_increment": expected_increment,
                "energy_increment_error": float(abs(actual_increment - expected_increment)),
                "pressure_min": float(np.min(primitive.p)),
                "temperature_min": float(np.min(primitive.T)),
                "physical": physical,
                "steps": result.steps,
            }
            runs.append(run)
            rows.append({"scheme": scheme, **run})
            velocity_errors.append(run["velocity_error"])
            if cfl == cfls[-1]:
                profiles[scheme] = primitive.u
        data[scheme] = {"CFL": list(cfls), "runs": runs, "velocity_error": velocity_errors, "temporal_order": _orders(velocity_errors)}
    return data, rows, profiles


def _fanno_case():
    data, rows, profiles = {}, [], {"x": None}
    length, diameter = 10.0, 0.1
    for scheme in SCHEMES:
        data[scheme] = {}
        for branch, inlet, outlet in (("subsonic", 0.4, 0.6), ("supersonic", 2.0, 1.5)):
            friction = float(diameter / length * (fanno_parameter(inlet, GAS) - fanno_parameter(outlet, GAS)))
            errors = [[], [], []]
            source_scale = None
            for count in COUNTS:
                x = (np.arange(count) + 0.5) * length / count
                reference = fanno_flow_reference(x, 1.0, 100_000.0, inlet, diameter, friction, GAS, branch)
                state = _state(reference.rho, reference.u, reference.p)
                rhs = quasi_1d_rhs_transmissive(state, constant_area_profile(count), length / count, GAS, flux_scheme=scheme, hydraulic_diameter=diameter, darcy_friction_factor=friction, wall_heat_flux=0.0)
                for component in range(3):
                    errors[component].append(_rms(rhs[4:-4, component]))
                source_scale = _rms(np.abs(wall_friction_source(state, diameter, friction, GAS)[4:-4, 1]))
                if count == COUNTS[-1]:
                    profiles["x"] = x
                    profiles[f"{scheme}_{branch}"] = reference.Mach
            assessment = assess_residual_convergence(errors[1], source_scale)
            orders = _orders(errors[1])
            data[scheme][branch] = {"N": list(COUNTS), "mass_rms": errors[0], "momentum_rms": errors[1], "energy_rms": errors[2], "primary_normalized_residual": assessment.normalized_finest_error, "observed_order": orders, "classification": assessment.classification, "darcy_friction_factor": friction}
            for count, mass, momentum, energy, order in zip(COUNTS, *errors, orders):
                rows.append({"scheme": scheme, "branch": branch, "N": count, "mass_rms": mass, "momentum_rms": momentum, "energy_rms": energy, "primary_normalized_residual": momentum / source_scale, "order": "" if order is None else order, "classification": assessment.classification})
    return data, rows, profiles


def _rayleigh_setup(inlet, outlet):
    length, diameter, pressure, temperature = 10.0, 0.1, 100_000.0, 300.0
    density = pressure / (GAS.R * temperature)
    t0 = temperature * (1.0 + 0.5 * (GAS.gamma - 1.0) * inlet**2)
    t0_star = t0 / rayleigh_t0_ratio(inlet, GAS)
    delta_t0 = t0_star * rayleigh_t0_ratio(outlet, GAS) - t0
    mass_flux = density * inlet * np.sqrt(GAS.gamma * GAS.R * temperature)
    cp = GAS.gamma * GAS.R / (GAS.gamma - 1.0)
    heat_flux = mass_flux * cp * diameter * delta_t0 / (4.0 * length)
    return length, diameter, density, pressure, heat_flux, mass_flux


def _rayleigh_case():
    data, rows, profiles = {}, [], {"x": None}
    for scheme in SCHEMES:
        data[scheme] = {}
        for branch, inlet, outlet in (("subsonic", 0.4, 0.6), ("supersonic", 2.0, 1.5)):
            length, diameter, density, pressure, heat_flux, mass_flux = _rayleigh_setup(inlet, outlet)
            errors = [[], [], []]
            source_scale = None
            slope_error = None
            for count in COUNTS:
                x = (np.arange(count) + 0.5) * length / count
                reference = rayleigh_flow_reference(x, density, pressure, inlet, diameter, heat_flux, GAS, branch)
                state = _state(reference.rho, reference.u, reference.p)
                rhs = quasi_1d_rhs_transmissive(state, constant_area_profile(count), length / count, GAS, flux_scheme=scheme, hydraulic_diameter=diameter, darcy_friction_factor=0.0, wall_heat_flux=heat_flux)
                for component in range(3):
                    errors[component].append(_rms(rhs[4:-4, component]))
                source_scale = _rms(np.abs(wall_heat_transfer_source(state, diameter, heat_flux, GAS)[4:-4, 2]))
                t0 = reference.T * (1.0 + 0.5 * (GAS.gamma - 1.0) * reference.Mach**2)
                expected_slope = 4.0 * heat_flux / (diameter * mass_flux * (GAS.gamma * GAS.R / (GAS.gamma - 1.0)))
                slope_error = float(np.max(np.abs(np.diff(t0) / np.diff(x) - expected_slope)))
                if count == COUNTS[-1]:
                    profiles["x"] = x
                    profiles[f"{scheme}_{branch}_mach"] = reference.Mach
                    profiles[f"{scheme}_{branch}_temperature"] = reference.T
            assessment = assess_residual_convergence(errors[2], source_scale)
            orders = _orders(errors[2])
            data[scheme][branch] = {"N": list(COUNTS), "mass_rms": errors[0], "momentum_rms": errors[1], "energy_rms": errors[2], "primary_normalized_residual": assessment.normalized_finest_error, "observed_order": orders, "classification": assessment.classification, "t0_slope_error": slope_error, "wall_heat_flux": float(heat_flux)}
            for count, mass, momentum, energy, order in zip(COUNTS, *errors, orders):
                rows.append({"scheme": scheme, "branch": branch, "N": count, "mass_rms": mass, "momentum_rms": momentum, "energy_rms": energy, "primary_normalized_residual": energy / source_scale, "order": "" if order is None else order, "classification": assessment.classification, "t0_slope_error": slope_error})
    return data, rows, profiles


def _sensitivity_case():
    initial = _state(np.full(12, 1.0), np.full(12, 600.0), np.full(12, 100_000.0))
    data, rows = {}, []
    for label, friction, heat_flux in (("1x", 0.02, 50_000.0), ("2x", 0.04, 100_000.0), ("4x", 0.08, 200_000.0)):
        exact = uniform_wall_source_reference(1.0, 600.0, 100_000.0, 0.002, 0.1, friction, heat_flux, GAS)
        data[label] = {}
        for scheme in SCHEMES:
            entries, errors = [], []
            for cfl in (0.5, 0.25, 0.125):
                result = solve_quasi_1d(initial, constant_area_profile(12), 1.0 / 12.0, 0.002, GAS, NumericalConfig(cfl=cfl), flux_scheme=scheme, hydraulic_diameter=0.1, darcy_friction_factor=friction, wall_heat_flux=heat_flux)
                primitive = conservative_to_primitive(result.U, GAS)
                error = float(np.max(np.abs(primitive.u - exact.primitive.u)))
                physical = bool(np.all(np.isfinite(result.U)) and np.all(primitive.rho > 0.0) and np.all(primitive.p > 0.0) and np.all(primitive.T > 0.0))
                entries.append({"strength": label, "scheme": scheme, "f_D": friction, "q_wall": heat_flux, "CFL": cfl, "exact_velocity_error": error, "physical": physical, "reached_t_final": bool(np.isclose(result.time, 0.002))})
                errors.append(error)
            orders = _orders(errors)
            data[label][scheme] = {"f_D": friction, "q_wall": heat_flux, "CFL": [0.5, 0.25, 0.125], "velocity_error": errors, "temporal_order": orders, "physical": all(row["physical"] for row in entries), "reached_t_final": all(row["reached_t_final"] for row in entries)}
            for row, order in zip(entries, orders):
                row["order"] = "" if order is None else order
                rows.append(row)
    return data, rows


def _plots(output, temporal, temporal_profiles, fanno, fanno_profiles, rayleigh, rayleigh_profiles, sensitivity_rows):
    plt.plot(temporal_profiles["x"], temporal_profiles["exact"], "k--", label="exact")
    for scheme in SCHEMES:
        plt.plot(temporal_profiles["x"], temporal_profiles[scheme], label=scheme)
    _save(output / "uniform_source_velocity.png", "Uniform wall-source velocity", "x [m]", "u [m/s]")
    for scheme in SCHEMES:
        plt.plot(temporal[scheme]["CFL"], temporal[scheme]["velocity_error"], marker="o", label=scheme)
    _save(output / "uniform_source_cfl_convergence.png", "Uniform source temporal convergence", "CFL [-]", "velocity error [m/s]", logarithmic=True)
    for scheme in SCHEMES:
        for branch in ("subsonic", "supersonic"):
            plt.plot(fanno_profiles["x"], fanno_profiles[f"{scheme}_{branch}"], label=f"{scheme} {branch}")
    _save(output / "fanno_mach_profile.png", "Fanno reference Mach profiles", "x [m]", "Mach [-]")
    for scheme in SCHEMES:
        for branch in ("subsonic", "supersonic"):
            plt.plot(COUNTS, fanno[scheme][branch]["momentum_rms"], marker="o", label=f"{scheme} {branch}")
    _save(output / "fanno_residual_convergence.png", "Fanno momentum residual", "N [-]", "RMS residual", logarithmic=True)
    for field, filename, ylabel in (("mach", "rayleigh_mach_profile.png", "Mach [-]"), ("temperature", "rayleigh_temperature_profile.png", "T [K]")):
        for scheme in SCHEMES:
            for branch in ("subsonic", "supersonic"):
                plt.plot(rayleigh_profiles["x"], rayleigh_profiles[f"{scheme}_{branch}_{field}"], label=f"{scheme} {branch}")
        _save(output / filename, f"Rayleigh reference {field}", "x [m]", ylabel)
    for scheme in SCHEMES:
        for branch in ("subsonic", "supersonic"):
            plt.plot(COUNTS, rayleigh[scheme][branch]["energy_rms"], marker="o", label=f"{scheme} {branch}")
    _save(output / "rayleigh_residual_convergence.png", "Rayleigh energy residual", "N [-]", "RMS residual", logarithmic=True)
    for label in ("1x", "2x", "4x"):
        for scheme in SCHEMES:
            rows = [row for row in sensitivity_rows if row["strength"] == label and row["scheme"] == scheme]
            plt.plot([row["CFL"] for row in rows], [row["exact_velocity_error"] for row in rows], marker="o", label=f"{label} {scheme}")
    _save(output / "source_strength_cfl.png", "Wall-source CFL sensitivity", "CFL [-]", "velocity error [m/s]", logarithmic=True)


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
    _csv(output / "uniform_source_cfl_convergence.csv", temporal_rows, ["scheme", "CFL", "density_error", "velocity_error", "energy_density_error", "actual_energy_increment", "expected_energy_increment", "energy_increment_error", "pressure_min", "temperature_min", "physical", "steps"])
    _csv(output / "fanno_residual_convergence.csv", fanno_rows, ["scheme", "branch", "N", "mass_rms", "momentum_rms", "energy_rms", "primary_normalized_residual", "order", "classification"])
    _csv(output / "rayleigh_residual_convergence.csv", rayleigh_rows, ["scheme", "branch", "N", "mass_rms", "momentum_rms", "energy_rms", "primary_normalized_residual", "order", "classification", "t0_slope_error"])
    _csv(output / "source_strength_cfl.csv", sensitivity_rows, ["strength", "scheme", "f_D", "q_wall", "CFL", "exact_velocity_error", "order", "physical", "reached_t_final"])
    _plots(output, temporal, temporal_profiles, fanno, fanno_profiles, rayleigh, rayleigh_profiles, sensitivity_rows)
    return metrics


if __name__ == "__main__":
    run()
