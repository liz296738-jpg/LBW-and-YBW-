"""Hard gates for the P9.2 characteristic static-pressure outlet."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.boundary import BoundaryConditions, boundary_interface_fluxes, subsonic_pressure_outlet_state
from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.gas import speed_of_sound
from scramjet1d.geometry import constant_area_profile
from scramjet1d.solver import quasi_1d_rhs, solve_quasi_1d
from scramjet1d.source_terms import combined_wall_source, distributed_combustion_heat_release_source, distributed_fuel_injection_source
from scramjet1d.spatial import internal_numerical_fluxes
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative


GAS = GasProperties(); NUMERICAL = NumericalConfig(cfl=.2)


def _state(rho: float = 1.2, u: float = 200., p: float = 100_000., n: int = 8) -> np.ndarray:
    return primitive_to_conservative(np.full(n, rho), np.full(n, u), np.full(n, p), GAS)


def _conditions(pressure: float = 100_000.) -> BoundaryConditions:
    return BoundaryConditions(outlet="subsonic-pressure", outlet_static_pressure=pressure)


def test_pressure_outlet_configuration_validation() -> None:
    with pytest.raises(ValueError): BoundaryConditions(outlet="subsonic-pressure")
    for pressure in (0., -1., np.nan, np.inf, -np.inf, np.array([100_000.])):
        with pytest.raises(ValueError): BoundaryConditions(outlet="subsonic-pressure", outlet_static_pressure=pressure)
    for outlet in ("transmissive", "supersonic-outflow"):
        with pytest.raises(ValueError): BoundaryConditions(outlet=outlet, outlet_static_pressure=100_000.)


def test_reconstruction_preserves_pressure_entropy_and_outgoing_invariant() -> None:
    interior = _state(n=1)[0]; boundary = subsonic_pressure_outlet_state(interior, 105_000., GAS)
    pi, pb = conservative_to_primitive(interior, GAS), conservative_to_primitive(boundary, GAS)
    ai, ab = speed_of_sound(pi.T, GAS), speed_of_sound(pb.T, GAS)
    assert_allclose(pb.p, 105_000., rtol=0., atol=1e-10)
    assert_allclose(pb.p / pb.rho**GAS.gamma, pi.p / pi.rho**GAS.gamma, rtol=0., atol=1e-10)
    assert_allclose(pb.u + 2*ab/(GAS.gamma-1), pi.u + 2*ai/(GAS.gamma-1), rtol=0., atol=1e-10)
    assert 0 < pb.u and 0 < pb.Mach < 1
    assert_allclose(subsonic_pressure_outlet_state(interior, float(pi.p), GAS), interior, rtol=0., atol=1e-9)


def test_reconstruction_rejects_invalid_interior_and_reconstructed_regimes() -> None:
    for interior in (_state(u=0., n=1)[0], _state(u=-10., n=1)[0], _state(u=400., n=1)[0]):
        with pytest.raises(ValueError): subsonic_pressure_outlet_state(interior, 100_000., GAS)
    interior = _state(n=1)[0]
    for pressure in (50_000., 300_000.):
        with pytest.raises(ValueError): subsonic_pressure_outlet_state(interior, pressure, GAS)


def test_exact_sonic_pressure_outlet_is_rejected() -> None:
    rho, pressure = 1.2, 100_000.; sonic = np.sqrt(GAS.gamma * pressure / rho)
    with pytest.raises(ValueError): subsonic_pressure_outlet_state(primitive_to_conservative(rho, sonic, pressure, GAS), pressure, GAS)


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_pressure_outlet_flux_uses_interior_and_reconstructed_state(scheme: str) -> None:
    states = _state(); conditions = _conditions(105_000.)
    actual = boundary_interface_fluxes(states, GAS, conditions, scheme=scheme)[-1]
    boundary = subsonic_pressure_outlet_state(states[-1], 105_000., GAS)
    expected = internal_numerical_fluxes(np.stack((states[-1], boundary)), GAS, scheme=scheme)[0]
    assert_allclose(actual, expected, rtol=0., atol=1e-10)


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_uniform_subsonic_pressure_outlet_is_steady_and_moderate_mismatch_is_finite(scheme: str) -> None:
    states = _state(); geometry = constant_area_profile(8); conditions = _conditions()
    assert_allclose(quasi_1d_rhs(states, geometry, .1, GAS, flux_scheme=scheme, boundary_conditions=conditions), 0., rtol=0., atol=1e-6)
    steady = solve_quasi_1d(states, geometry, .1, 3e-5, GAS, NUMERICAL, flux_scheme=scheme, boundary_conditions=conditions)
    assert_allclose(steady.U, states, rtol=0., atol=1e-8)
    mismatch = solve_quasi_1d(states, geometry, .1, 1e-4, GAS, NUMERICAL, flux_scheme=scheme, boundary_conditions=_conditions(105_000.))
    primitive = conservative_to_primitive(mismatch.U, GAS)
    assert mismatch.steps > 1 and mismatch.time == 1e-4 and np.all(np.isfinite(mismatch.U))
    assert np.all(primitive.rho > 0) and np.all(primitive.p > 0) and np.all(primitive.T > 0)


@pytest.mark.parametrize("states, conditions", ((_state(u=400.), _conditions()), (_state(), _conditions(50_000.)), (_state(), _conditions(300_000.))))
def test_invalid_initial_pressure_outlet_fails_before_cfl(monkeypatch: pytest.MonkeyPatch, states: np.ndarray, conditions: BoundaryConditions) -> None:
    import scramjet1d.solver as solver
    monkeypatch.setattr(solver, "cfl_timestep", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("CFL reached")))
    with pytest.raises(ValueError): solve_quasi_1d(states, constant_area_profile(8), .1, 1e-5, GAS, NUMERICAL, boundary_conditions=conditions)


def test_rk_stage_pressure_outlet_regime_violation_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    import scramjet1d.solver as solver
    def invalid_stage(state: np.ndarray, dt: float, rhs: object) -> np.ndarray:
        stage = state.copy(); stage[-1] = _state(u=400., n=1)[0]
        return rhs(stage)  # type: ignore[operator]
    monkeypatch.setattr(solver, "ssp_rk3_step", invalid_stage)
    with pytest.raises(ValueError):
        solve_quasi_1d(_state(), constant_area_profile(8), .1, 1e-5, GAS, NUMERICAL, boundary_conditions=_conditions())


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_batched_pressure_reconstruction_and_flux_match_loop(scheme: str) -> None:
    states = np.stack((_state(), _state(rho=1.1, u=180., p=95_000.))); conditions = _conditions(100_000.)
    reconstructed = subsonic_pressure_outlet_state(states[..., -1, :], 100_000., GAS)
    fluxes = boundary_interface_fluxes(states, GAS, conditions, scheme=scheme)
    expected = np.stack([boundary_interface_fluxes(sample, GAS, conditions, scheme=scheme) for sample in states])
    interior = conservative_to_primitive(states[..., -1, :], GAS); boundary = conservative_to_primitive(reconstructed, GAS)
    sound_i, sound_b = speed_of_sound(interior.T, GAS), speed_of_sound(boundary.T, GAS)
    assert reconstructed.shape == (2, 3) and fluxes.shape == (2, 9, 3)
    assert_allclose(boundary.p, 100_000., rtol=0., atol=1e-10)
    assert_allclose(boundary.p / boundary.rho**GAS.gamma, interior.p / interior.rho**GAS.gamma, rtol=0., atol=1e-10)
    assert_allclose(boundary.u + 2*sound_b/(GAS.gamma-1), interior.u + 2*sound_i/(GAS.gamma-1), rtol=0., atol=1e-10)
    assert_allclose(fluxes, expected, rtol=0., atol=0.)


def test_pressure_outlet_composes_wall_fuel_combustion_and_preserves_inputs() -> None:
    states = _state(); original = states.copy(); geometry = constant_area_profile(8, .02); areas = geometry.cell_area.copy()
    conditions = _conditions(105_000.); wall = dict(hydraulic_diameter=.1, darcy_friction_factor=.01, wall_heat_flux=20_000.)
    fuel = dict(fuel_mass_flow_rate_per_length=.002, fuel_axial_velocity=100., fuel_specific_total_enthalpy=1e6); burn = dict(fuel_burn_rate_per_length=.0002, fuel_lower_heating_value=40e6)
    base = quasi_1d_rhs(states, geometry, .1, GAS, boundary_conditions=conditions)
    actual = quasi_1d_rhs(states, geometry, .1, GAS, boundary_conditions=conditions, **wall, **fuel, **burn)
    expected = base + combined_wall_source(states, **wall, gas=GAS) + distributed_fuel_injection_source(states, geometry, **fuel, gas=GAS) + distributed_combustion_heat_release_source(states, geometry, **burn, gas=GAS)
    assert_allclose(actual, expected, rtol=0., atol=1e-10); assert_allclose(states, original, rtol=0., atol=0.); assert_allclose(geometry.cell_area, areas, rtol=0., atol=0.)
