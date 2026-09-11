"""Hard gates for P9.1 physical supersonic boundary semantics."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.boundary import BoundaryConditions, PrimitiveBoundaryState, boundary_interface_fluxes
from scramjet1d.config import GasProperties, NumericalConfig
from scramjet1d.flux import euler_flux
from scramjet1d.geometry import constant_area_profile
from scramjet1d.solver import quasi_1d_rhs, quasi_1d_rhs_transmissive, solve_quasi_1d
from scramjet1d.source_terms import combined_wall_source, distributed_combustion_heat_release_source, distributed_fuel_injection_source
from scramjet1d.state import primitive_to_conservative


GAS = GasProperties(gamma=1.4, R=287.0)
NUMERICAL = NumericalConfig(cfl=0.2)
INLET = PrimitiveBoundaryState(rho=1.0, u=700.0, p=101_325.0)
PHYSICAL = BoundaryConditions(inlet="supersonic-inflow", outlet="supersonic-outflow", inlet_state=INLET)


def _state(rho: float = 1.0, u: float = 700.0, p: float = 101_325.0, n: int = 8) -> np.ndarray:
    return primitive_to_conservative(np.full(n, rho), np.full(n, u), np.full(n, p), GAS)


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_supersonic_boundary_fluxes_are_physical_and_inlet_is_invariant(scheme: str) -> None:
    from scramjet1d.boundary import boundary_interface_fluxes

    first_a = _state(); first_b = _state(rho=0.85, u=760.0, p=95_000.0)
    first_b[1:] = first_a[1:]
    for state in (first_a, first_b):
        faces = boundary_interface_fluxes(state, GAS, PHYSICAL, scheme=scheme)
        assert_allclose(faces[0], euler_flux(primitive_to_conservative(INLET.rho, INLET.u, INLET.p, GAS), GAS), rtol=0.0, atol=1e-10)
        assert_allclose(faces[-1], euler_flux(state[-1], GAS), rtol=0.0, atol=1e-10)
    assert_allclose(boundary_interface_fluxes(first_a, GAS, PHYSICAL, scheme=scheme)[0], boundary_interface_fluxes(first_b, GAS, PHYSICAL, scheme=scheme)[0], rtol=0.0, atol=0.0)


def test_boundary_configuration_is_immutable_and_rejects_invalid_states() -> None:
    with pytest.raises(FrozenInstanceError):
        INLET.u = 1.0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        PHYSICAL.outlet = "transmissive"  # type: ignore[misc]
    for kwargs in ({"rho": 0.0, "u": 700.0, "p": 1.0}, {"rho": 1.0, "u": np.inf, "p": 1.0}, {"rho": 1.0, "u": 700.0, "p": 0.0}):
        with pytest.raises(ValueError): PrimitiveBoundaryState(**kwargs)
    with pytest.raises(ValueError): BoundaryConditions(inlet="unknown")
    with pytest.raises(ValueError): BoundaryConditions(outlet="unknown")
    with pytest.raises(ValueError): BoundaryConditions(inlet="transmissive", inlet_state=INLET)


@pytest.mark.parametrize(
    "conditions",
    (
        BoundaryConditions(inlet="supersonic-inflow"),
        BoundaryConditions(inlet="supersonic-inflow", inlet_state=PrimitiveBoundaryState(1.0, -700.0, 101_325.0)),
        BoundaryConditions(inlet="supersonic-inflow", inlet_state=PrimitiveBoundaryState(1.0, 300.0, 101_325.0)),
        BoundaryConditions(outlet="supersonic-outflow"),
    ),
)
def test_invalid_physical_boundaries_fail_before_cfl(monkeypatch: pytest.MonkeyPatch, conditions: BoundaryConditions) -> None:
    import scramjet1d.solver as solver

    def forbidden_cfl(*args: object, **kwargs: object) -> float:
        raise AssertionError("CFL must not be reached")

    monkeypatch.setattr(solver, "cfl_timestep", forbidden_cfl)
    state = _state(u=300.0) if conditions.outlet == "supersonic-outflow" else _state()
    with pytest.raises(ValueError):
        solve_quasi_1d(state, constant_area_profile(state.shape[0]), 0.1, 1.0e-5, GAS, NUMERICAL, boundary_conditions=conditions)


def test_rhs_rejects_a_supersonic_outflow_violation_at_a_stage() -> None:
    stage_state = _state(); stage_state[-1] = primitive_to_conservative(1.0, 300.0, 101_325.0, GAS)
    with pytest.raises(ValueError):
        quasi_1d_rhs(stage_state, constant_area_profile(stage_state.shape[0]), .1, GAS, boundary_conditions=PHYSICAL)


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_legacy_transmissive_api_and_default_solver_are_unchanged(scheme: str) -> None:
    state = _state(); geometry = constant_area_profile(state.shape[0])
    assert_allclose(quasi_1d_rhs_transmissive(state, geometry, .1, GAS, flux_scheme=scheme), quasi_1d_rhs(state, geometry, .1, GAS, flux_scheme=scheme, boundary_conditions=BoundaryConditions()), rtol=0.0, atol=0.0)
    default = solve_quasi_1d(state, geometry, .1, 2.0e-5, GAS, NUMERICAL, flux_scheme=scheme)
    explicit = solve_quasi_1d(state, geometry, .1, 2.0e-5, GAS, NUMERICAL, flux_scheme=scheme, boundary_conditions=BoundaryConditions())
    assert_allclose(default.U, explicit.U, rtol=0.0, atol=0.0)


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_uniform_supersonic_state_is_steady_and_mismatch_stays_physical(scheme: str) -> None:
    state = _state(); geometry = constant_area_profile(state.shape[0])
    assert_allclose(quasi_1d_rhs(state, geometry, .1, GAS, flux_scheme=scheme, boundary_conditions=PHYSICAL), 0.0, rtol=0.0, atol=1e-9)
    steady = solve_quasi_1d(state, geometry, .1, 3.0e-5, GAS, NUMERICAL, flux_scheme=scheme, boundary_conditions=PHYSICAL)
    assert_allclose(steady.U, state, rtol=0.0, atol=1e-8)
    mismatch = solve_quasi_1d(_state(p=99_500.0), geometry, .1, 3.0e-5, GAS, NUMERICAL, flux_scheme=scheme, boundary_conditions=PHYSICAL)
    assert mismatch.steps > 1 and mismatch.time == 3.0e-5
    assert np.all(np.isfinite(mismatch.U))


def test_physical_boundaries_preserve_existing_combustion_source_and_inputs() -> None:
    state = _state(); original = state.copy(); geometry = constant_area_profile(state.shape[0]); areas = geometry.cell_area.copy()
    rhs = quasi_1d_rhs(state, geometry, .1, GAS, boundary_conditions=PHYSICAL, fuel_burn_rate_per_length=.001, fuel_lower_heating_value=40e6)
    assert np.all(rhs[:, 2] > 0.0)
    assert_allclose(state, original, rtol=0.0, atol=0.0); assert_allclose(geometry.cell_area, areas, rtol=0.0, atol=0.0)


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_batched_transmissive_rhs_remains_backward_compatible(scheme: str) -> None:
    geometry = constant_area_profile(8); states = np.stack((_state(), _state(rho=.9, u=720., p=98_000.)))
    original = states.copy(); cell_area = geometry.cell_area.copy(); face_area = geometry.face_area.copy()
    legacy = quasi_1d_rhs_transmissive(states, geometry, .1, GAS, flux_scheme=scheme)
    generic = quasi_1d_rhs(states, geometry, .1, GAS, flux_scheme=scheme, boundary_conditions=BoundaryConditions())
    expected = np.stack([quasi_1d_rhs_transmissive(sample, geometry, .1, GAS, flux_scheme=scheme) for sample in states])
    assert legacy.shape == (2, 8, 3) and np.all(np.isfinite(legacy))
    assert_allclose(legacy, generic, rtol=0.0, atol=0.0); assert_allclose(legacy, expected, rtol=0.0, atol=0.0)
    assert_allclose(states, original, rtol=0.0, atol=0.0); assert_allclose(geometry.cell_area, cell_area, rtol=0.0, atol=0.0); assert_allclose(geometry.face_area, face_area, rtol=0.0, atol=0.0)


@pytest.mark.parametrize("scheme", ("rusanov", "steger-warming"))
def test_batched_physical_boundary_fluxes_preserve_per_batch_semantics(scheme: str) -> None:
    states = np.stack((_state(), _state(rho=.9, u=720., p=98_000.)))
    fluxes = boundary_interface_fluxes(states, GAS, PHYSICAL, scheme=scheme)
    inlet_flux = euler_flux(primitive_to_conservative(INLET.rho, INLET.u, INLET.p, GAS), GAS)
    assert fluxes.shape == (2, 9, 3)
    assert_allclose(fluxes[..., 0, :], np.broadcast_to(inlet_flux, (2, 3)), rtol=0.0, atol=1e-10)
    assert_allclose(fluxes[..., -1, :], euler_flux(states[..., -1, :], GAS), rtol=0.0, atol=1e-10)


def test_physical_boundary_rhs_composes_wall_fuel_and_combustion_sources() -> None:
    state = _state(); geometry = constant_area_profile(8, .02)
    wall = dict(hydraulic_diameter=.1, darcy_friction_factor=.01, wall_heat_flux=20_000.)
    fuel = dict(fuel_mass_flow_rate_per_length=.002, fuel_axial_velocity=100., fuel_specific_total_enthalpy=1e6)
    burn = dict(fuel_burn_rate_per_length=.0002, fuel_lower_heating_value=40e6)
    base = quasi_1d_rhs(state, geometry, .1, GAS, boundary_conditions=PHYSICAL)
    actual = quasi_1d_rhs(state, geometry, .1, GAS, boundary_conditions=PHYSICAL, **wall, **fuel, **burn)
    expected = base + combined_wall_source(state, **wall, gas=GAS) + distributed_fuel_injection_source(state, geometry, **fuel, gas=GAS) + distributed_combustion_heat_release_source(state, geometry, **burn, gas=GAS)
    assert_allclose(actual, expected, rtol=0.0, atol=1e-10)
