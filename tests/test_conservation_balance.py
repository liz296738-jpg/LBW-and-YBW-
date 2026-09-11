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
def test_physical_subsonic_boundary_ledger_closes(scheme):
    state = primitive_to_conservative(np.full(8, 1.2), np.full(8, 200.), np.full(8, 100000.), GAS)
    q = state[0]; rho, momentum, energy = q; velocity = momentum / rho; pressure = (GAS.gamma - 1) * (energy - .5 * rho * velocity**2); temperature = pressure / (rho * GAS.R); mach = velocity / np.sqrt(GAS.gamma * GAS.R * temperature); beta = (GAS.gamma - 1) / 2
    conditions = BoundaryConditions(inlet="subsonic-total-inflow", outlet="subsonic-pressure", inlet_total_pressure=pressure * (1 + beta * mach**2) ** (GAS.gamma / (GAS.gamma - 1)), inlet_total_temperature=temperature * (1 + beta * mach**2), outlet_static_pressure=pressure)
    balance = quasi_1d_conservation_balance(state, constant_area_profile(8), .1, GAS, flux_scheme=scheme, boundary_conditions=conditions)
    assert_allclose(balance.closure_error, 0., rtol=0, atol=1e-8)
