"""Validation utilities and controlled P5.4 flux-scheme comparisons."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.geometry import AreaProfile, constant_area_profile
from scramjet1d.isentropic import isentropic_nozzle_reference
from scramjet1d.solver import quasi_1d_rhs_transmissive, solve_quasi_1d
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative
from scramjet1d.verification import (
    advected_contact_reference,
    l1_error,
    observed_order,
    smooth_entropy_wave_reference,
    transition_width_cells,
)


GAS = GasProperties()
NUMERICAL = NumericalConfig()


def _state(rho: object, velocity: object, pressure: object) -> np.ndarray:
    return primitive_to_conservative(rho, velocity, pressure, GAS)


def test_verification_references_and_metrics_are_vectorized_and_validate_inputs() -> None:
    x = np.array([0.0, 0.25, 0.5])
    entropy = smooth_entropy_wave_reference(x, 0.1, 1.0, 800.0, 100_000.0, 0.1, 0.25, 0.05, GAS)
    assert entropy.rho.shape == x.shape
    assert_allclose(entropy.u, 800.0)
    assert_allclose(entropy.p, 100_000.0)
    contact = advected_contact_reference(x, 0.0, 1.0, 0.6, 800.0, 100_000.0, 0.3, GAS)
    assert_allclose(contact.rho, [1.0, 1.0, 0.6])
    assert l1_error([1.0, 2.0], [2.0, 4.0]) == pytest.approx(1.5)
    assert observed_order(0.4, 0.2) == pytest.approx(1.0)
    assert transition_width_cells([1.0, 0.8, 0.5, 0.2, 0.1], 1.0, 0.1) == 3
    with pytest.raises(ValueError):
        smooth_entropy_wave_reference([0.0, np.nan], 0.0, 1.0, 800.0, 100_000.0, 0.1, 0.25, 0.05, GAS)
    with pytest.raises(ValueError):
        observed_order(0.0, 0.2)


@pytest.mark.parametrize("scheme", ["rusanov", "steger-warming"])
@pytest.mark.parametrize("branch,mach", [("subsonic", 0.5), ("supersonic", 2.0)])
def test_steger_warming_isentropic_residual_converges_first_order(branch: str, mach: float, scheme: str) -> None:
    errors = []
    for count in (80, 160, 320):
        face_area = np.linspace(1.0, 1.2, count + 1)
        geometry = AreaProfile(0.5 * (face_area[:-1] + face_area[1:]), face_area)
        reference = isentropic_nozzle_reference(geometry.cell_area, 1.0, mach, 300_000.0, 500.0, GAS, branch)
        residual = quasi_1d_rhs_transmissive(_state(reference.rho, reference.u, reference.p), geometry, 1.0 / count, GAS, flux_scheme=scheme)
        errors.append(float(np.sqrt(np.mean(residual[2:-2, 1] ** 2))))
    assert all(later < earlier for earlier, later in zip(errors, errors[1:]))
    assert 0.8 <= observed_order(errors[-2], errors[-1]) <= 1.2


@pytest.mark.parametrize("scheme", ["rusanov", "steger-warming"])
def test_flux_scheme_entropy_wave_converges_first_order(scheme: str) -> None:
    errors = []
    for count in (80, 160, 320):
        dx = 1.0 / count
        x = (np.arange(count) + 0.5) * dx
        initial = smooth_entropy_wave_reference(x, 0.0, 1.0, 800.0, 100_000.0, 0.1, 0.25, 0.05, GAS)
        final = solve_quasi_1d(_state(initial.rho, initial.u, initial.p), constant_area_profile(count), dx, 0.1 / 800.0, GAS, NUMERICAL, flux_scheme=scheme)
        exact = smooth_entropy_wave_reference(x, final.time, 1.0, 800.0, 100_000.0, 0.1, 0.25, 0.05, GAS)
        errors.append(l1_error(conservative_to_primitive(final.U, GAS).rho, exact.rho))
    assert all(later < earlier for earlier, later in zip(errors, errors[1:]))
    assert 0.75 <= observed_order(errors[-2], errors[-1]) <= 1.25


def test_steger_warming_is_less_diffusive_for_fully_supersonic_contact() -> None:
    count, velocity, pressure, final_time = 200, 800.0, 100_000.0, 0.0002
    dx = 1.0 / count
    x = (np.arange(count) + 0.5) * dx
    initial = advected_contact_reference(x, 0.0, 1.0, 0.6, velocity, pressure, 0.3, GAS)
    assert np.all(initial.u - np.sqrt(GAS.gamma * initial.p / initial.rho) > 0.0)
    exact = advected_contact_reference(x, final_time, 1.0, 0.6, velocity, pressure, 0.3, GAS)
    results = {scheme: conservative_to_primitive(solve_quasi_1d(_state(initial.rho, initial.u, initial.p), constant_area_profile(count), dx, final_time, GAS, NUMERICAL, flux_scheme=scheme).U, GAS).rho for scheme in ("rusanov", "steger-warming")}
    errors = {scheme: l1_error(rho, exact.rho) for scheme, rho in results.items()}
    assert errors["steger-warming"] < errors["rusanov"]


@pytest.mark.parametrize("scheme", ["rusanov", "steger-warming"])
def test_both_flux_schemes_survive_sod_smoke_case(scheme: str) -> None:
    count, dx = 200, 1.0 / 200
    x = (np.arange(count) + 0.5) * dx
    initial = _state(np.where(x < 0.5, 1.0, 0.125), np.zeros(count), np.where(x < 0.5, 100_000.0, 10_000.0))
    result = solve_quasi_1d(initial, constant_area_profile(count), dx, 0.0004, GAS, NUMERICAL, flux_scheme=scheme)
    primitive = conservative_to_primitive(result.U, GAS)
    assert result.time == 0.0004
    assert np.all(np.isfinite(result.U)) and np.all(primitive.rho > 0.0) and np.all(primitive.p > 0.0) and np.all(primitive.T > 0.0) and np.all(np.isfinite(primitive.Mach))
    assert not np.allclose(result.U, initial)


@pytest.mark.parametrize("mach", [0.95, 1.0, 1.05])
def test_steger_warming_near_sonic_smoke_case_remains_physical(mach: float) -> None:
    count, dx, pressure, density = 100, 0.01, 100_000.0, 1.0
    sound_speed = np.sqrt(GAS.gamma * pressure / density)
    x = (np.arange(count) + 0.5) * dx
    initial = _state(np.full(count, density), np.full(count, mach * sound_speed), pressure * (1.0 + 0.002 * np.exp(-((x - 0.5) / 0.08) ** 2)))
    result = solve_quasi_1d(initial, constant_area_profile(count), dx, 3e-5, GAS, NUMERICAL, flux_scheme="steger-warming")
    primitive = conservative_to_primitive(result.U, GAS)
    assert result.time == 3e-5
    assert np.all(np.isfinite(result.U)) and np.all(primitive.rho > 0.0) and np.all(primitive.p > 0.0) and np.all(primitive.T > 0.0)
