"""Reference-level tests for P6.4 wall-source validation utilities."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.config import GasProperties
from scramjet1d.state import conservative_to_primitive
from scramjet1d.verification import (
    assess_residual_convergence,
    fanno_parameter,
    fanno_flow_reference,
    mach_from_fanno_parameter,
    mach_from_rayleigh_t0_ratio,
    rayleigh_flow_reference,
    rayleigh_t0_ratio,
    uniform_wall_source_reference,
)


GAS = GasProperties()


def test_uniform_wall_source_reference_matches_hand_derived_conservative_state() -> None:
    reference = uniform_wall_source_reference(1.0, 600.0, 100_000.0, 0.002, 0.1, 0.04, 100_000.0, GAS)
    expected_velocity = 600.0 / (1.0 + (0.04 / 0.2) * 600.0 * 0.002)
    expected_energy = 100_000.0 / 0.4 + 0.5 * 600.0**2 + (4.0 * 100_000.0 / 0.1) * 0.002
    assert reference.U.shape == (3,)
    assert_allclose(reference.U, [1.0, expected_velocity, expected_energy])
    assert np.isfinite(reference.primitive.p) and reference.primitive.p > 0.0


@pytest.mark.parametrize("mach", [0.4, 0.8, 1.5, 2.0])
def test_fanno_parameter_and_branch_inversion_are_consistent(mach: float) -> None:
    branch = "subsonic" if mach < 1.0 else "supersonic"
    assert_allclose(mach_from_fanno_parameter(fanno_parameter(mach, GAS), GAS, branch), mach, rtol=0.0, atol=2e-12)


def test_fanno_parameter_has_sonic_zero_and_positive_nonsonic_values() -> None:
    assert_allclose(fanno_parameter(1.0, GAS), 0.0, rtol=0.0, atol=1e-14)
    assert fanno_parameter(0.4, GAS) > 0.0
    assert fanno_parameter(2.0, GAS) > 0.0


def test_fanno_supersonic_inversion_rejects_targets_beyond_its_finite_branch_limit() -> None:
    limit = -1.0 / GAS.gamma + (GAS.gamma + 1.0) / (2.0 * GAS.gamma) * np.log((GAS.gamma + 1.0) / (GAS.gamma - 1.0))
    with pytest.raises(ValueError, match="exceeds the supersonic branch limit"):
        mach_from_fanno_parameter(limit * (1.0 + 1e-8), GAS, "supersonic")


def test_residual_assessment_accepts_superconvergence_and_roundoff_limited_sequences() -> None:
    superconvergent = assess_residual_convergence([1.0, 0.25, 0.0625], 2.0)
    roundoff_limited = assess_residual_convergence([3e-13, 8e-13, 2e-13], 1.0)
    assert superconvergent.classification == "superconvergent"
    assert superconvergent.monotone
    assert_allclose(superconvergent.final_order, 2.0)
    assert roundoff_limited.classification == "roundoff-limited"
    assert roundoff_limited.normalized_finest_error <= 1e-10


def test_residual_assessment_rejects_nonmonotone_or_low_order_sequences() -> None:
    assert assess_residual_convergence([1.0, 0.9, 0.85], 1.0).classification == "failed"
    assert assess_residual_convergence([1.0, 1.1, 0.5], 1.0).classification == "failed"


@pytest.mark.parametrize("mach", [0.4, 0.8, 1.5, 2.0])
def test_rayleigh_ratio_and_branch_inversion_are_consistent(mach: float) -> None:
    branch = "subsonic" if mach < 1.0 else "supersonic"
    assert_allclose(mach_from_rayleigh_t0_ratio(rayleigh_t0_ratio(mach, GAS), GAS, branch), mach, rtol=0.0, atol=2e-12)


def test_rayleigh_ratio_has_sonic_maximum() -> None:
    assert_allclose(rayleigh_t0_ratio(1.0, GAS), 1.0, rtol=0.0, atol=1e-14)
    assert 0.0 < rayleigh_t0_ratio(0.4, GAS) < 1.0
    assert 0.0 < rayleigh_t0_ratio(2.0, GAS) < 1.0


@pytest.mark.parametrize("function,args", [(fanno_parameter, (0.0, GAS)), (rayleigh_t0_ratio, (np.nan, GAS)), (mach_from_fanno_parameter, (-1.0, GAS, "subsonic")), (mach_from_rayleigh_t0_ratio, (1.1, GAS, "subsonic"))])
def test_p6_verification_helpers_reject_invalid_values(function: object, args: tuple[object, ...]) -> None:
    with pytest.raises(ValueError):
        function(*args)


@pytest.mark.parametrize("branch,mach_in,mach_out", [("subsonic", 0.4, 0.6), ("supersonic", 2.0, 1.5)])
def test_fanno_reference_preserves_mass_and_stagnation_temperature(branch: str, mach_in: float, mach_out: float) -> None:
    length, diameter = 10.0, 0.1
    friction = diameter / length * (fanno_parameter(mach_in, GAS) - fanno_parameter(mach_out, GAS))
    state = fanno_flow_reference(np.linspace(0.0, length, 21), 1.0, 100_000.0, mach_in, diameter, friction, GAS, branch)
    mass_flux = state.rho * state.u
    t0 = state.T * (1.0 + (GAS.gamma - 1.0) * state.Mach**2 / 2.0)
    assert_allclose(state.Mach[[0, -1]], [mach_in, mach_out], rtol=0.0, atol=2e-11)
    assert_allclose(mass_flux, mass_flux[0], rtol=1e-12)
    assert_allclose(t0, t0[0], rtol=1e-12)
    assert (state.Mach[-1] > state.Mach[0]) if branch == "subsonic" else (state.Mach[-1] < state.Mach[0])


@pytest.mark.parametrize("branch,mach_in,mach_out", [("subsonic", 0.4, 0.6), ("supersonic", 2.0, 1.5)])
def test_rayleigh_reference_preserves_mass_momentum_and_target_mach(branch: str, mach_in: float, mach_out: float) -> None:
    length, diameter, pressure, temperature = 10.0, 0.1, 100_000.0, 300.0
    rho = pressure / (GAS.R * temperature)
    t0_in = temperature * (1.0 + (GAS.gamma - 1.0) * mach_in**2 / 2.0)
    t0_star = t0_in / rayleigh_t0_ratio(mach_in, GAS)
    delta_t0 = t0_star * rayleigh_t0_ratio(mach_out, GAS) - t0_in
    speed = mach_in * np.sqrt(GAS.gamma * GAS.R * temperature)
    mass_flux = rho * speed
    cp = GAS.gamma * GAS.R / (GAS.gamma - 1.0)
    heat_flux = mass_flux * cp * diameter * delta_t0 / (4.0 * length)
    state = rayleigh_flow_reference(np.linspace(0.0, length, 21), rho, pressure, mach_in, diameter, heat_flux, GAS, branch)
    assert_allclose(state.Mach[[0, -1]], [mach_in, mach_out], rtol=0.0, atol=2e-11)
    assert_allclose(state.rho * state.u, mass_flux, rtol=1e-12)
    assert_allclose(state.rho * state.u**2 + state.p, state.rho[0] * state.u[0] ** 2 + state.p[0], rtol=1e-12)
