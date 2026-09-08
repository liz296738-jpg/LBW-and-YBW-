"""Tests for quasi-1D numerical flux scheme selection."""
import numpy as np
import pytest
from numpy.testing import assert_allclose
from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.geometry import AreaProfile, constant_area_profile
from scramjet1d.boundary import transmissive_ghost_cells
from scramjet1d.spatial import internal_rusanov_fluxes, internal_steger_warming_fluxes, internal_numerical_fluxes, quasi_1d_residual
from scramjet1d.solver import quasi_1d_rhs_transmissive, solve_quasi_1d
from scramjet1d.state import primitive_to_conservative

GAS=GasProperties(); NUM=NumericalConfig()
def U(rho,u,p): return primitive_to_conservative(rho,u,p,GAS)
def test_internal_sw_matches_pairwise_interface_fluxes_and_dispatch():
    states=U(np.ones(5),np.linspace(-200,200,5),np.full(5,1e5))
    sw=internal_steger_warming_fluxes(states,GAS)
    assert sw.shape==(4,3)
    assert_allclose(internal_numerical_fluxes(states,GAS,scheme='steger-warming'),sw)
    assert_allclose(internal_numerical_fluxes(states,GAS,scheme='rusanov'),internal_rusanov_fluxes(states,GAS))
def test_invalid_schemes_fail():
    states=U(np.ones(2),np.zeros(2),np.full(2,1e5))
    for scheme in ('sw','Rusanov',None,1,True):
        with pytest.raises(ValueError): internal_numerical_fluxes(states,GAS,scheme=scheme)
def test_rhs_default_matches_explicit_rusanov_and_sw_manual_assembly():
    states=U([1,.9,1.1],[100,0,-50],[1e5,9e4,1.1e5]); geo=AreaProfile([1.1,1.2,1.3],[1,1.2,1.3,1.4])
    assert_allclose(quasi_1d_rhs_transmissive(states,geo,.1,GAS),quasi_1d_rhs_transmissive(states,geo,.1,GAS,flux_scheme='rusanov'))
    expected=quasi_1d_residual(states,internal_steger_warming_fluxes(transmissive_ghost_cells(states),GAS),geo,.1,GAS)
    assert_allclose(quasi_1d_rhs_transmissive(states,geo,.1,GAS,flux_scheme='steger-warming'),expected)
def test_both_schemes_preserve_uniform_and_static_area_equilibrium():
    uniform=U(np.ones(4),np.full(4,100.),np.full(4,1e5)); const=constant_area_profile(4)
    static=U(np.ones(3),np.zeros(3),np.full(3,1e5)); varied=AreaProfile([1.1,1.2,1.3],[1,1.2,1.3,1.4])
    for scheme in ('rusanov','steger-warming'):
        assert_allclose(quasi_1d_rhs_transmissive(uniform,const,.1,GAS,flux_scheme=scheme),0,atol=1e-10)
        assert_allclose(quasi_1d_rhs_transmissive(static,varied,.1,GAS,flux_scheme=scheme),0,atol=1e-8)
def test_solver_default_is_explicit_rusanov_and_invalid_fails_early():
    initial=U([1,.9,1.1],[100,0,-50],[1e5,9e4,1.1e5]); geo=constant_area_profile(3)
    a=solve_quasi_1d(initial,geo,.05,1e-4,GAS,NUM); b=solve_quasi_1d(initial,geo,.05,1e-4,GAS,NUM,flux_scheme='rusanov')
    assert a.time==b.time and a.steps==b.steps; assert_allclose(a.U,b.U)
    with pytest.raises(ValueError): solve_quasi_1d(initial,geo,.05,1e-4,GAS,NUM,flux_scheme='hll')
