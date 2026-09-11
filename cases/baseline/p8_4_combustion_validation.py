"""Generate reproducible P8.4 prescribed-combustion validation artifacts."""

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
from scramjet1d.solver import quasi_1d_rhs_transmissive, solve_quasi_1d
from scramjet1d.source_terms import distributed_combustion_heat_release_source
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative


GAS = GasProperties()
SCHEMES = ("rusanov", "steger-warming")


def _state(n: int, x: np.ndarray | None = None) -> np.ndarray:
    if x is None:
        return primitive_to_conservative(np.ones(n), np.full(n, 500.0), np.full(n, 100_000.0), GAS)
    return primitive_to_conservative(
        1.0 + 0.04 * np.sin(2.0 * np.pi * x),
        500.0 + 20.0 * np.cos(2.0 * np.pi * x),
        100_000.0 * (1.0 + 0.03 * np.sin(2.0 * np.pi * x)),
        GAS,
    )


def _geometry(n: int) -> AreaProfile:
    faces = 0.02 * (1.0 + 0.12 * np.sin(2.0 * np.pi * np.linspace(0.0, 1.0, n + 1)))
    return AreaProfile(0.5 * (faces[:-1] + faces[1:]), faces)


def _burn_profile(x: np.ndarray, maximum: float = 3.0e-4) -> np.ndarray:
    profile = np.zeros_like(x)
    active = (x >= 0.25) & (x <= 0.75)
    profile[active] = maximum * np.sin(np.pi * (x[active] - 0.25) / 0.5) ** 2
    return profile


def _physical(U: np.ndarray) -> dict[str, float | bool]:
    primitive = conservative_to_primitive(U, GAS)
    return {
        "min_rho": float(np.min(primitive.rho)), "min_p": float(np.min(primitive.p)),
        "min_T": float(np.min(primitive.T)), "min_mach": float(np.min(primitive.Mach)),
        "max_mach": float(np.max(primitive.Mach)),
        "all_finite": bool(np.all(np.isfinite(U))),
        "physical": bool(np.all(primitive.rho > 0.0) and np.all(primitive.p > 0.0) and np.all(primitive.T > 0.0)),
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _plot(path: Path, title: str, xlabel: str, ylabel: str) -> None:
    plt.title(title); plt.xlabel(xlabel); plt.ylabel(ylabel); plt.legend(); plt.grid(True, alpha=0.3)
    plt.tight_layout(); plt.savefig(path, dpi=150); plt.close()


def _relative_metrics(values: np.ndarray, reference: np.ndarray) -> tuple[float, float, float]:
    scale = max(float(np.max(np.abs(reference))), 1.0e-14)
    delta = values - reference
    return float(np.mean(np.abs(delta)) / scale), float(np.sqrt(np.mean(delta**2)) / scale), float(np.max(np.abs(delta)) / scale)


def _uniform() -> tuple[dict[str, object], list[dict[str, object]], dict[str, np.ndarray]]:
    n, area, burn, lhv, final_time = 20, 0.02, 0.001, 40.0e6, 1.0e-4
    initial = _state(n); geometry = constant_area_profile(n, area); source = burn * lhv / area
    expected = initial + np.array([0.0, 0.0, source * final_time])
    rows, records, profiles = [], {}, {}
    for scheme in SCHEMES:
        result = solve_quasi_1d(initial, geometry, 1.0 / n, final_time, GAS, NumericalConfig(cfl=0.2), flux_scheme=scheme, fuel_burn_rate_per_length=burn, fuel_lower_heating_value=lhv)
        primitive, primitive0 = conservative_to_primitive(result.U, GAS), conservative_to_primitive(initial, GAS)
        record = {"rho_error": float(np.max(np.abs(result.U[:, 0] - expected[:, 0]))), "rhou_error": float(np.max(np.abs(result.U[:, 1] - expected[:, 1]))), "rhoE_error": float(np.max(np.abs(result.U[:, 2] - expected[:, 2]))), "u_error": float(np.max(np.abs(primitive.u - primitive0.u))), "p_ratio": float(np.mean(primitive.p / primitive0.p)), "T_ratio": float(np.mean(primitive.T / primitive0.T)), "steps": result.steps, **_physical(result.U)}
        records[scheme] = record; profiles[scheme] = result.U.copy(); rows.append({"scheme": scheme, **record})
    expected_energy = final_time * n * area * source / n
    measured_energy = float(np.sum((expected[:, 2] - initial[:, 2]) * area / n))
    profiles["x"] = (np.arange(n) + .5) / n; profiles["exact"] = expected
    return {"schemes": records, "domain_energy_expected": expected_energy, "domain_energy_measured": measured_energy, "domain_energy_relative_error": abs(measured_energy - expected_energy) / expected_energy}, rows, profiles


def _source_conservation() -> tuple[dict[str, float], list[dict[str, object]]]:
    n, dx = 31, 1.0 / 31
    x = (np.arange(n) + 0.5) * dx; geometry = _geometry(n); burn = _burn_profile(x, 0.001) + 0.0001; lhv = np.linspace(40.0e6, 44.0e6, n)
    source = distributed_combustion_heat_release_source(_state(n), geometry, burn, lhv, GAS)
    reference = float(np.sum(burn * lhv) * dx); actual = float(np.sum(geometry.cell_area * source[:, 2]) * dx)
    metrics = {"reference_power": reference, "source_power": actual, "absolute_error": abs(actual-reference), "relative_error": abs(actual-reference)/reference, "max_mass_source": float(np.max(np.abs(source[:, 0]))), "max_momentum_source": float(np.max(np.abs(source[:, 1])))}
    return metrics, [metrics]


def _wall_equivalence() -> tuple[dict[str, object], list[dict[str, object]]]:
    n, area, burn, lhv, diameter, final_time = 20, 0.02, 0.001, 40.0e6, 0.1, 1.0e-4
    qdot = burn * lhv / area; wall_flux = qdot * diameter / 4.0; initial = _state(n); geometry = constant_area_profile(n, area)
    records, rows = {}, []
    for scheme in SCHEMES:
        wall_rhs = quasi_1d_rhs_transmissive(initial, geometry, 1/n, GAS, flux_scheme=scheme, hydraulic_diameter=diameter, wall_heat_flux=wall_flux)
        comb_rhs = quasi_1d_rhs_transmissive(initial, geometry, 1/n, GAS, flux_scheme=scheme, fuel_burn_rate_per_length=burn, fuel_lower_heating_value=lhv)
        wall = solve_quasi_1d(initial, geometry, 1/n, final_time, GAS, NumericalConfig(cfl=.2), flux_scheme=scheme, hydraulic_diameter=diameter, wall_heat_flux=wall_flux)
        combustion = solve_quasi_1d(initial, geometry, 1/n, final_time, GAS, NumericalConfig(cfl=.2), flux_scheme=scheme, fuel_burn_rate_per_length=burn, fuel_lower_heating_value=lhv)
        record = {"rhs_difference": float(np.max(np.abs(wall_rhs-comb_rhs))), "final_state_difference": float(np.max(np.abs(wall.U-combustion.U)))}
        records[scheme] = record; rows.append({"scheme": scheme, **record})
    return {"schemes": records, "max_rhs_difference": max(r["rhs_difference"] for r in records.values()), "max_final_state_difference": max(r["final_state_difference"] for r in records.values())}, rows


def _strength_scaling() -> tuple[dict[str, object], list[dict[str, object]]]:
    n, area, base_burn, lhv, final_time = 20, .02, .0005, 40e6, 1e-4
    initial, geometry = _state(n), constant_area_profile(n, area); records, rows = {}, []
    for scheme in SCHEMES:
        increments = {}
        for factor in (1.0, 2.0, 4.0):
            result = solve_quasi_1d(initial, geometry, 1/n, final_time, GAS, NumericalConfig(cfl=.2), flux_scheme=scheme, fuel_burn_rate_per_length=factor*base_burn, fuel_lower_heating_value=lhv)
            increment = float(np.mean(result.U[:, 2] - initial[:, 2]))
            increments[str(factor)] = increment; rows.append({"scheme": scheme, "strength": factor, "energy_increment": increment, "ratio_to_1x": increment / increments["1.0"]})
        records[scheme] = increments
    errors = [abs(values["2.0"]/values["1.0"]-2.0) for values in records.values()] + [abs(values["4.0"]/values["1.0"]-4.0) for values in records.values()]
    return {"schemes": records, "max_scaling_error": max(errors)}, rows


def _smooth_case(scheme: str, cfl: float) -> tuple[object, np.ndarray, np.ndarray, AreaProfile, np.ndarray]:
    n, dx = 40, 1.0 / 40; x = (np.arange(n)+.5)*dx; geometry = _geometry(n); initial = _state(n, x); burn = _burn_profile(x)
    result = solve_quasi_1d(initial, geometry, dx, 2.0e-4, GAS, NumericalConfig(cfl=cfl), flux_scheme=scheme, fuel_burn_rate_per_length=burn, fuel_lower_heating_value=43.0e6)
    return result, x, initial, geometry, burn


def _cfl_sensitivity() -> tuple[dict[str, object], list[dict[str, object]]]:
    records, rows = {}, []
    for scheme in SCHEMES:
        reference = conservative_to_primitive(_smooth_case(scheme, .025)[0].U, GAS); scheme_records = {}
        for cfl in (.4, .2, .1):
            result = _smooth_case(scheme, cfl)[0]; primitive = conservative_to_primitive(result.U, GAS)
            values = {name: _relative_metrics(getattr(primitive, name), getattr(reference, name)) for name in ("rho", "u", "p", "T", "Mach")}
            record = {"steps": result.steps, **{f"{name}_{suffix}": metric for name, metrics in values.items() for suffix, metric in zip(("l1", "l2", "linf"), metrics)}}
            scheme_records[str(cfl)] = record; rows.append({"scheme": scheme, "cfl": cfl, **record})
        records[scheme] = scheme_records
    field_refinement = {scheme: {field: bool(records[scheme]["0.2"][f"{field}_linf"] <= records[scheme]["0.4"][f"{field}_linf"] + 1e-12 and records[scheme]["0.1"][f"{field}_linf"] <= records[scheme]["0.2"][f"{field}_linf"] + 1e-12) for field in ("rho", "u", "p", "T", "Mach")} for scheme in SCHEMES}
    good = all(passed for scheme in field_refinement.values() for passed in scheme.values())
    return {"schemes": records, "reference_cfl": .025, "field_refinement": field_refinement, "all_refinement_not_materially_worse": good}, rows


def _distributed_and_comparison() -> tuple[dict[str, object], dict[str, object], list[dict[str, object]], dict[str, np.ndarray]]:
    finals, physical, profiles = {}, {}, {}
    for scheme in SCHEMES:
        result, x, _, _, burn = _smooth_case(scheme, .2); primitive = conservative_to_primitive(result.U, GAS)
        finals[scheme] = primitive; physical[scheme] = {"steps": result.steps, "final_time": result.time, **_physical(result.U)}
        profiles[f"{scheme}_rho"], profiles[f"{scheme}_u"], profiles[f"{scheme}_p"], profiles[f"{scheme}_T"], profiles[f"{scheme}_Mach"] = primitive.rho, primitive.u, primitive.p, primitive.T, primitive.Mach
    profiles["x"], profiles["burn"] = x, burn
    comparison = {name: _relative_metrics(getattr(finals["rusanov"], name), getattr(finals["steger-warming"], name)) for name in ("rho", "u", "p", "T", "Mach")}
    rows = [{"scheme": scheme, **physical[scheme]} for scheme in SCHEMES]
    max_relative_linf = max(metric[2] for metric in comparison.values())
    return {"schemes": physical, "both_physical": all(v["physical"] and v["all_finite"] for v in physical.values())}, {"metrics": comparison, "both_physical": all(v["physical"] for v in physical.values()), "max_relative_linf": max_relative_linf, "qualitatively_consistent": max_relative_linf < .10}, rows, profiles


def _mixed() -> tuple[dict[str, object], list[dict[str, object]]]:
    n, dx = 20, .05; initial = _state(n); geometry = constant_area_profile(n, .02)
    values = [initial, geometry.cell_area, geometry.face_area, np.full(n,.002), np.full(n,100.), np.full(n,1e6), np.full(n,.0002), np.full(n,40e6), np.full(n,.1), np.full(n,.01), np.full(n,20000.)]
    originals = [np.array(value, copy=True) for value in values]; records, rows = {}, []
    for scheme in SCHEMES:
        result = solve_quasi_1d(initial, geometry, dx, 3e-4, GAS, NumericalConfig(cfl=.2), flux_scheme=scheme, hydraulic_diameter=values[8], darcy_friction_factor=values[9], wall_heat_flux=values[10], fuel_mass_flow_rate_per_length=values[3], fuel_axial_velocity=values[4], fuel_specific_total_enthalpy=values[5], fuel_burn_rate_per_length=values[6], fuel_lower_heating_value=values[7])
        records[scheme] = {"steps": result.steps, "final_time": result.time, **_physical(result.U)}; rows.append({"scheme": scheme, **records[scheme]})
    immutable = all(np.array_equal(value, original) for value, original in zip(values, originals))
    return {"schemes": records, "both_physical": all(v["physical"] and v["all_finite"] for v in records.values()), "inputs_immutable": immutable}, rows


def _plots(output: Path, uniform: dict[str, object], uniform_profiles: dict[str, np.ndarray], cfl: dict[str, object], profiles: dict[str, np.ndarray]) -> None:
    for scheme, record in uniform["schemes"].items(): plt.bar(scheme, record["rhoE_error"], label=scheme)
    _plot(output / "exact_uniform.png", "Exact uniform combustion energy error", "Scheme", "Maximum rhoE error")
    plt.plot(uniform_profiles["x"], uniform_profiles["exact"][:, 2], linewidth=2, label="analytical")
    for scheme in SCHEMES: plt.plot(uniform_profiles["x"], uniform_profiles[scheme][:, 2], marker="o", linestyle="none", label=scheme)
    _plot(output / "exact_uniform_energy.png", "Exact uniform combustion energy", "x [m]", "rhoE [J/m$^3$]")
    fields = ("rho", "rhou", "rhoE", "u")
    fig, axes = plt.subplots(2, 2, figsize=(8, 6))
    for axis, field in zip(axes.flat, fields):
        axis.bar(SCHEMES, [uniform["schemes"][scheme][f"{field}_error"] for scheme in SCHEMES])
        axis.set_title(f"{field} error"); axis.set_ylabel("maximum absolute error"); axis.grid(True, alpha=.3)
    fig.suptitle("Exact uniform combustion errors"); fig.tight_layout(); fig.savefig(output / "exact_uniform_error.png", dpi=150); plt.close(fig)
    for scheme in SCHEMES:
        data = cfl["schemes"][scheme]; plt.semilogy([.4,.2,.1], [data[str(level)]["p_linf"] for level in (.4,.2,.1)], marker="o", label=scheme)
    _plot(output / "cfl_sensitivity.png", "CFL sensitivity", "CFL", "Pressure relative Linf")
    for name, filename, label in (("rho", "rho", "Density [kg/m$^3$]"), ("u", "u", "Velocity [m/s]"), ("p", "p", "Pressure [Pa]"), ("T", "T", "Temperature [K]"), ("Mach", "mach", "Mach [-]")):
        for scheme in SCHEMES: plt.plot(profiles["x"], profiles[f"{scheme}_{name}"], label=scheme)
        _plot(output / f"distributed_{filename}.png", f"Distributed combustion {name}", "x [m]", label)
    plt.plot(profiles["x"], profiles["burn"], label="prescribed burn rate")
    _plot(output / "distributed_profiles.png", "Prescribed distributed combustion profile", "x [m]", "Burn rate [kg/(m s)]")


def run(output_directory: Path | None = None) -> dict[str, object]:
    """Run P8.4 controlled validations and write CSV, JSON, and PNG artifacts."""
    output = Path("results/p8_4") if output_directory is None else Path(output_directory); output.mkdir(parents=True, exist_ok=True)
    v1, uniform_rows, uniform_profiles = _uniform(); v2, source_rows = _source_conservation(); v3, wall_rows = _wall_equivalence(); v4, scaling_rows = _strength_scaling(); v5, cfl_rows = _cfl_sensitivity(); v6, v7, distributed_rows, profiles = _distributed_and_comparison(); v8, mixed_rows = _mixed()
    acceptance = {"v1": all(r["rho_error"] < 1e-12 and r["rhou_error"] < 1e-10 and r["rhoE_error"] < 1e-8 and r["u_error"] < 1e-12 and r["p_ratio"] > 1 and r["T_ratio"] > 1 and r["physical"] for r in v1["schemes"].values()), "v2": v2["relative_error"] < 1e-12 and v2["max_mass_source"] == 0 and v2["max_momentum_source"] == 0, "v3": v3["max_rhs_difference"] < 1e-9 and v3["max_final_state_difference"] < 1e-8, "v4": v4["max_scaling_error"] < 1e-10, "v5": v5["all_refinement_not_materially_worse"], "v6": v6["both_physical"], "v7": v7["both_physical"] and v7["qualitatively_consistent"], "v8": v8["both_physical"] and v8["inputs_immutable"]}
    acceptance["all_passed"] = all(acceptance.values())
    metrics = {"v1": v1, "v2": v2, "v3": v3, "v4": v4, "v5": v5, "v6": v6, "v7": v7, "v8": v8, "acceptance": acceptance}
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    for filename, rows in (("exact_uniform_metrics.csv", uniform_rows), ("source_conservation_metrics.csv", source_rows), ("wall_equivalence_metrics.csv", wall_rows), ("strength_scaling_metrics.csv", scaling_rows), ("cfl_sensitivity_metrics.csv", cfl_rows), ("scheme_comparison_metrics.csv", [{"quantity": k, "relative_l1": v[0], "relative_l2": v[1], "relative_linf": v[2]} for k,v in v7["metrics"].items()]), ("mixed_source_metrics.csv", mixed_rows)):
        _write_csv(output / filename, rows)
    _plots(output, v1, uniform_profiles, v5, profiles)
    return metrics


if __name__ == "__main__":
    run()
