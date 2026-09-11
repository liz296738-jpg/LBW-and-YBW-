"""Formal hard gates for the P9.3 characteristic total-condition inlet."""

from dataclasses import FrozenInstanceError
import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.boundary import BoundaryConditions, PrimitiveBoundaryState, boundary_interface_fluxes, subsonic_total_inlet_state
from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.flux import euler_flux
from scramjet1d.gas import speed_of_sound
from scramjet1d.geometry import constant_area_profile
from scramjet1d.solver import quasi_1d_rhs, solve_quasi_1d
from scramjet1d.source_terms import combined_wall_source, distributed_combustion_heat_release_source, distributed_fuel_injection_source
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative

GAS = GasProperties()
NUMERICAL = NumericalConfig(cfl=0.2)


def _state(rho=1.2, u=200.0, p=100_000.0, n=1):
    return primitive_to_conservative(np.full(n, rho), np.full(n, u), np.full(n, p), GAS)


def _totals(state):
    q = conservative_to_primitive(state, GAS); beta = (GAS.gamma - 1.0) / 2.0
    return float(q.p.flat[0] * (1 + beta * q.Mach.flat[0] ** 2) ** (GAS.gamma / (GAS.gamma - 1))), float(q.T.flat[0] * (1 + beta * q.Mach.flat[0] ** 2))


def _conditions(state, pressure_factor=1.0, temperature_factor=1.0):
    p0, t0 = _totals(state); outlet = float(conservative_to_primitive(state, GAS).p.flat[0])
    return BoundaryConditions(inlet="subsonic-total-inflow", outlet="subsonic-pressure", inlet_total_pressure=p0 * pressure_factor, inlet_total_temperature=t0 * temperature_factor, outlet_static_pressure=outlet)


def test_reconstruction_recovers_totals_and_incoming_characteristic():
    interior = _state()[0]; p0, t0 = _totals(interior); boundary = subsonic_total_inlet_state(interior, p0, t0, GAS)
    qi, qb = conservative_to_primitive(interior, GAS), conservative_to_primitive(boundary, GAS)
    assert_allclose(boundary, interior, rtol=0, atol=1e-9); assert_allclose(_totals(boundary), (p0, t0), rtol=0, atol=1e-9)
    assert_allclose(qb.u - 2 * speed_of_sound(qb.T, GAS) / (GAS.gamma - 1), qi.u - 2 * speed_of_sound(qi.T, GAS) / (GAS.gamma - 1), rtol=0, atol=1e-9)
    assert 0 < qb.Mach < 1


@pytest.mark.parametrize("bad", ((None, 300.), (200000., None), (0., 300.), (200000., 0.)))
def test_total_condition_configuration_rejects_missing_and_zero_values(bad):
    with pytest.raises(ValueError): BoundaryConditions(inlet="subsonic-total-inflow", inlet_total_pressure=bad[0], inlet_total_temperature=bad[1])


@pytest.mark.parametrize("value", (-1., np.nan, np.inf, -np.inf, np.array([200000.])))
def test_total_condition_configuration_rejects_invalid_scalar_values(value):
    with pytest.raises(ValueError): BoundaryConditions(inlet="subsonic-total-inflow", inlet_total_pressure=value, inlet_total_temperature=300.)
    with pytest.raises(ValueError): BoundaryConditions(inlet="subsonic-total-inflow", inlet_total_pressure=200000., inlet_total_temperature=value)


def test_inlet_modes_reject_irrelevant_prescribed_fields():
    prescribed = PrimitiveBoundaryState(1.2, 500., 100000.)
    for kwargs in (dict(inlet="transmissive", inlet_state=prescribed), dict(inlet="transmissive", inlet_total_pressure=200000., inlet_total_temperature=300.), dict(inlet="supersonic-inflow", inlet_state=prescribed, inlet_total_pressure=200000., inlet_total_temperature=300.), dict(inlet="subsonic-total-inflow", inlet_state=prescribed, inlet_total_pressure=200000., inlet_total_temperature=300.)):
        with pytest.raises(ValueError): BoundaryConditions(**kwargs)


@pytest.mark.parametrize("velocity", (0., -1., 400.))
def test_inlet_rejects_stagnant_reverse_and_supersonic_interiors(velocity):
    with pytest.raises(ValueError): subsonic_total_inlet_state(_state(u=velocity)[0], 200000., 300., GAS)


def test_exact_sonic_inlet_is_rejected():
    rho, pressure = 1.2, 100000.; sonic = np.sqrt(GAS.gamma * pressure / rho)
    with pytest.raises(ValueError): subsonic_total_inlet_state(_state(rho, sonic, pressure)[0], 200000., 300., GAS)


def test_no_strict_subsonic_root_is_rejected():
    interior = _state()[0]; t0 = 1000.; q = conservative_to_primitive(interior, GAS); target = q.u - 2 * speed_of_sound(q.T, GAS) / (GAS.gamma - 1); beta = (GAS.gamma - 1) / 2
    def residual(mach): return np.sqrt(GAS.gamma * GAS.R * t0 / (1 + beta * mach**2)) * (mach - 2 / (GAS.gamma - 1)) - target
    assert residual(0.) * residual(1.) >= 0
    with pytest.raises(ValueError): subsonic_total_inlet_state(interior, 200000., t0, GAS)


@pytest.mark.parametrize("velocity", (-1., 400.))
def test_invalid_initial_inlet_is_rejected_before_cfl(monkeypatch, velocity):
    import scramjet1d.solver as solver
    monkeypatch.setattr(solver, "cfl_timestep", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("CFL reached")))
    with pytest.raises(ValueError): solve_quasi_1d(_state(u=velocity, n=8), constant_area_profile(8), .1, 1e-5, GAS, NUMERICAL, boundary_conditions=_conditions(_state()))


def test_no_root_initial_inlet_is_rejected_before_cfl(monkeypatch):
    import scramjet1d.solver as solver
    monkeypatch.setattr(solver, "cfl_timestep", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("CFL reached")))
    conditions = BoundaryConditions(inlet="subsonic-total-inflow", inlet_total_pressure=200000., inlet_total_temperature=1000.)
    with pytest.raises(ValueError): solve_quasi_1d(_state(n=8), constant_area_profile(8), .1, 1e-5, GAS, NUMERICAL, boundary_conditions=conditions)


@pytest.mark.parametrize("velocity", (-1., 400.))
def test_invalid_rk_stage_inlet_is_rejected(monkeypatch, velocity):
    import scramjet1d.solver as solver
    def invalid_stage(state, dt, rhs):
        stage = state.copy(); stage[0] = _state(u=velocity)[0]; return rhs(stage)
    monkeypatch.setattr(solver, "ssp_rk3_step", invalid_stage)
    initial = _state(n=8)
    with pytest.raises(ValueError): solve_quasi_1d(initial, constant_area_profile(8), .1, 1e-5, GAS, NUMERICAL, boundary_conditions=_conditions(initial))


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_identity_boundary_flux_equals_euler_flux(scheme):
    states = _state(n=8); flux = boundary_interface_fluxes(states, GAS, _conditions(states), scheme=scheme)[0]
    assert_allclose(flux, euler_flux(states[0], GAS), rtol=0, atol=1e-7)


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_batched_reconstruction_and_flux_match_per_sample_loop(scheme):
    states = np.stack((_state(n=8), _state(rho=1.1, u=180., p=95000., n=8))); p0, t0 = _totals(states[0, 0]); conditions = BoundaryConditions(inlet="subsonic-total-inflow", inlet_total_pressure=p0, inlet_total_temperature=t0)
    reconstruction = subsonic_total_inlet_state(states[..., 0, :], p0, t0, GAS); expected_reconstruction = np.stack([subsonic_total_inlet_state(sample[0], p0, t0, GAS) for sample in states])
    fluxes = boundary_interface_fluxes(states, GAS, conditions, scheme=scheme); expected_fluxes = np.stack([boundary_interface_fluxes(sample, GAS, conditions, scheme=scheme) for sample in states])
    assert reconstruction.shape == (2, 3) and fluxes.shape == (2, 9, 3)
    assert_allclose(reconstruction, expected_reconstruction, rtol=0, atol=0); assert_allclose(fluxes, expected_fluxes, rtol=0, atol=0)


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_full_physical_uniform_flow_is_steady(scheme):
    states = _state(n=8); geometry = constant_area_profile(8); conditions = _conditions(states)
    assert_allclose(quasi_1d_rhs(states, geometry, .1, GAS, flux_scheme=scheme, boundary_conditions=conditions), 0., rtol=0, atol=1e-6)
    result = solve_quasi_1d(states, geometry, .1, 5e-4, GAS, NUMERICAL, flux_scheme=scheme, boundary_conditions=conditions)
    assert result.steps > 1; assert_allclose(result.U, states, rtol=0, atol=1e-8)


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_controlled_total_condition_mismatch_remains_physical(scheme):
    states = _state(n=8); result = solve_quasi_1d(states, constant_area_profile(8), .1, 1e-4, GAS, NUMERICAL, flux_scheme=scheme, boundary_conditions=_conditions(states, 1.01, 1.005)); q = conservative_to_primitive(result.U, GAS)
    assert result.steps > 1 and result.time == 1e-4 and np.all(np.isfinite(result.U)); assert np.all(q.rho > 0) and np.all(q.p > 0) and np.all(q.T > 0)


def test_sources_compose_with_physical_boundaries_and_inputs_remain_immutable():
    states = _state(n=8); original = states.copy(); geometry = constant_area_profile(8, .02); cell_area, face_area = geometry.cell_area.copy(), geometry.face_area.copy(); conditions = _conditions(states)
    wall = dict(hydraulic_diameter=.1, darcy_friction_factor=.01, wall_heat_flux=20000.); fuel = dict(fuel_mass_flow_rate_per_length=.002, fuel_axial_velocity=100., fuel_specific_total_enthalpy=1e6); combustion = dict(fuel_burn_rate_per_length=.0002, fuel_lower_heating_value=40e6)
    base = quasi_1d_rhs(states, geometry, .1, GAS, boundary_conditions=conditions); actual = quasi_1d_rhs(states, geometry, .1, GAS, boundary_conditions=conditions, **wall, **fuel, **combustion)
    expected = base + combined_wall_source(states, **wall, gas=GAS) + distributed_fuel_injection_source(states, geometry, **fuel, gas=GAS) + distributed_combustion_heat_release_source(states, geometry, **combustion, gas=GAS)
    assert_allclose(actual, expected, rtol=0, atol=1e-10); assert_allclose(states, original, rtol=0, atol=0); assert_allclose(geometry.cell_area, cell_area, rtol=0, atol=0); assert_allclose(geometry.face_area, face_area, rtol=0, atol=0)
    with pytest.raises(FrozenInstanceError): conditions.inlet_total_pressure = 1.0
