"""Generate reproducible P5.4 Rusanov/Steger-Warming comparison artifacts."""

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
from scramjet1d.isentropic import isentropic_nozzle_reference
from scramjet1d.solver import quasi_1d_rhs_transmissive, solve_quasi_1d
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative
from scramjet1d.verification import advected_contact_reference, l1_error, observed_order, smooth_entropy_wave_reference, transition_width_cells


GAS = GasProperties()
NUMERICAL = NumericalConfig()
SCHEMES = ("rusanov", "steger-warming")


def _state(rho: object, velocity: object, pressure: object) -> np.ndarray:
    return primitive_to_conservative(rho, velocity, pressure, GAS)


def _orders(errors: list[float]) -> list[float | None]:
    return [None] + [observed_order(errors[index - 1], errors[index]) for index in range(1, len(errors))]


def _write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _plot(path: Path, title: str, xlabel: str, ylabel: str) -> None:
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def _isentropic_case() -> tuple[dict[str, object], list[dict[str, object]]]:
    records: dict[str, object] = {}
    rows: list[dict[str, object]] = []
    for scheme in SCHEMES:
        branches: dict[str, object] = {}
        for branch, mach in (("subsonic", 0.5), ("supersonic", 2.0)):
            errors: list[float] = []
            counts = (80, 160, 320)
            for count in counts:
                face_area = np.linspace(1.0, 1.2, count + 1)
                geometry = AreaProfile(0.5 * (face_area[:-1] + face_area[1:]), face_area)
                reference = isentropic_nozzle_reference(geometry.cell_area, 1.0, mach, 300_000.0, 500.0, GAS, branch)
                residual = quasi_1d_rhs_transmissive(_state(reference.rho, reference.u, reference.p), geometry, 1.0 / count, GAS, flux_scheme=scheme)
                errors.append(float(np.sqrt(np.mean(residual[2:-2, 1] ** 2))))
            orders = _orders(errors)
            branches[branch] = {"N": list(counts), "rms_error": errors, "observed_order": orders}
            rows.extend({"scheme": scheme, "branch": branch, "N": count, "dx": 1.0 / count, "error": error, "order": "" if order is None else order} for count, error, order in zip(counts, errors, orders))
        records[scheme] = branches
    return records, rows


def _entropy_case() -> tuple[dict[str, object], list[dict[str, object]], dict[str, np.ndarray]]:
    counts = (80, 160, 320)
    final_time = 0.1 / 800.0
    records: dict[str, object] = {}
    rows: list[dict[str, object]] = []
    profiles: dict[str, np.ndarray] = {}
    for scheme in SCHEMES:
        errors: list[float] = []
        for count in counts:
            dx = 1.0 / count
            x = (np.arange(count) + 0.5) * dx
            initial = smooth_entropy_wave_reference(x, 0.0, 1.0, 800.0, 100_000.0, 0.1, 0.25, 0.05, GAS)
            result = solve_quasi_1d(_state(initial.rho, initial.u, initial.p), constant_area_profile(count), dx, final_time, GAS, NUMERICAL, flux_scheme=scheme)
            exact = smooth_entropy_wave_reference(x, result.time, 1.0, 800.0, 100_000.0, 0.1, 0.25, 0.05, GAS)
            primitive = conservative_to_primitive(result.U, GAS)
            errors.append(l1_error(primitive.rho, exact.rho))
            if count == counts[-1]:
                profiles[scheme] = primitive.rho
                profiles["x"] = x
                profiles["exact"] = exact.rho
        orders = _orders(errors)
        records[scheme] = {"N": list(counts), "density_l1": errors, "observed_order": orders}
        rows.extend({"scheme": scheme, "N": count, "dx": 1.0 / count, "error": error, "order": "" if order is None else order} for count, error, order in zip(counts, errors, orders))
    return records, rows, profiles


def _contact_case() -> tuple[dict[str, object], dict[str, np.ndarray]]:
    count, velocity, pressure, final_time = 200, 800.0, 100_000.0, 0.0002
    dx = 1.0 / count
    x = (np.arange(count) + 0.5) * dx
    initial = advected_contact_reference(x, 0.0, 1.0, 0.6, velocity, pressure, 0.3, GAS)
    exact = advected_contact_reference(x, final_time, 1.0, 0.6, velocity, pressure, 0.3, GAS)
    records: dict[str, object] = {"N": count, "final_time": final_time, "fully_right_going": bool(np.all(initial.u - np.sqrt(GAS.gamma * initial.p / initial.rho) > 0.0))}
    profiles: dict[str, np.ndarray] = {"x": x, "exact": exact.rho}
    for scheme in SCHEMES:
        result = solve_quasi_1d(_state(initial.rho, initial.u, initial.p), constant_area_profile(count), dx, final_time, GAS, NUMERICAL, flux_scheme=scheme)
        density = conservative_to_primitive(result.U, GAS).rho
        profiles[scheme] = density
        records[scheme] = {"density_l1": l1_error(density, exact.rho), "transition_width_cells": transition_width_cells(density, 1.0, 0.6)}
    return records, profiles


def _physical_metrics(state: np.ndarray) -> dict[str, float]:
    primitive = conservative_to_primitive(state, GAS)
    return {"min_rho": float(np.min(primitive.rho)), "max_rho": float(np.max(primitive.rho)), "min_p": float(np.min(primitive.p)), "max_p": float(np.max(primitive.p)), "min_T": float(np.min(primitive.T)), "max_mach": float(np.max(np.abs(primitive.Mach))), "rho_total_variation": float(np.sum(np.abs(np.diff(primitive.rho))))}


def _sod_case() -> tuple[dict[str, object], dict[str, np.ndarray]]:
    count, dx, final_time = 200, 1.0 / 200, 0.0004
    x = (np.arange(count) + 0.5) * dx
    initial = _state(np.where(x < 0.5, 1.0, 0.125), np.zeros(count), np.where(x < 0.5, 100_000.0, 10_000.0))
    records: dict[str, object] = {"N": count, "final_time": final_time}
    profiles: dict[str, np.ndarray] = {"x": x}
    for scheme in SCHEMES:
        result = solve_quasi_1d(initial, constant_area_profile(count), dx, final_time, GAS, NUMERICAL, flux_scheme=scheme)
        primitive = conservative_to_primitive(result.U, GAS)
        records[scheme] = {"reached_final_time": result.time == final_time, **_physical_metrics(result.U)}
        profiles[f"{scheme}_rho"] = primitive.rho
        profiles[f"{scheme}_p"] = primitive.p
        profiles[f"{scheme}_mach"] = primitive.Mach
    return records, profiles


def _near_sonic_case() -> dict[str, object]:
    count, dx, pressure, density, final_time = 100, 0.01, 100_000.0, 1.0, 3e-5
    sound_speed = np.sqrt(GAS.gamma * pressure / density)
    x = (np.arange(count) + 0.5) * dx
    records: dict[str, object] = {"N": count, "final_time": final_time}
    for mach in (0.95, 1.0, 1.05):
        initial = _state(np.full(count, density), np.full(count, mach * sound_speed), pressure * (1.0 + 0.002 * np.exp(-((x - 0.5) / 0.08) ** 2)))
        result = solve_quasi_1d(initial, constant_area_profile(count), dx, final_time, GAS, NUMERICAL, flux_scheme="steger-warming")
        metrics = _physical_metrics(result.U)
        records[str(mach)] = {"reached_final_time": result.time == final_time, **metrics}
    return records


def _plots(output: Path, isentropic: dict[str, object], entropy: dict[str, object], entropy_profiles: dict[str, np.ndarray], contact_profiles: dict[str, np.ndarray], sod_profiles: dict[str, np.ndarray]) -> None:
    for scheme in SCHEMES:
        for branch, style in (("subsonic", "-"), ("supersonic", "--")):
            record = isentropic[scheme][branch]
            plt.loglog(record["N"], record["rms_error"], style, marker="o", label=f"{scheme} {branch}")
    _plot(output / "isentropic_residual_convergence.png", "Isentropic residual convergence", "Cell count N [-]", "Interior momentum RMS [SI]")
    x = entropy_profiles["x"]
    plt.plot(x, entropy_profiles["exact"], "k--", label="exact")
    for scheme in SCHEMES:
        plt.plot(x, entropy_profiles[scheme], label=scheme)
    _plot(output / "entropy_wave_comparison.png", "Smooth entropy wave at final time", "x [m]", "Density [kg m$^{-3}$]")
    for scheme in SCHEMES:
        record = entropy[scheme]
        plt.loglog(record["N"], record["density_l1"], marker="o", label=scheme)
    _plot(output / "entropy_wave_convergence.png", "Entropy-wave density convergence", "Cell count N [-]", "Density L1 error [kg m$^{-3}$]")
    plt.plot(contact_profiles["x"], contact_profiles["exact"], "k--", label="exact")
    for scheme in SCHEMES:
        plt.plot(contact_profiles["x"], contact_profiles[scheme], label=scheme)
    _plot(output / "contact_comparison.png", "Supersonic contact comparison", "x [m]", "Density [kg m$^{-3}$]")
    for quantity, label, filename in (("rho", "Density [kg m$^{-3}$]", "sod_density.png"), ("p", "Pressure [Pa]", "sod_pressure.png"), ("mach", "Mach [-]", "sod_mach.png")):
        for scheme in SCHEMES:
            plt.plot(sod_profiles["x"], sod_profiles[f"{scheme}_{quantity}"], label=scheme)
        _plot(output / filename, f"Sod-type shock tube {quantity}", "x [m]", label)


def run(output_directory: Path | None = None) -> dict[str, object]:
    """Run all P5.4 controlled cases and write JSON, CSV, and PNG artifacts."""
    output = Path("results/p5_4") if output_directory is None else Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    isentropic, isentropic_rows = _isentropic_case()
    entropy, entropy_rows, entropy_profiles = _entropy_case()
    contact, contact_profiles = _contact_case()
    sod, sod_profiles = _sod_case()
    near_sonic = _near_sonic_case()
    metrics = {"isentropic_residual": isentropic, "smooth_entropy_wave": entropy, "contact": contact, "sod": sod, "near_sonic": near_sonic}
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    _write_csv(output / "isentropic_residual_convergence.csv", isentropic_rows, ["scheme", "branch", "N", "dx", "error", "order"])
    _write_csv(output / "entropy_wave_convergence.csv", entropy_rows, ["scheme", "N", "dx", "error", "order"])
    _plots(output, isentropic, entropy, entropy_profiles, contact_profiles, sod_profiles)
    return metrics


if __name__ == "__main__":
    run()
