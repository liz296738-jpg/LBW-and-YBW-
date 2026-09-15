"""Fast deterministic tests for the P11.2A public-surrogate study layer."""

import json
from pathlib import Path

import numpy as np
import pytest

from scramjet1d.config import GasProperties

from cases.studies.p11_2a_public_surrogate import (
    CASE_ID_BASELINE,
    SOURCE_PATH,
    build_case,
    build_public_surrogate_geometry,
    load_public_surrogate_source,
    run_case,
    source_inlet,
    total_to_static_inlet,
)


def test_source_ledger_loads_and_has_expected_authority() -> None:
    source = load_public_surrogate_source()
    assert source["schema_version"] == 1
    assert source["primary_source"]["doi"] == "10.7527/S1000-6893.2024.30944"
    assert source["inflow_total_conditions_si"]["Mach"] == pytest.approx(2.52)
    assert sum(source["inflow_total_conditions_si"]["mass_fractions"].values()) == pytest.approx(1.0)


def test_source_loader_rejects_invalid_mass_fraction_sum(tmp_path: Path) -> None:
    source = load_public_surrogate_source()
    source["inflow_total_conditions_si"]["mass_fractions"]["N2"] = 0.5
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(source), encoding="utf-8")
    with pytest.raises(ValueError, match="mass fractions must sum to 1"):
        load_public_surrogate_source(path)


def test_total_to_static_conversion_matches_source_case() -> None:
    inlet = total_to_static_inlet(2.52, 1650.0, 1_340_000.0, GasProperties())
    assert inlet.Mach == pytest.approx(2.52)
    assert inlet.T_K == pytest.approx(726.85, rel=2.0e-4)
    assert inlet.p_Pa == pytest.approx(76_030.0, rel=3.0e-4)
    assert inlet.rho_kg_m3 == pytest.approx(0.36445, rel=4.0e-4)
    assert inlet.u_m_s == pytest.approx(1361.84, rel=3.0e-4)
    assert inlet.T_K > 0.0
    assert inlet.p_Pa > 0.0
    assert inlet.rho_kg_m3 > 0.0
    assert inlet.u_m_s > 0.0


def test_source_inlet_retains_expected_mach() -> None:
    inlet = source_inlet(load_public_surrogate_source(), GasProperties())
    reconstructed = inlet.u_m_s / inlet.a_m_s
    assert reconstructed == pytest.approx(2.52, rel=1.0e-12)


def test_geometry_uses_source_lengths_and_positive_areas() -> None:
    source = load_public_surrogate_source()
    geometry, x, length = build_public_surrogate_geometry(source, 238)
    g = source["geometry_si"]
    expected_length = g["L1_isolator_m"] + g["L2_pre_cavity_m"] + g["L3_combustor_m"]
    assert length == pytest.approx(expected_length)
    assert geometry.num_cells == 238
    assert geometry.face_area.size == 239
    assert x.size == 238
    assert np.all(np.isfinite(geometry.cell_area))
    assert np.all(geometry.cell_area > 0.0)
    assert geometry.face_area[0] == pytest.approx(g["width_W_m"] * g["height_H1_m"])
    assert geometry.face_area[-1] == pytest.approx(g["width_W_m"] * g["height_H2_m"])


def test_cavity_depth_is_not_added_to_core_area() -> None:
    source = load_public_surrogate_source()
    geometry, _, _ = build_public_surrogate_geometry(source, 64)
    g = source["geometry_si"]
    maximum_core_area = g["width_W_m"] * max(g["height_H1_m"], g["height_H2_m"])
    assert float(np.max(geometry.face_area)) == pytest.approx(maximum_core_area)
    assert float(np.max(geometry.face_area)) < g["width_W_m"] * (
        g["height_H2_m"] + g["cavity_depth_Dc_m"]
    )


def test_isolator_ofat_changes_only_axial_length_policy() -> None:
    source = load_public_surrogate_source()
    base, _, base_length = build_public_surrogate_geometry(source, 120, isolator_length_m=0.560)
    short, _, short_length = build_public_surrogate_geometry(source, 92, isolator_length_m=0.280)
    assert base_length - short_length == pytest.approx(0.280)
    assert base.face_area[0] == pytest.approx(short.face_area[0])
    assert base.face_area[-1] == pytest.approx(short.face_area[-1])


def test_case_configuration_is_nonreactive_supersonic_cold_flow() -> None:
    source = load_public_surrogate_source()
    case = build_case(source, case_id=CASE_ID_BASELINE, target_dx_m=0.02, max_time_s=1.0e-5)
    assert case.boundary_conditions.inlet == "supersonic-inflow"
    assert case.boundary_conditions.outlet == "supersonic-outflow"
    assert case.inlet.Mach > 1.0
    assert case.numerical.cfl == pytest.approx(0.2)
    assert case.numerical.tolerance == pytest.approx(1.0e-8)
    assert case.dx_m > 0.0


def test_small_grid_solver_smoke_is_finite() -> None:
    source = load_public_surrogate_source()
    case = build_case(
        source,
        case_id="P11A-SMOKE",
        target_dx_m=0.15,
        max_time_s=1.0e-7,
        max_steps=100,
    )
    result = run_case(case)
    assert result.U.shape == (case.num_cells, 3)
    assert np.all(np.isfinite(result.U))
    assert np.isfinite(result.residual)
    assert result.steps >= 0


def test_tracked_source_path_exists() -> None:
    assert SOURCE_PATH.is_file()
