"""Integration test for the reproducible P6.4 validation artifact generator."""

import json
from pathlib import Path
import runpy


def test_p6_validation_script_writes_required_metrics_tables_and_plots(tmp_path: Path) -> None:
    script = Path(__file__).parents[1] / "cases" / "baseline" / "p6_wall_source_validation.py"
    module = runpy.run_path(str(script))
    module["run"](tmp_path)
    metrics = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert set(metrics) == {"exact_temporal", "fanno", "rayleigh", "source_cfl_sensitivity"}
    for name in ("uniform_source_cfl_convergence.csv", "fanno_residual_convergence.csv", "rayleigh_residual_convergence.csv", "source_strength_cfl.csv", "uniform_source_velocity.png", "uniform_source_cfl_convergence.png", "fanno_mach_profile.png", "fanno_residual_convergence.png", "rayleigh_mach_profile.png", "rayleigh_temperature_profile.png", "rayleigh_residual_convergence.png", "source_strength_cfl.png"):
        assert (tmp_path / name).is_file()
    assert set(metrics["source_cfl_sensitivity"]) == {"1x", "2x", "4x"}
    for scheme in ("rusanov", "steger-warming"):
        for branch in ("subsonic", "supersonic"):
            assert metrics["fanno"][scheme][branch]["classification"] in {"convergent", "superconvergent"}
            assert metrics["rayleigh"][scheme][branch]["classification"] != "failed"
            assert len(metrics["fanno"][scheme][branch]["mass_rms"]) == 3
            assert len(metrics["rayleigh"][scheme][branch]["energy_rms"]) == 3
