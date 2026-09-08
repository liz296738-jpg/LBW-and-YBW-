"""Controlled isentropic quasi-1D area-physics validation tests."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.config import GasProperties
from scramjet1d.flux import euler_flux
from scramjet1d.geometry import AreaProfile
from scramjet1d.isentropic import (
    area_mach_ratio,
    isentropic_nozzle_reference,
    isentropic_state_from_stagnation,
    mach_from_area_ratio,
)
from scramjet1d.solver import quasi_1d_rhs_transmissive
from scramjet1d.spatial import quasi_1d_residual
from scramjet1d.state import primitive_to_conservative


GAS = GasProperties()
P0 = 300_000.0
T0 = 500.0


def _profile(num_cells: int, *, start: float = 1.0, end: float = 1.2) -> AreaProfile:
    face_area = np.linspace(start, end, num_cells + 1)
    return AreaProfile(0.5 * (face_area[:-1] + face_area[1:]), face_area)


def _reference(profile: AreaProfile, mach: float, branch: str):
    return isentropic_nozzle_reference(
        profile.cell_area, profile.cell_area[0], mach, P0, T0, GAS, branch
    )


def _momentum_rms(values: np.ndarray) -> float:
    return float(np.sqrt(np.mean(values[..., 1] ** 2)))


def test_area_mach_relation_has_sonic_minimum() -> None:
    assert_allclose(area_mach_ratio(1.0, GAS), 1.0, rtol=0.0, atol=1e-14)
    assert area_mach_ratio(0.5, GAS) > 1.0
    assert area_mach_ratio(2.0, GAS) > 1.0


@pytest.mark.parametrize("mach", [0.2, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0])
def test_area_mach_inverse_recovers_each_branch(mach: float) -> None:
    branch = "subsonic" if mach <= 1.0 else "supersonic"
    ratio = area_mach_ratio(mach, GAS)
    assert_allclose(mach_from_area_ratio(ratio, GAS, branch), mach, rtol=0.0, atol=2e-12)


@pytest.mark.parametrize("mach", [0.0, -0.1, np.nan, np.inf])
def test_area_mach_rejects_invalid_mach(mach: float) -> None:
    with pytest.raises(ValueError):
        area_mach_ratio(mach, GAS)


@pytest.mark.parametrize("ratio", [0.0, -1.0, 0.999, np.nan, np.inf])
def test_inverse_rejects_invalid_area_ratio(ratio: float) -> None:
    with pytest.raises(ValueError):
        mach_from_area_ratio(ratio, GAS, "subsonic")


@pytest.mark.parametrize("branch", ["slow", "fast", "sub", None])
def test_inverse_rejects_invalid_branch(branch: object) -> None:
    with pytest.raises(ValueError):
        mach_from_area_ratio(1.5, GAS, branch)


def test_isentropic_state_recovers_stagnation_quantities() -> None:
    state = isentropic_state_from_stagnation(np.array([0.4, 0.8, 1.5, 2.5]), P0, T0, GAS)
    temperature_ratio = 1.0 + (GAS.gamma - 1.0) * state.Mach**2 / 2.0
    recovered_T0 = state.T * temperature_ratio
    recovered_p0 = state.p * temperature_ratio ** (GAS.gamma / (GAS.gamma - 1.0))

    assert_allclose(recovered_T0, T0, rtol=1e-13)
    assert_allclose(recovered_p0, P0, rtol=1e-13)
    assert_allclose(state.Mach, [0.4, 0.8, 1.5, 2.5], rtol=1e-13)


@pytest.mark.parametrize("bad", [0.0, -1.0, np.nan, np.inf])
def test_isentropic_state_rejects_invalid_stagnation_quantities(bad: float) -> None:
    with pytest.raises(ValueError):
        isentropic_state_from_stagnation(0.5, bad, T0, GAS)
    with pytest.raises(ValueError):
        isentropic_state_from_stagnation(0.5, P0, bad, GAS)


def test_nozzle_reference_conserves_mass_and_stagnation_properties() -> None:
    area = np.linspace(1.0, 1.2, 41)
    state = isentropic_nozzle_reference(area, 1.0, 0.5, P0, T0, GAS, "subsonic")
    mass_flow = state.rho * state.u * area
    temperature_ratio = 1.0 + (GAS.gamma - 1.0) * state.Mach**2 / 2.0

    assert (np.max(mass_flow) - np.min(mass_flow)) / abs(np.mean(mass_flow)) < 1e-10
    assert_allclose(state.T * temperature_ratio, T0, rtol=1e-12)
    assert_allclose(state.p * temperature_ratio ** (GAS.gamma / (GAS.gamma - 1.0)), P0, rtol=1e-12)


@pytest.mark.parametrize("branch, reference_mach", [("subsonic", 2.0), ("supersonic", 0.5)])
def test_nozzle_reference_rejects_mismatched_reference_branch(branch: str, reference_mach: float) -> None:
    with pytest.raises(ValueError):
        isentropic_nozzle_reference(np.linspace(1.0, 1.2, 5), 1.0, reference_mach, P0, T0, GAS, branch)


def test_nozzle_reference_rejects_profile_below_critical_area() -> None:
    with pytest.raises(ValueError):
        isentropic_nozzle_reference(np.array([0.9, 1.0]), 1.0, 1.0, P0, T0, GAS, "subsonic")


@pytest.mark.parametrize(
    "branch, start, end, reference_mach, mach_direction, velocity_direction, pressure_direction",
    [
        ("subsonic", 1.0, 1.2, 0.5, -1, -1, 1),
        ("subsonic", 1.2, 1.0, 0.5, 1, 1, -1),
        ("supersonic", 1.0, 1.2, 2.0, 1, 1, -1),
        ("supersonic", 1.2, 1.0, 2.0, -1, -1, 1),
    ],
)
def test_nozzle_reference_has_correct_area_response_trends(
    branch: str, start: float, end: float, reference_mach: float, mach_direction: int, velocity_direction: int, pressure_direction: int
) -> None:
    area = np.linspace(start, end, 31)
    state = isentropic_nozzle_reference(area, area[0], reference_mach, P0, T0, GAS, branch)
    assert mach_direction * (state.Mach[-1] - state.Mach[0]) > 0.0
    assert velocity_direction * (state.u[-1] - state.u[0]) > 0.0
    assert pressure_direction * (state.p[-1] - state.p[0]) > 0.0


def test_exact_face_quasi_residual_has_second_order_geometry_consistency() -> None:
    errors = []
    for num_cells in (40, 80, 160):
        profile = _profile(num_cells)
        cell = _reference(profile, 0.5, "subsonic")
        face = isentropic_nozzle_reference(profile.face_area, profile.cell_area[0], 0.5, P0, T0, GAS, "subsonic")
        U_cell = primitive_to_conservative(cell.rho, cell.u, cell.p, GAS)
        F_face = euler_flux(primitive_to_conservative(face.rho, face.u, face.p, GAS), GAS)
        errors.append(_momentum_rms(quasi_1d_residual(U_cell, F_face, profile, 1.0 / num_cells, GAS)))
    orders = np.log(np.asarray(errors[:-1]) / np.asarray(errors[1:])) / np.log(2.0)
    assert np.all(orders > 1.7)


def test_actual_rusanov_interior_residual_converges_first_order() -> None:
    errors = []
    for num_cells in (80, 160, 320):
        profile = _profile(num_cells)
        cell = _reference(profile, 0.5, "subsonic")
        U_cell = primitive_to_conservative(cell.rho, cell.u, cell.p, GAS)
        residual = quasi_1d_rhs_transmissive(U_cell, profile, 1.0 / num_cells, GAS)
        errors.append(_momentum_rms(residual[2:-2]))
    orders = np.log(np.asarray(errors[:-1]) / np.asarray(errors[1:])) / np.log(2.0)
    assert np.all(orders > 0.7)
