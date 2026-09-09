"""P7.3 solver integration checks for distributed fuel injection."""
import numpy as np
import pytest
from numpy.testing import assert_allclose
from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.geometry import constant_area_profile
from scramjet1d.solver import quasi_1d_rhs_transmissive, solve_quasi_1d
from scramjet1d.state import primitive_to_conservative, conservative_to_primitive

GAS=GasProperties()
def state(n=12): return primitive_to_conservative(np.ones(n),np.full(n,500.),np.full(n,100000.),GAS)

@pytest.mark.parametrize("scheme",["rusanov","steger-warming"])
def test_uniform_fuel_source_is_integrated_exactly(scheme):
    U0=state(); area=.02; mprime=.02; t=.0001
    result=solve_quasi_1d(U0,constant_area_profile(12,area),1/12,t,GAS,NumericalConfig(cfl=.5),flux_scheme=scheme,fuel_mass_flow_rate_per_length=mprime,fuel_axial_velocity=100.,fuel_specific_total_enthalpy=1e6)
    exact=U0+np.array([1.,100.,1e6])*t
    assert_allclose(result.U,exact,rtol=1e-12,atol=1e-8)
    prim=conservative_to_primitive(result.U,GAS)
    assert np.all(prim.rho>0)&np.all(prim.p>0)&np.all(prim.T>0)

def test_explicit_zero_fuel_is_identical_to_default():
    U0=state(); geo=constant_area_profile(12,.02); args=(U0,geo,1/12,.0001,GAS,NumericalConfig(cfl=.5))
    default=solve_quasi_1d(*args); zero=solve_quasi_1d(*args,fuel_mass_flow_rate_per_length=0.,fuel_axial_velocity=0.,fuel_specific_total_enthalpy=0.)
    assert default.time==zero.time and default.steps==zero.steps
    assert_allclose(default.U,zero.U,rtol=0,atol=0)

@pytest.mark.parametrize("kwargs",[{"fuel_mass_flow_rate_per_length":-1.},{"fuel_mass_flow_rate_per_length":np.nan},{"fuel_axial_velocity":np.nan},{"fuel_specific_total_enthalpy":np.inf}])
def test_invalid_fuel_configuration_fails_early(kwargs):
    with pytest.raises(ValueError): solve_quasi_1d(state(),constant_area_profile(12,.02),1/12,.0001,GAS,NumericalConfig(),**kwargs)
