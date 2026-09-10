"""Hard gates for reproducible P7.4 prescribed-fuel validation."""

from pathlib import Path
import runpy

import numpy as np


def _metrics(tmp_path: Path):
    script = Path(__file__).parents[1] / "cases" / "baseline" / "p7_4_fuel_injection_validation.py"
    module = runpy.run_path(str(script))
    return module["run"](tmp_path)


def test_p7_4_validation_generates_required_artifacts_and_hard_gate_metrics(tmp_path: Path) -> None:
    """Catch a missing validation case, artifact, or prescribed-source invariant."""
    metrics = _metrics(tmp_path)

    assert set(metrics) == {
        "exact_uniform",
        "integral_conservation",
        "source_scaling",
        "cfl_sensitivity",
        "distributed_transient",
        "scheme_comparison",
    }
    for filename in (
        "exact_uniform_metrics.csv",
        "integral_conservation_metrics.csv",
        "strength_scaling_metrics.csv",
        "cfl_sensitivity_metrics.csv",
        "scheme_comparison_metrics.csv",
        "exact_uniform.png",
        "strength_scaling.png",
        "cfl_sensitivity.png",
        "distributed_profiles.png",
        "scheme_comparison.png",
        "validation_report.md",
    ):
        assert (tmp_path / filename).is_file()

    for record in metrics["exact_uniform"]:
        assert record["rho_linf_error"] <= 1.0e-11
        assert record["momentum_linf_error"] <= 1.0e-8
        assert record["energy_linf_error"] <= 1.0e-5
        assert record["physical"]

    conservation = metrics["integral_conservation"]
    assert conservation["mass_relative_error"] <= 1.0e-12
    assert conservation["momentum_relative_error"] <= 1.0e-12
    assert conservation["energy_relative_error"] <= 1.0e-12

    for scheme in ("rusanov", "steger-warming"):
        scaling = metrics["source_scaling"][scheme]
        assert np.allclose(scaling["mass_ratios"], [2.0, 4.0], rtol=1.0e-11, atol=1.0e-12)
        assert np.allclose(scaling["momentum_ratios"], [2.0, 4.0], rtol=1.0e-11, atol=1.0e-12)
        assert np.allclose(scaling["energy_ratios"], [2.0, 4.0], rtol=1.0e-11, atol=1.0e-12)
        cfl = metrics["cfl_sensitivity"][scheme]
        assert cfl["classification"] in {"CFL-convergent", "roundoff-limited"}
        assert cfl["reference_physical"]
        assert cfl["physical"]
        transient = metrics["distributed_transient"][scheme]
        assert transient["steps"] > 1
        assert transient["physical"]

    comparison = metrics["scheme_comparison"]
    assert comparison["both_physical"]
    assert comparison["qualitatively_consistent"]
