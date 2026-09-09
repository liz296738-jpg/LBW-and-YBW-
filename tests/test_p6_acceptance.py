"""P6.4 hard gates calculated from live solver/reference evaluations."""

from pathlib import Path
import runpy

import numpy as np
from numpy.testing import assert_allclose

from scramjet1d.config import GasProperties
from scramjet1d.verification import fanno_flow_reference, rayleigh_flow_reference


GAS = GasProperties()


def _metrics(tmp_path: Path):
    module = runpy.run_path(str(Path(__file__).parents[1] / "cases" / "baseline" / "p6_wall_source_validation.py"))
    return module["run"](tmp_path)


def test_p6_exact_temporal_and_source_strength_hard_gates(tmp_path: Path) -> None:
    metrics = _metrics(tmp_path)
    for scheme in ("rusanov", "steger-warming"):
        exact = metrics["exact_temporal"][scheme]
        for record in exact["runs"]:
            assert record["density_error"] <= 1e-12
            assert record["energy_density_error"] <= 1e-5
            assert record["energy_increment_error"] <= 1e-5
            assert record["physical"]
        assert np.all(np.diff(exact["velocity_error"]) < 0.0)
        assert exact["temporal_order"][-1] >= 2.5
    for strength in ("1x", "2x", "4x"):
        for scheme in ("rusanov", "steger-warming"):
            record = metrics["source_cfl_sensitivity"][strength][scheme]
            assert record["physical"] and record["reached_t_final"]
            assert np.all(np.diff(record["velocity_error"]) < 0.0)
            assert record["temporal_order"][-1] >= 2.5


def test_p6_residual_classification_hard_gates(tmp_path: Path) -> None:
    metrics = _metrics(tmp_path)
    for scheme in ("rusanov", "steger-warming"):
        for branch in ("subsonic", "supersonic"):
            assert metrics["fanno"][scheme][branch]["classification"] in {"convergent", "superconvergent"}
            assert metrics["rayleigh"][scheme][branch]["classification"] != "failed"
    supersonic_sw = metrics["rayleigh"]["steger-warming"]["supersonic"]
    assert supersonic_sw["classification"] == "roundoff-limited" or supersonic_sw["primary_normalized_residual"] <= 1e-10


def test_p6_fanno_and_rayleigh_reference_invariants() -> None:
    fanno = fanno_flow_reference(np.linspace(0.0, 1.0, 31), 1.0, 100_000.0, 0.4, 0.1, 0.005, GAS, "subsonic")
    assert_allclose(fanno.rho * fanno.u, (fanno.rho * fanno.u)[0], rtol=1e-10)
    t0_fanno = fanno.T * (1.0 + 0.5 * (GAS.gamma - 1.0) * fanno.Mach**2)
    assert_allclose(t0_fanno, t0_fanno[0], rtol=1e-10)
    assert fanno.Mach[-1] > fanno.Mach[0]

    x, diameter, rho, pressure, mach, q_wall = np.linspace(0.0, 0.1, 31), 0.1, 1.0, 100_000.0, 0.4, 50_000.0
    rayleigh = rayleigh_flow_reference(x, rho, pressure, mach, diameter, q_wall, GAS, "subsonic")
    mass_flux = rayleigh.rho * rayleigh.u
    momentum_flux = rayleigh.rho * rayleigh.u**2 + rayleigh.p
    assert_allclose(mass_flux, mass_flux[0], rtol=1e-10)
    assert_allclose(momentum_flux, momentum_flux[0], rtol=1e-10)
    t0 = rayleigh.T * (1.0 + 0.5 * (GAS.gamma - 1.0) * rayleigh.Mach**2)
    cp = GAS.gamma * GAS.R / (GAS.gamma - 1.0)
    expected_slope = 4.0 * q_wall / (diameter * mass_flux[0] * cp)
    assert_allclose(np.diff(t0) / np.diff(x), expected_slope, rtol=1e-9, atol=1e-9)
