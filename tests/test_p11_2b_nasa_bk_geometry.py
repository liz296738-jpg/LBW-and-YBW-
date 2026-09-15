from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "cases" / "studies" / "p11_2b_nasa_bk_geometry.py"
SOURCE_PATH = ROOT / "cases" / "studies" / "data" / "p11_2b_nasa_bk_geometry_source.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("p11_2b_nasa_bk_geometry", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_backed_geometry_values_and_area_ratio():
    module = _load_module()
    record = module.load_nasa_bk_geometry_source()
    geometry = module.nasa_bk_geometry()

    assert record["status"] == "GEOMETRY_FROZEN_SOURCE_BACKED"
    assert geometry.x_start_m == pytest.approx(0.0)
    assert geometry.x_exit_m == pytest.approx(0.356)
    assert geometry.length_m == pytest.approx(0.356)
    assert geometry.width_m == pytest.approx(0.051)
    assert geometry.height_start_m == pytest.approx(0.0938)
    assert geometry.height_exit_m == pytest.approx(0.1048)
    assert geometry.area_start_m2 == pytest.approx(0.0047838)
    assert geometry.area_exit_m2 == pytest.approx(0.0053448)
    assert geometry.area_ratio == pytest.approx(1.1172707889125801)


def test_height_and_area_are_linear_and_exact_at_endpoints():
    module = _load_module()
    geometry = module.nasa_bk_geometry()

    x = np.array([0.0, 0.178, 0.356])
    height = geometry.height(x)
    area = geometry.area(x)

    assert height[0] == pytest.approx(0.0938)
    assert height[1] == pytest.approx((0.0938 + 0.1048) / 2.0)
    assert height[2] == pytest.approx(0.1048)
    assert area[0] == pytest.approx(0.0047838)
    assert area[2] == pytest.approx(0.0053448)
    assert np.all(np.diff(height) > 0.0)
    assert np.all(np.diff(area) > 0.0)


def test_uniform_mesh_sampling_preserves_source_face_endpoints():
    module = _load_module()
    sampled = module.sample_cell_and_face_areas(20)

    assert sampled["x_face_m"].shape == (21,)
    assert sampled["x_cell_m"].shape == (20,)
    assert sampled["area_face_m2"].shape == (21,)
    assert sampled["area_cell_m2"].shape == (20,)
    assert sampled["x_face_m"][0] == pytest.approx(0.0)
    assert sampled["x_face_m"][-1] == pytest.approx(0.356)
    assert sampled["area_face_m2"][0] == pytest.approx(0.0047838)
    assert sampled["area_face_m2"][-1] == pytest.approx(0.0053448)
    assert np.all(sampled["area_face_m2"] > 0.0)
    assert np.all(sampled["area_cell_m2"] > 0.0)


def test_geometry_rejects_points_outside_source_domain():
    module = _load_module()
    geometry = module.nasa_bk_geometry()

    with pytest.raises(ValueError, match="outside"):
        geometry.area(np.array([-1.0e-4, 0.1]))
    with pytest.raises(ValueError, match="outside"):
        geometry.height(np.array([0.1, 0.357]))


def test_mesh_sampling_rejects_invalid_cell_count():
    module = _load_module()
    for value in (1, 0, -1, 2.0, True):
        with pytest.raises(ValueError, match="integer >= 2"):
            module.sample_cell_and_face_areas(value)


def test_tampered_derived_area_is_rejected(tmp_path: Path):
    module = _load_module()
    record = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    record["derived_geometry"]["area_exit_m2"] += 1.0e-5
    tampered = tmp_path / "geometry.json"
    tampered.write_text(json.dumps(record), encoding="utf-8")

    with pytest.raises(ValueError, match="area_exit_m2"):
        module.load_nasa_bk_geometry_source(tampered)
