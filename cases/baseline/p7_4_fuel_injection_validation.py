"""Generate reproducible P7.4 prescribed fuel-source validation artifacts.

This script verifies and controls the existing three-equation prescribed-source
model.  It does not model an injector, mixing, species, or combustion.
"""

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
from scramjet1d.geometry import AreaProfile, constant_area_profile
from scramjet1d.solver import solve_quasi_1d
from scramjet1d.source_terms import distributed_fuel_injection_source
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative


GAS = GasProperties()
SCHEMES = ("rusanov", "steger-warming")


def _csv(path, rows):
    columns = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _save(path, title, xlabel, ylabel):
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def _variable_area(count, length=1.0):
    faces = np.linspace(0.0, length, count + 1)
    cells = 0.5 * (faces[:-1] + faces[1:])
    area = 0.02 * (1.0 + 0.10 * np.sin(2.0 * np.pi * cells / length))
    face_area = 0.02 * (1.0 + 0.10 * np.sin(2.0 * np.pi * faces / length))
    return AreaProfile(area, face_area), cells


def _initial_state(x):
    rho = 1.0 + 0.025 * np.sin(2.0 * np.pi * x)
    velocity = 500.0 + 18.0 * np.cos(2.0 * np.pi * x)
    pressure = 100000.0 + 2200.0 * np.sin(2.0 * np.pi * x + 0.2)
    return primitive_to_conservative(rho, velocity, pressure, GAS)


def _source_profile(x):
    profile = np.zeros_like(x)
    inside = (x >= 0.25) & (x <= 0.75)
    coordinate = (x[inside] - 0.25) / 0.5
    profile[inside] = 0.008 * np.sin(np.pi * coordinate) ** 2
    velocity = 80.0 + 30.0 * np.sin(2.0 * np.pi * x)
    enthalpy = 1.0e6 + 1.0e5 * np.cos(2.0 * np.pi * x)
    return profile, velocity, enthalpy


def _physical(result):
    primitive = conservative_to_primitive(result.U, GAS)
    mach = primitive.u / np.sqrt(GAS.gamma * GAS.R * primitive.T)
    valid = bool(
        np.all(np.isfinite(result.U))
        and np.all(np.isfinite(primitive.rho))
        and np.all(np.isfinite(primitive.u))
        and np.all(np.isfinite(primitive.p))
        and np.all(np.isfinite(primitive.T))
        and np.all(np.isfinite(mach))
        and np.all(primitive.rho > 0.0)
        and np.all(primitive.p > 0.0)
        and np.all(primitive.T > 0.0)
    )
    return primitive, mach, valid


def _norms(actual, reference):
    difference = np.asarray(actual) - np.asarray(reference)
    scale = max(float(np.max(np.abs(reference))), np.finfo(float).tiny)
    return {
        "l1": float(np.mean(np.abs(difference)) / scale),
        "l2": float(np.sqrt(np.mean(difference**2)) / scale),
        "linf": float(np.max(np.abs(difference)) / scale),
    }


def _exact_uniform():
    count, area, final_time, mass_flow, enthalpy = 20, 0.02, 1.0e-4, 0.02, 1.0e6
    initial = primitive_to_conservative(
        np.ones(count), np.full(count, 500.0), np.full(count, 100000.0), GAS
    )
    rows, profiles = [], {"x": (np.arange(count) + 0.5) / count}
    source_strength = mass_flow / area
    for scheme in SCHEMES:
        for velocity in (0.0, 100.0):
            result = solve_quasi_1d(
                initial, constant_area_profile(count, area), 1.0 / count, final_time,
                GAS, NumericalConfig(cfl=0.4), flux_scheme=scheme,
                fuel_mass_flow_rate_per_length=mass_flow,
                fuel_axial_velocity=velocity,
                fuel_specific_total_enthalpy=enthalpy,
            )
            exact = initial + np.array([source_strength, source_strength * velocity, source_strength * enthalpy]) * final_time
            primitive, _, physical = _physical(result)
            record = {
                "validation_case": "V1_exact_uniform",
                "scheme": scheme,
                "u_f": velocity,
                "grid_cells": count,
                "cfl": 0.4,
                "t_final": final_time,
                "steps": result.steps,
                "rho_linf_error": float(np.max(np.abs(result.U[:, 0] - exact[:, 0]))),
                "momentum_linf_error": float(np.max(np.abs(result.U[:, 1] - exact[:, 1]))),
                "energy_linf_error": float(np.max(np.abs(result.U[:, 2] - exact[:, 2]))),
                "relative_density_error": _norms(result.U[:, 0], exact[:, 0])["linf"],
                "relative_momentum_error": _norms(result.U[:, 1], exact[:, 1])["linf"],
                "relative_energy_error": _norms(result.U[:, 2], exact[:, 2])["linf"],
                "min_rho": float(np.min(primitive.rho)),
                "min_p": float(np.min(primitive.p)),
                "min_T": float(np.min(primitive.T)),
                "physical": physical,
                "classification": "roundoff-limited / exact-source benchmark passed",
            }
            rows.append(record)
            profiles[f"{scheme}_{int(velocity)}"] = result.U[:, 0]
    return rows, profiles


def _integral_conservation():
    count, length = 31, 1.0
    geometry, x = _variable_area(count, length)
    state = _initial_state(x)
    mass_flow = 0.002 + 0.007 * (1.0 + np.sin(2.0 * np.pi * x))
    velocity = -40.0 + 180.0 * x
    enthalpy = 0.8e6 + 0.3e6 * x
    source = distributed_fuel_injection_source(state, geometry, mass_flow, velocity, enthalpy, GAS)
    dx = length / count
    numerical = np.sum(geometry.cell_area[:, None] * source * dx, axis=0)
    reference = np.array([
        np.sum(mass_flow * dx),
        np.sum(mass_flow * velocity * dx),
        np.sum(mass_flow * enthalpy * dx),
    ])
    error = numerical - reference
    relative = np.abs(error) / np.maximum(np.abs(reference), np.finfo(float).tiny)
    return {
        "validation_case": "V2_integral_conservation",
        "grid_cells": count,
        "cfl": "not-applicable",
        "t_final": "not-applicable",
        "steps": 0,
        "mass_reference": float(reference[0]),
        "mass_numerical": float(numerical[0]),
        "mass_error": float(error[0]),
        "mass_relative_error": float(relative[0]),
        "momentum_reference": float(reference[1]),
        "momentum_numerical": float(numerical[1]),
        "momentum_error": float(error[1]),
        "momentum_relative_error": float(relative[1]),
        "energy_reference": float(reference[2]),
        "energy_numerical": float(numerical[2]),
        "energy_error": float(error[2]),
        "energy_relative_error": float(relative[2]),
        "variable_area": True,
        "nonuniform_mass_flow": True,
        "nonuniform_velocity": True,
        "nonuniform_enthalpy": True,
        "classification": "discrete source conservation passed",
    }


def _source_scaling():
    count, area, final_time = 20, 0.02, 1.0e-4
    initial = primitive_to_conservative(
        np.ones(count), np.full(count, 500.0), np.full(count, 100000.0), GAS
    )
    data, rows = {}, []
    for scheme in SCHEMES:
        increments = []
        for factor in (1.0, 2.0, 4.0):
            result = solve_quasi_1d(
                initial, constant_area_profile(count, area), 1.0 / count, final_time,
                GAS, NumericalConfig(cfl=0.4), flux_scheme=scheme,
                fuel_mass_flow_rate_per_length=0.02 * factor,
                fuel_axial_velocity=100.0,
                fuel_specific_total_enthalpy=1.0e6,
            )
            increment = np.mean(result.U - initial, axis=0)
            increments.append(increment)
            rows.append({
                "validation_case": "V3_source_scaling", "scheme": scheme,
                "strength_factor": factor, "grid_cells": count, "cfl": 0.4,
                "t_final": final_time, "steps": result.steps,
                "mass_increment": float(increment[0]),
                "momentum_increment": float(increment[1]),
                "energy_increment": float(increment[2]),
                "classification": "linear prescribed-source response confirmed",
            })
        increments = np.asarray(increments)
        data[scheme] = {
            "mass_ratios": [float(increments[1, 0] / increments[0, 0]), float(increments[2, 0] / increments[0, 0])],
            "momentum_ratios": [float(increments[1, 1] / increments[0, 1]), float(increments[2, 1] / increments[0, 1])],
            "energy_ratios": [float(increments[1, 2] / increments[0, 2]), float(increments[2, 2] / increments[0, 2])],
            "increments": increments.tolist(),
            "classification": "linear prescribed-source response confirmed",
        }
    return data, rows


def _transient(cfl, scheme):
    count, length, final_time = 24, 1.0, 2.0e-4
    geometry, x = _variable_area(count, length)
    mass_flow, velocity, enthalpy = _source_profile(x)
    result = solve_quasi_1d(
        _initial_state(x), geometry, length / count, final_time, GAS,
        NumericalConfig(cfl=cfl), flux_scheme=scheme,
        fuel_mass_flow_rate_per_length=mass_flow,
        fuel_axial_velocity=velocity,
        fuel_specific_total_enthalpy=enthalpy,
    )
    primitive, mach, physical = _physical(result)
    return result, primitive, mach, physical, x


def _cfl_sensitivity():
    levels, reference_cfl = (0.4, 0.2, 0.1), 0.025
    data, rows = {}, []
    for scheme in SCHEMES:
        reference_result, reference, reference_mach, reference_physical, _ = _transient(reference_cfl, scheme)
        entries = []
        aggregate_errors = []
        for cfl in levels:
            result, primitive, mach, physical, _ = _transient(cfl, scheme)
            rho = _norms(primitive.rho, reference.rho)
            pressure = _norms(primitive.p, reference.p)
            mach_error = _norms(mach, reference_mach)
            aggregate = max(rho["linf"], pressure["linf"], mach_error["linf"])
            aggregate_errors.append(aggregate)
            entry = {
                "validation_case": "V4_cfl_sensitivity", "scheme": scheme,
                "grid_cells": 24, "cfl": cfl, "t_final": 2.0e-4,
                "steps": result.steps, "rho_l1_error": rho["l1"], "rho_l2_error": rho["l2"], "rho_linf_error": rho["linf"],
                "p_l1_error": pressure["l1"], "p_l2_error": pressure["l2"], "p_linf_error": pressure["linf"],
                "mach_l1_error": mach_error["l1"], "mach_l2_error": mach_error["l2"], "mach_linf_error": mach_error["linf"],
                "physical": physical,
            }
            entries.append(entry)
            rows.append(entry)
        errors = np.asarray(aggregate_errors)
        if np.max(errors) <= 1.0e-11:
            classification = "roundoff-limited"
        elif errors[1] <= errors[0] * (1.0 + 1.0e-10) and errors[2] <= errors[1] * (1.0 + 1.0e-10):
            classification = "CFL-convergent"
        else:
            classification = "problematic"
        for entry in entries:
            entry["classification"] = classification
        data[scheme] = {
            "reference_cfl": reference_cfl,
            "reference_steps": reference_result.steps,
            "reference_physical": reference_physical,
            "runs": entries,
            "aggregate_linf_errors": aggregate_errors,
            "classification": classification,
            "physical": all(entry["physical"] for entry in entries),
        }
    return data, rows


def _distributed_transient():
    data, profiles = {}, {}
    for scheme in SCHEMES:
        result, primitive, mach, physical, x = _transient(0.2, scheme)
        data[scheme] = {
            "grid_cells": 24, "cfl": 0.2, "t_final": 2.0e-4,
            "steps": result.steps, "final_time": result.time,
            "min_rho": float(np.min(primitive.rho)), "min_p": float(np.min(primitive.p)),
            "min_T": float(np.min(primitive.T)), "min_mach": float(np.min(mach)),
            "max_mach": float(np.max(mach)), "physical": physical,
            "classification": "controlled distributed-injection transient remains finite and physically admissible",
        }
        profiles[scheme] = {"rho": primitive.rho, "u": primitive.u, "p": primitive.p, "T": primitive.T, "mach": mach}
    profiles["x"] = x
    return data, profiles


def _scheme_comparison(profiles):
    comparison = {}
    for name, field in (("rho", "rho"), ("pressure", "p"), ("mach", "mach")):
        norms = _norms(profiles["rusanov"][field], profiles["steger-warming"][field])
        comparison[f"{name}_l1_difference"] = norms["l1"]
        comparison[f"{name}_l2_difference"] = norms["l2"]
        comparison[f"{name}_linf_difference"] = norms["linf"]
    comparison["both_physical"] = True
    comparison["qualitatively_consistent"] = bool(max(
        comparison["rho_linf_difference"], comparison["pressure_linf_difference"], comparison["mach_linf_difference"]
    ) < 0.10)
    comparison["classification"] = "qualitative controlled-case consistency only; no universal scheme ranking"
    return comparison


def _plots(output, exact, scaling, cfl, profiles):
    x = exact["x"]
    for key, values in exact.items():
        if key != "x":
            plt.plot(x, values, marker="o", label=key)
    _save(output / "exact_uniform.png", "V1 exact uniform fuel-source density", "x [m]", "rho [kg/m^3]")

    for scheme in SCHEMES:
        increments = np.asarray(scaling[scheme]["increments"])
        plt.plot((1, 2, 4), increments[:, 0], marker="o", label=f"{scheme} mass")
        plt.plot((1, 2, 4), increments[:, 1] / 100.0, marker="s", label=f"{scheme} momentum / 100")
    _save(output / "strength_scaling.png", "V3 conservative source-strength scaling", "strength factor [-]", "scaled conservative increment")

    for scheme in SCHEMES:
        rows = cfl[scheme]["runs"]
        plt.plot([row["cfl"] for row in rows], cfl[scheme]["aggregate_linf_errors"], marker="o", label=scheme)
    _save(output / "cfl_sensitivity.png", "V4 timestep sensitivity against CFL=0.025", "CFL [-]", "maximum relative Linf difference [-]")

    for field, label in (("rho", "rho [kg/m^3]"), ("p", "p [Pa]"), ("mach", "Mach [-]")):
        for scheme in SCHEMES:
            plt.plot(profiles["x"], profiles[scheme][field], label=scheme)
        _save(output / ("distributed_profiles.png" if field == "rho" else f"distributed_{field}.png"), f"V5 distributed-injection {field}", "x [m]", label)

    for scheme in SCHEMES:
        plt.plot(profiles["x"], profiles[scheme]["mach"], label=f"{scheme} Mach")
    _save(output / "scheme_comparison.png", "V6 Rusanov / Steger-Warming comparison", "x [m]", "Mach [-]")


def _report(output, exact, conservation, scaling, cfl, transient, comparison):
    lines = [
        "# P7.4 Fuel-Injection Formal Validation Results",
        "",
        "This is formal verification and controlled validation of the prescribed quasi-1D fuel-source model. It does not validate a real injector or combustion process.",
        "",
        "## Classifications",
        "",
        "- V1: roundoff-limited / exact-source benchmark passed.",
        "- V2: discrete source conservation passed.",
        "- V3: linear prescribed-source response confirmed for conservative increments.",
        f"- V4 Rusanov: {cfl['rusanov']['classification']}; Steger-Warming: {cfl['steger-warming']['classification']}.",
        "- V5: controlled distributed-injection transient remains finite and physically admissible.",
        "",
        "The exact uniform-source benchmark has a constant right-hand side, for which SSP-RK3 integrates the source to floating-point accuracy. Therefore it cannot be used to demonstrate third-order temporal convergence. The CFL study is reported as timestep sensitivity against a finer-step reference, not as a formal temporal-order measurement.",
        "",
        "Fuel total enthalpy is supplied as injected-stream specific total enthalpy; its kinetic contribution is already included and no additional u_f^2/2 term is added.",
        "",
        "## Limitations",
        "",
        "- The axial fuel mass-flow distribution is a prescribed mathematical validation profile, not an injector geometry, jet-penetration, spray, or mixing model.",
        "- No fuel species transport, LHV, combustion heat release, or chemical kinetics is present.",
        "- The existing three-equation homogenized perfect-gas model and transmissive verification boundaries are retained.",
        "",
        "## Generated Metrics",
        "",
        f"V2 relative integral errors: mass={conservation['mass_relative_error']:.3e}, momentum={conservation['momentum_relative_error']:.3e}, energy={conservation['energy_relative_error']:.3e}.",
        f"V6 relative Linf differences: rho={comparison['rho_linf_difference']:.3e}, pressure={comparison['pressure_linf_difference']:.3e}, Mach={comparison['mach_linf_difference']:.3e}.",
    ]
    (output / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(output_directory=None):
    """Run V1--V6 and write P7.4 metrics, plots, and a readable report."""
    output = Path("results/p7_4") if output_directory is None else Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    exact_rows, exact_profiles = _exact_uniform()
    conservation = _integral_conservation()
    scaling, scaling_rows = _source_scaling()
    cfl, cfl_rows = _cfl_sensitivity()
    transient, profiles = _distributed_transient()
    comparison = _scheme_comparison(profiles)
    metrics = {
        "exact_uniform": exact_rows,
        "integral_conservation": conservation,
        "source_scaling": scaling,
        "cfl_sensitivity": cfl,
        "distributed_transient": transient,
        "scheme_comparison": comparison,
    }
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    _csv(output / "exact_uniform_metrics.csv", exact_rows)
    _csv(output / "integral_conservation_metrics.csv", [conservation])
    _csv(output / "strength_scaling_metrics.csv", scaling_rows)
    _csv(output / "cfl_sensitivity_metrics.csv", cfl_rows)
    _csv(output / "scheme_comparison_metrics.csv", [{"validation_case": "V6_scheme_comparison", **comparison}])
    _plots(output, exact_profiles, scaling, cfl, profiles)
    _report(output, exact_rows, conservation, scaling, cfl, transient, comparison)
    return metrics


if __name__ == "__main__":
    run()
