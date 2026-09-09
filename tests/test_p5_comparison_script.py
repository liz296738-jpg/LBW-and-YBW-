"""Integration test for the reproducible P5.4 comparison artifact generator."""

import json
from pathlib import Path
import runpy


def test_p5_comparison_script_writes_metrics_tables_and_plots(tmp_path: Path) -> None:
    script = Path(__file__).parents[1] / "cases" / "baseline" / "p5_flux_scheme_comparison.py"
    module = runpy.run_path(str(script))
    module["run"](tmp_path)

    metrics = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert set(metrics) == {"isentropic_residual", "smooth_entropy_wave", "contact", "sod", "near_sonic"}
    assert (tmp_path / "isentropic_residual_convergence.csv").is_file()
    assert (tmp_path / "entropy_wave_convergence.csv").is_file()
    for name in ("entropy_wave_comparison.png", "entropy_wave_convergence.png", "contact_comparison.png", "sod_density.png", "sod_pressure.png", "sod_mach.png", "isentropic_residual_convergence.png"):
        assert (tmp_path / name).is_file()
