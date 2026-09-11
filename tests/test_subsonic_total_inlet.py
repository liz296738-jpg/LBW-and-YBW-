"""P9.3 characteristic total-condition inlet hard gates."""
import numpy as np
import pytest
from numpy.testing import assert_allclose
from scramjet1d.boundary import BoundaryConditions, boundary_interface_fluxes, subsonic_total_inlet_state
from scramjet1d.config import GasProperties
from scramjet1d.gas import speed_of_sound
from scramjet1d.spatial import internal_numerical_fluxes
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative

GAS = GasProperties()
def state(rho=1.2, u=200., p=100000.): return primitive_to_conservative(rho,u,p,GAS)
def totals(U):
    q=conservative_to_primitive(U,GAS); b=(GAS.gamma-1)/2
    return float(q.p*(1+b*q.Mach**2)**(GAS.gamma/(GAS.gamma-1))),float(q.T*(1+b*q.Mach**2))

def test_total_inlet_reconstructs_total_conditions_and_jminus():
    U=state(); p0,T0=totals(U); B=subsonic_total_inlet_state(U,p0,T0,GAS)
    i,b=conservative_to_primitive(U,GAS),conservative_to_primitive(B,GAS); ai,ab=speed_of_sound(i.T,GAS),speed_of_sound(b.T,GAS)
    assert_allclose(B,U,rtol=0,atol=1e-9); assert_allclose(totals(B),(p0,T0),rtol=0,atol=1e-9)
    assert_allclose(b.u-2*ab/(GAS.gamma-1),i.u-2*ai/(GAS.gamma-1),rtol=0,atol=1e-9)

@pytest.mark.parametrize('bad',[(None,300.),(200000.,None),(0.,300.),(200000.,0.)])
def test_total_inlet_configuration_rejects_missing_or_invalid(bad):
    with pytest.raises(ValueError): BoundaryConditions(inlet='subsonic-total-inflow',inlet_total_pressure=bad[0],inlet_total_temperature=bad[1])

@pytest.mark.parametrize('scheme',['rusanov','steger-warming'])
def test_total_inlet_flux_and_batches(scheme):
    U=np.stack([np.tile(state(),(8,1)),np.tile(state(1.1,180.,95000.),(8,1))]); p0,T0=totals(U[0,0]); c=BoundaryConditions(inlet='subsonic-total-inflow',inlet_total_pressure=p0,inlet_total_temperature=T0)
    F=boundary_interface_fluxes(U,GAS,c,scheme=scheme); B=subsonic_total_inlet_state(U[...,0,:],p0,T0,GAS)
    expected=internal_numerical_fluxes(np.stack((B,U[...,0,:]),axis=-2),GAS,scheme=scheme)[...,0,:]
    assert F.shape==(2,9,3); assert_allclose(F[...,0,:],expected,rtol=0,atol=1e-10)

@pytest.mark.parametrize('u',[0.,-1.,400.])
def test_total_inlet_rejects_invalid_interior(u):
    with pytest.raises(ValueError): subsonic_total_inlet_state(state(u=u),200000.,300.,GAS)
