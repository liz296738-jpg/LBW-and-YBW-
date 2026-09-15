from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "cases" / "studies" / "p11_2b_nasa_bk_thermo.py"
SOURCE_PATH = ROOT / "cases" / "studies" / "data" / "p11_2b_nasa_bk_thermo_reduction.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("p11_2b_nasa_bk_thermo", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reference_effective_gas_matches_tracked_derivation():
    module = _load_module()
    state = module.reference_effective_gas()

    assert state.temperature_K == pytest.approx(1270.0)
    assert state.R_J_per_kg_K == pytest.approx(329.4821420180208, rel=0.0, abs=1.0e-10)
    assert state.cp_J_per_kg_K == pytest.approx(1514.961402157982, rel=0.0, abs=1.0e-9)
    assert state.cv_J_per_kg_K == pytest.approx(1185.4792601399613, rel=0.0, abs=1.0e-9)
    assert state.gamma == pytest.approx(1.2779315953440815, rel=0.0, abs=1.0e-12)


def test_heated_range_sensitivity_recomputes_from_public_nasa7_coefficients():
    module = _load_module()
    result = module.validate_tracked_derivations()

    rows = {row["temperature_K"]: row for row in result["sensitivity"]}
    assert rows[2000.0]["gamma"] == pytest.approx(1.246731797999899, rel=0.0, abs=1.0e-12)
    assert rows[2500.0]["gamma"] == pytest.approx(1.235485697239657, rel=0.0, abs=1.0e-12)
    assert rows[3000.0]["gamma"] == pytest.approx(1.2283625235046551, rel=0.0, abs=1.0e-12)
    assert rows[3000.0]["gamma"] < rows[2000.0]["gamma"] < result["reference"].gamma
    assert "formal NASA-BK reduced-order result" in result["required_sensitivity"]


def test_nasa7_evaluator_rejects_invalid_inputs():
    module = _load_module()
    with pytest.raises(ValueError, match="five coefficients"):
        module.nasa7_cp_over_R([1.0, 2.0], 1270.0)
    with pytest.raises(ValueError, match="positive"):
        module.nasa7_cp_over_R([1.0] * 5, 0.0)


def test_temperature_outside_species_interval_is_rejected():
    module = _load_module()
    with pytest.raises(ValueError, match="outside"):
        module.mixture_state_at_temperature(900.0)
    with pytest.raises(ValueError, match="outside"):
        module.mixture_state_at_temperature(3600.0)


def test_tampered_reference_gamma_is_rejected(tmp_path: Path):
    module = _load_module()
    record = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    record["derived_reference_state"]["gamma_eff"] += 0.01
    tampered = tmp_path / "thermo.json"
    tampered.write_text(json.dumps(record), encoding="utf-8")

    with pytest.raises(ValueError, match="gamma_eff"):
        module.validate_tracked_derivations(tampered)


def test_tampered_mass_fraction_sum_is_rejected(tmp_path: Path):
    module = _load_module()
    record = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    record["composition_source"]["mass_fractions"]["N2"] = 0.40
    tampered = tmp_path / "thermo.json"
    tampered.write_text(json.dumps(record), encoding="utf-8")

    with pytest.raises(ValueError, match="sum to 1"):
        module.load_thermo_reduction(tampered)
