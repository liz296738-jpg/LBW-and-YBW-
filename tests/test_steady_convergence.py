"""P9.4 steady residual and termination contracts."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.boundary import BoundaryConditions
from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.geometry import constant_area_profile
from scramjet1d.solver import (
    SolverResult,
    normalized_steady_residual,
    solve_quasi_1d,
    solve_quasi_1d_steady,
    steady_residual_reference,
)
from scramjet1d.state import conservative_to_primitive, primitive_to_conservative


GAS = GasProperties()


def _state(pressure=100_000.0, n=8):
    return primitive_to_conservative(np.full(n, 1.2), np.full(n, 200.0), np.full(n, pressure), GAS)


def _conditions(states):
    primitive = conservative_to_primitive(states, GAS)
    beta = (GAS.gamma - 1.0) / 2.0
    p0 = float(primitive.p[0] * (1 + beta * primitive.Mach[0] ** 2) ** (GAS.gamma / (GAS.gamma - 1)))
    t0 = float(primitive.T[0] * (1 + beta * primitive.Mach[0] ** 2))
    return BoundaryConditions(inlet="subsonic-total-inflow", outlet="subsonic-pressure", inlet_total_pressure=p0, inlet_total_temperature=t0, outlet_static_pressure=float(primitive.p[0]))


def test_residual_reference_and_normalization_follow_documented_formula():
    states = _state(); reference = steady_residual_reference(states, .1, GAS)
    rhs = np.zeros_like(states); rhs[:, 0] = 2.; rhs[:, 1] = 3.; rhs[:, 2] = 4.
    primitive = conservative_to_primitive(states, GAS)
    speed = np.max(np.abs(primitive.u) + np.sqrt(GAS.gamma * GAS.R * primitive.T))
    expected_scales = np.array([np.max(primitive.rho), np.max(primitive.rho) * speed, np.max(np.abs(states[:, 2]))])
    assert_allclose(reference.time_scale, states.shape[0] * .1 / speed, rtol=0, atol=1e-15)
    assert_allclose(reference.conservative_scales, expected_scales, rtol=0, atol=0)
    assert_allclose(normalized_steady_residual(rhs, reference), np.max(reference.time_scale * np.array([2., 3., 4.]) / expected_scales), rtol=0, atol=1e-15)


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_exact_uniform_physical_state_converges_without_a_step(scheme):
    states = _state(); result = solve_quasi_1d_steady(states, constant_area_profile(8), .1, 1., GAS, NumericalConfig(tolerance=1e-8), flux_scheme=scheme, boundary_conditions=_conditions(states))
    assert result.converged and result.termination_reason == "converged"
    assert result.steps == 0 and result.time == 0.
    assert result.residual_history.shape == (1,) and result.time_history.tolist() == [0.]
    assert not np.shares_memory(result.U, states)


def test_normal_termination_reports_max_time_and_history_contract():
    states = _state(); result = solve_quasi_1d_steady(states, constant_area_profile(8), .1, 1e-6, GAS, NumericalConfig(tolerance=1e-14), boundary_conditions=_conditions(_state(101_000.)))
    assert not result.converged and result.termination_reason == "max-time" and result.time == 1e-6
    assert len(result.residual_history) == result.steps + 1 == len(result.time_history)
    assert np.all(np.isfinite(result.residual_history)) and np.all(result.residual_history >= 0.)
    assert np.all(np.diff(result.time_history) > 0.)


def test_normal_termination_reports_max_steps_and_legacy_solver_contract_is_unchanged():
    states = _state(); result = solve_quasi_1d_steady(states, constant_area_profile(8), .1, 1., GAS, NumericalConfig(tolerance=1e-14), max_steps=1, boundary_conditions=_conditions(_state(101_000.)))
    assert not result.converged and result.termination_reason == "max-steps" and result.steps == 1
    transient = solve_quasi_1d(states, constant_area_profile(8), .1, 1e-5, GAS, NumericalConfig())
    assert len(transient) == 3 and isinstance(transient, SolverResult)


@pytest.mark.parametrize("kwargs", (
    dict(hydraulic_diameter=None, darcy_friction_factor=.01),
    dict(fuel_mass_flow_rate_per_length=-.001),
    dict(fuel_burn_rate_per_length=.001, fuel_lower_heating_value=None),
))
def test_invalid_initial_source_configuration_raises_value_error(kwargs):
    with pytest.raises(ValueError):
        solve_quasi_1d_steady(_state(), constant_area_profile(8), .1, 1e-4, GAS, NumericalConfig(), boundary_conditions=_conditions(_state()), **kwargs)


def test_initial_residual_is_independent_of_cfl_and_result_arrays_are_read_only():
    states = _state()
    conditions = _conditions(_state(101000.))
    low = solve_quasi_1d_steady(states, constant_area_profile(8), .1, 1e-6, GAS, NumericalConfig(cfl=.1, tolerance=1e-14), boundary_conditions=conditions)
    high = solve_quasi_1d_steady(states, constant_area_profile(8), .1, 1e-6, GAS, NumericalConfig(cfl=.8, tolerance=1e-14), boundary_conditions=conditions)
    assert_allclose(low.residual_history[0], high.residual_history[0], rtol=0, atol=0)
    assert not low.U.flags.writeable and not low.residual_history.flags.writeable and not low.time_history.flags.writeable
    assert low.time_history[0] == 0 and low.time_history[-1] == low.time and low.residual == low.residual_history[-1]


def test_transient_solver_ignores_steady_tolerance():
    states = _state(101000.)
    loose = solve_quasi_1d(states, constant_area_profile(8), .1, 1e-4, GAS, NumericalConfig(cfl=.2, tolerance=1.))
    strict = solve_quasi_1d(states, constant_area_profile(8), .1, 1e-4, GAS, NumericalConfig(cfl=.2, tolerance=1e-12))
    assert loose.time == strict.time and loose.steps == strict.steps
    assert_allclose(loose.U, strict.U, rtol=0, atol=0)
