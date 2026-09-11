import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.config import GasProperties
from scramjet1d.boundary import BoundaryConditions
from scramjet1d.geometry import constant_area_profile
from scramjet1d.geometry import AreaProfile
from scramjet1d.state import primitive_to_conservative
from scramjet1d.verification import quasi_1d_conservation_balance

GAS = GasProperties()


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_v1_uniform_constant_area_free_stream_is_exactly_balanced(scheme):
    state = primitive_to_conservative(np.full(8, 1.2), np.full(8, 200.), np.full(8, 100000.), GAS)
    balance = quasi_1d_conservation_balance(state, constant_area_profile(8), .1, GAS, flux_scheme=scheme)
    assert_allclose(balance.rhs_integral, 0., rtol=0, atol=1e-8)
    assert_allclose(balance.boundary_flux, 0., rtol=0, atol=1e-8)
    assert_allclose(balance.source_integral, 0., rtol=0, atol=0)
    assert_allclose(balance.closure_error, 0., rtol=0, atol=1e-8)


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_constant_area_nonuniform_global_balance_closes(scheme):
    x = np.linspace(0., 1., 8); state = primitive_to_conservative(1.2 + .01 * np.sin(x), 200. + 2. * np.cos(x), 100000. + 100. * np.sin(x), GAS)
    balance = quasi_1d_conservation_balance(state, constant_area_profile(8), .1, GAS, flux_scheme=scheme)
    assert_allclose(balance.closure_error, 0., rtol=0, atol=1e-8)
    assert_allclose(balance.source_integral, 0., rtol=0, atol=0)


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_variable_area_and_combined_sources_global_balance_close(scheme):
    state = primitive_to_conservative(np.full(8, 1.2), np.full(8, 200.), np.full(8, 100000.), GAS)
    faces = 1. + .02 * np.sin(np.linspace(0., np.pi, 9)); geometry = AreaProfile((faces[:-1] + faces[1:]) / 2., faces)
    balance = quasi_1d_conservation_balance(state, geometry, .1, GAS, flux_scheme=scheme, hydraulic_diameter=.1, darcy_friction_factor=.001, wall_heat_flux=1000., fuel_mass_flow_rate_per_length=.0001, fuel_axial_velocity=100., fuel_specific_total_enthalpy=1e6, fuel_burn_rate_per_length=.00001, fuel_lower_heating_value=40e6)
    assert_allclose(balance.closure_error, 0., rtol=0, atol=1e-8)
    assert_allclose(balance.area_source_integral[[0, 2]], 0., rtol=0, atol=0)
    assert_allclose(balance.fuel_source_integral, [.00008, .008, 80.], rtol=0, atol=1e-12)
    assert_allclose(balance.combustion_source_integral, [0., 0., 320.], rtol=0, atol=1e-12)


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_v3_monotonic_variable_area_has_expected_nonzero_momentum_force(scheme):
    state = primitive_to_conservative(np.full(8, 1.2), np.full(8, 200.), np.full(8, 100000.), GAS)
    faces = np.linspace(1., 1.05, 9); geometry = AreaProfile((faces[:-1] + faces[1:]) / 2., faces)
    balance = quasi_1d_conservation_balance(state, geometry, .1, GAS, flux_scheme=scheme)
    assert_allclose(balance.area_source_integral[[0, 2]], 0., rtol=0, atol=0)
    assert_allclose(balance.area_source_integral[1], 100000. * (faces[-1] - faces[0]), rtol=0, atol=1e-10)
    assert balance.area_source_integral[1] != 0.
    assert_allclose(balance.closure_error, 0., rtol=0, atol=1e-8)


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
@pytest.mark.parametrize("kind", ("wall", "fuel", "combustion"))
def test_v4_to_v6_standalone_source_ledgers_match_authoritative_helpers(scheme, kind):
    state = primitive_to_conservative(np.full(8, 1.2), np.full(8, 200.), np.full(8, 100000.), GAS); geometry = constant_area_profile(8); kwargs = {}
    if kind == "wall":
        kwargs = dict(hydraulic_diameter=.1, darcy_friction_factor=.002, wall_heat_flux=1000.)
        expected_integral = np.array([0., np.sum(-.002/(2*.1)*1.2*200.*abs(200.)*geometry.cell_area*.1), np.sum(4*1000./.1*geometry.cell_area*.1)])
    elif kind == "fuel":
        rate = np.linspace(.0001, .0002, 8); velocity = np.linspace(90., 110., 8); enthalpy = np.linspace(9e5, 1.1e6, 8); kwargs = dict(fuel_mass_flow_rate_per_length=rate, fuel_axial_velocity=velocity, fuel_specific_total_enthalpy=enthalpy)
        expected_integral = np.array([np.sum(rate*.1), np.sum(rate*velocity*.1), np.sum(rate*enthalpy*.1)])
    else:
        burn = np.linspace(.00001, .00002, 8); kwargs = dict(fuel_burn_rate_per_length=burn, fuel_lower_heating_value=40e6)
        expected_integral = np.array([0., 0., np.sum(burn*40e6*.1)])
    balance = quasi_1d_conservation_balance(state, geometry, .1, GAS, flux_scheme=scheme, **kwargs)
    measured = {"wall": balance.wall_source_integral, "fuel": balance.fuel_source_integral, "combustion": balance.combustion_source_integral}[kind]
    assert_allclose(measured, expected_integral, rtol=256*np.finfo(float).eps, atol=256*np.finfo(float).eps*max(1., np.max(np.abs(expected_integral))))
    assert_allclose(balance.closure_error, 0., rtol=0, atol=1e-8)


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_physical_subsonic_boundary_ledger_closes(scheme):
    state = primitive_to_conservative(np.full(8, 1.2), np.full(8, 200.), np.full(8, 100000.), GAS)
    q = state[0]; rho, momentum, energy = q; velocity = momentum / rho; pressure = (GAS.gamma - 1) * (energy - .5 * rho * velocity**2); temperature = pressure / (rho * GAS.R); mach = velocity / np.sqrt(GAS.gamma * GAS.R * temperature); beta = (GAS.gamma - 1) / 2
    conditions = BoundaryConditions(inlet="subsonic-total-inflow", outlet="subsonic-pressure", inlet_total_pressure=pressure * (1 + beta * mach**2) ** (GAS.gamma / (GAS.gamma - 1)), inlet_total_temperature=temperature * (1 + beta * mach**2), outlet_static_pressure=pressure)
    balance = quasi_1d_conservation_balance(state, constant_area_profile(8), .1, GAS, flux_scheme=scheme, boundary_conditions=conditions)
    assert_allclose(balance.closure_error, 0., rtol=0, atol=1e-8)


def test_source_defaults_match_solver_and_batched_states_are_rejected():
    state = primitive_to_conservative(np.full(8, 1.2), np.full(8, 200.), np.full(8, 100000.), GAS)
    balance = quasi_1d_conservation_balance(state, constant_area_profile(8), .1, GAS, hydraulic_diameter=.1)
    assert_allclose(balance.wall_source_integral, 0., rtol=0, atol=0)
    with pytest.raises(ValueError):
        quasi_1d_conservation_balance(np.stack((state, state)), constant_area_profile(8), .1, GAS)


def test_invalid_configs_fail_cleanly_and_inputs_are_immutable():
    state = primitive_to_conservative(np.full(8, 1.2), np.full(8, 200.), np.full(8, 100000.), GAS); original = state.copy(); geometry = constant_area_profile(8); cell_area, face_area = geometry.cell_area.copy(), geometry.face_area.copy()
    arrays = [np.full(8, value) for value in (.002, 1000., .0001, 100., 1e6, .00001, 40e6)]; copies = [value.copy() for value in arrays]
    quasi_1d_conservation_balance(state, geometry, .1, GAS, hydraulic_diameter=.1, darcy_friction_factor=arrays[0], wall_heat_flux=arrays[1], fuel_mass_flow_rate_per_length=arrays[2], fuel_axial_velocity=arrays[3], fuel_specific_total_enthalpy=arrays[4], fuel_burn_rate_per_length=arrays[5], fuel_lower_heating_value=arrays[6])
    assert_allclose(state, original, rtol=0, atol=0); assert_allclose(geometry.cell_area, cell_area, rtol=0, atol=0); assert_allclose(geometry.face_area, face_area, rtol=0, atol=0)
    for actual, expected in zip(arrays, copies): assert_allclose(actual, expected, rtol=0, atol=0)
    for kwargs in (dict(fuel_burn_rate_per_length=.1), dict(hydraulic_diameter=None, darcy_friction_factor=.1)):
        with pytest.raises(ValueError): quasi_1d_conservation_balance(state, geometry, .1, GAS, **kwargs)
    with pytest.raises(ValueError): quasi_1d_conservation_balance(state, geometry, 0., GAS)
    with pytest.raises(ValueError): quasi_1d_conservation_balance(state, geometry, .1, GAS, flux_scheme="unknown")
