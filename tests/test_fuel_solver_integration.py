"""P7.3 solver integration checks for distributed fuel injection."""
import numpy as np
import pytest
from numpy.testing import assert_allclose
from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.geometry import constant_area_profile
from scramjet1d.solver import quasi_1d_rhs_transmissive, solve_quasi_1d
from scramjet1d.boundary import transmissive_ghost_cells
from scramjet1d.spatial import internal_numerical_fluxes, quasi_1d_residual
from scramjet1d.source_terms import combined_wall_source, distributed_fuel_injection_source
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

@pytest.mark.parametrize("scheme",["rusanov","steger-warming"])
def test_rhs_matches_manual_fuel_and_wall_composition(scheme):
    U=primitive_to_conservative(np.array([1.,.9,1.1]),np.array([300.,350.,250.]),np.array([1e5,1.1e5,.9e5]),GAS)
    geo=constant_area_profile(3,.02); dx=.1; m=np.array([.01,.02,.03]); v=np.array([10.,20.,30.]); h=np.array([1e5,2e5,3e5])
    base=quasi_1d_residual(U,internal_numerical_fluxes(transmissive_ghost_cells(U),GAS,scheme=scheme),geo,dx,GAS)
    fuel=distributed_fuel_injection_source(U,geo,m,v,h,GAS)
    actual=quasi_1d_rhs_transmissive(U,geo,dx,GAS,flux_scheme=scheme,fuel_mass_flow_rate_per_length=m,fuel_axial_velocity=v,fuel_specific_total_enthalpy=h)
    assert_allclose(actual,base+fuel,rtol=0,atol=1e-10)
    wall=combined_wall_source(U,.1,.01,20000.,GAS)
    both=quasi_1d_rhs_transmissive(U,geo,dx,GAS,flux_scheme=scheme,hydraulic_diameter=.1,darcy_friction_factor=.01,wall_heat_flux=20000.,fuel_mass_flow_rate_per_length=m,fuel_axial_velocity=v,fuel_specific_total_enthalpy=h)
    assert_allclose(both,base+wall+fuel,rtol=0,atol=1e-10)

@pytest.mark.parametrize("kwargs",[{"fuel_mass_flow_rate_per_length":-1.},{"fuel_mass_flow_rate_per_length":np.nan},{"fuel_axial_velocity":np.nan},{"fuel_specific_total_enthalpy":np.inf}])
def test_invalid_fuel_configuration_fails_early(kwargs):
    with pytest.raises(ValueError): solve_quasi_1d(state(),constant_area_profile(12,.02),1/12,.0001,GAS,NumericalConfig(),**kwargs)

def test_fuel_source_is_re_evaluated_for_three_distinct_rk_stages(monkeypatch):
    import scramjet1d.solver as solver_module
    calls=[]; original=solver_module.distributed_fuel_injection_source
    def wrapped(U, geometry, fuel_mass_flow_rate_per_length, fuel_axial_velocity, fuel_specific_total_enthalpy, gas):
        calls.append((np.array(U, copy=True), geometry, np.array(fuel_mass_flow_rate_per_length, copy=True), np.array(fuel_axial_velocity, copy=True), np.array(fuel_specific_total_enthalpy, copy=True)))
        return original(U, geometry, fuel_mass_flow_rate_per_length, fuel_axial_velocity, fuel_specific_total_enthalpy, gas)
    monkeypatch.setattr(solver_module, "distributed_fuel_injection_source", wrapped)
    solve_quasi_1d(state(), constant_area_profile(12,.02), 1/12, 1e-6, GAS, NumericalConfig(cfl=.5), fuel_mass_flow_rate_per_length=.02, fuel_axial_velocity=100., fuel_specific_total_enthalpy=1e6)
    stages=calls[-3:]
    assert len(stages)==3
    assert np.max(np.abs(stages[0][0]-stages[1][0]))>0
    assert np.max(np.abs(stages[1][0]-stages[2][0]))>0
    assert all(item[1] is stages[0][1] for item in stages)

def test_wall_only_equals_wall_with_explicit_zero_fuel():
    args=(state(),constant_area_profile(12,.02),1/12,1e-5,GAS,NumericalConfig(cfl=.5))
    a=solve_quasi_1d(*args,hydraulic_diameter=.1,darcy_friction_factor=.01,wall_heat_flux=20000.)
    b=solve_quasi_1d(*args,hydraulic_diameter=.1,darcy_friction_factor=.01,wall_heat_flux=20000.,fuel_mass_flow_rate_per_length=0.,fuel_axial_velocity=0.,fuel_specific_total_enthalpy=0.)
    assert_allclose(a.U,b.U,rtol=0,atol=0); assert a.time==b.time and a.steps==b.steps
