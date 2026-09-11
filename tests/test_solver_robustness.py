"""P9.4 runtime diagnostics and controlled long-run robustness gates."""

import numpy as np
import pytest

from scramjet1d.boundary import BoundaryConditions
from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.geometry import constant_area_profile
from scramjet1d.solver import solve_quasi_1d_steady
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative

GAS = GasProperties()


def _state(n=8):
    return primitive_to_conservative(np.full(n, 1.2), np.full(n, 200.), np.full(n, 100000.), GAS)


def _conditions(states):
    q = conservative_to_primitive(states, GAS); beta = (GAS.gamma - 1) / 2
    return BoundaryConditions(inlet="subsonic-total-inflow", outlet="subsonic-pressure", inlet_total_pressure=float(q.p[0] * (1 + beta * q.Mach[0] ** 2) ** (GAS.gamma / (GAS.gamma - 1))), inlet_total_temperature=float(q.T[0] * (1 + beta * q.Mach[0] ** 2)), outlet_static_pressure=float(q.p[0]))


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_combined_sources_remain_physical_over_controlled_pseudotime(scheme):
    states = _state(); result = solve_quasi_1d_steady(states, constant_area_profile(8, .02), .1, 1e-4, GAS, NumericalConfig(cfl=.2, tolerance=1e-12), flux_scheme=scheme, boundary_conditions=_conditions(states), hydraulic_diameter=.1, darcy_friction_factor=.001, wall_heat_flux=1000., fuel_mass_flow_rate_per_length=.0001, fuel_axial_velocity=100., fuel_specific_total_enthalpy=1e6, fuel_burn_rate_per_length=.00001, fuel_lower_heating_value=40e6)
    q = conservative_to_primitive(result.U, GAS)
    assert np.all(np.isfinite(result.U)) and np.all(q.rho > 0) and np.all(q.p > 0) and np.all(q.T > 0)
    assert np.all(np.isfinite(result.residual_history))


def test_runtime_failure_includes_step_time_context_and_cause(monkeypatch):
    import scramjet1d.solver as solver
    def broken_step(state, dt, rhs): raise ValueError("injected invalid stage")
    monkeypatch.setattr(solver, "ssp_rk3_step", broken_step)
    with pytest.raises(RuntimeError, match=r"SSP-RK3.*step 0, time=") as error:
        solve_quasi_1d_steady(_state(), constant_area_profile(8), .1, 1e-4, GAS, NumericalConfig(), boundary_conditions=_conditions(_state(8) + np.array([0., 0., 1000.])))
    assert isinstance(error.value.__cause__, ValueError)


@pytest.mark.parametrize("cap", ("max_steps", "max_time"))
def test_convergence_wins_over_the_final_cap_step(monkeypatch, cap):
    import scramjet1d.solver as solver
    values = iter((1.0, 1e-8))
    monkeypatch.setattr(solver, "normalized_steady_residual", lambda rhs, reference: next(values))
    kwargs = dict(max_steps=1) if cap == "max_steps" else dict()
    duration = 1.0 if cap == "max_steps" else 1e-5
    result = solve_quasi_1d_steady(_state(), constant_area_profile(8), .1, duration, GAS, NumericalConfig(tolerance=1e-6), boundary_conditions=_conditions(_state(8) + np.array([0., 0., 1000.])), **kwargs)
    assert result.converged and result.termination_reason == "converged" and result.steps == 1


def test_array_source_inputs_remain_unchanged():
    states = _state(); arrays = [np.full(8, value) for value in (.001, 1000., .0001, 100., 1e6, .00001, 40e6)]
    original = [value.copy() for value in arrays]
    solve_quasi_1d_steady(states, constant_area_profile(8, .02), .1, 1e-5, GAS, NumericalConfig(tolerance=1e-12), boundary_conditions=_conditions(states), hydraulic_diameter=.1, darcy_friction_factor=arrays[0], wall_heat_flux=arrays[1], fuel_mass_flow_rate_per_length=arrays[2], fuel_axial_velocity=arrays[3], fuel_specific_total_enthalpy=arrays[4], fuel_burn_rate_per_length=arrays[5], fuel_lower_heating_value=arrays[6])
    for actual, expected in zip(arrays, original):
        assert np.array_equal(actual, expected)
