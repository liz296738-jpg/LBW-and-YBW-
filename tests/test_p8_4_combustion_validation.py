"""Hard gates for reproducible P8.4 prescribed-combustion validation."""

import importlib.util
from pathlib import Path


def _validation_module():
    path = Path(__file__).parents[1] / "cases" / "baseline" / "p8_4_combustion_validation.py"
    spec = importlib.util.spec_from_file_location("p8_4_validation", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_p8_4_validation_hard_gates_and_artifacts(tmp_path) -> None:
    """Catch broken P8 source mapping, integration, or reproducibility artifacts."""
    metrics = _validation_module().run(tmp_path)

    assert metrics["acceptance"]["all_passed"]
    assert metrics["v1"]["domain_energy_relative_error"] < 1.0e-12
    assert metrics["v2"]["relative_error"] < 1.0e-12
    assert metrics["v2"]["max_mass_source"] == 0.0
    assert metrics["v2"]["max_momentum_source"] == 0.0
    assert metrics["v3"]["max_rhs_difference"] < 1.0e-9
    assert metrics["v3"]["max_final_state_difference"] < 1.0e-8
    assert metrics["v4"]["max_scaling_error"] < 1.0e-10
    assert metrics["v5"]["all_refinement_not_materially_worse"]
    assert metrics["v6"]["both_physical"]
    assert metrics["v7"]["both_physical"]
    assert metrics["v8"]["both_physical"] and metrics["v8"]["inputs_immutable"]

    for filename in (
        "metrics.json",
        "exact_uniform_metrics.csv",
        "source_conservation_metrics.csv",
        "wall_equivalence_metrics.csv",
        "strength_scaling_metrics.csv",
        "cfl_sensitivity_metrics.csv",
        "scheme_comparison_metrics.csv",
        "mixed_source_metrics.csv",
        "exact_uniform.png",
        "cfl_sensitivity.png",
        "distributed_profiles.png",
    ):
        artifact = tmp_path / filename
        assert artifact.is_file() and artifact.stat().st_size > 0
