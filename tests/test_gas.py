"""Tests for ideal, calorically perfect gas relations."""

import numpy as np
import pytest

from scramjet1d.config import GasProperties
import scramjet1d.gas as gas_module


GAS = GasProperties()
P_REF = 101_325.0
T_REF = 288.15
RHO_REF = P_REF / (GAS.R * T_REF)


def test_equation_of_state_and_temperature_inverse() -> None:
    """Pressure and temperature forms of the ideal-gas law are inverses."""
    pressure = gas_module.pressure_from_density_temperature(RHO_REF, T_REF, GAS)
    temperature = gas_module.temperature_from_density_pressure(RHO_REF, P_REF, GAS)

    assert pressure == pytest.approx(P_REF, rel=1e-12)
    assert temperature == pytest.approx(T_REF, rel=1e-12)


def test_speed_of_sound_internal_and_total_energy_and_mach() -> None:
    """Thermodynamic utility values agree with their defining relations."""
    velocity = 500.0
    sound_speed = gas_module.speed_of_sound(T_REF, GAS)
    internal_energy = gas_module.specific_internal_energy(P_REF, RHO_REF, GAS)
    total_energy = gas_module.specific_total_energy(RHO_REF, velocity, P_REF, GAS)
    mach = gas_module.mach_number(velocity, T_REF, GAS)

    assert sound_speed == pytest.approx(340.3, abs=0.2)
    assert internal_energy == pytest.approx(P_REF / (RHO_REF * (GAS.gamma - 1)))
    assert total_energy == pytest.approx(internal_energy + velocity**2 / 2)
    assert mach == pytest.approx(velocity / sound_speed, rel=1e-12)


def test_thermodynamic_functions_vectorize() -> None:
    """Temperature-based relations broadcast over NumPy arrays."""
    temperature = np.array([250.0, 300.0, 1000.0])
    density = np.array([1.0, 0.9, 0.3])

    pressure = gas_module.pressure_from_density_temperature(density, temperature, GAS)
    sound_speed = gas_module.speed_of_sound(temperature, GAS)

    assert pressure.shape == (3,)
    assert sound_speed.shape == (3,)
    assert np.isfinite(pressure).all()
    assert np.isfinite(sound_speed).all()


@pytest.mark.parametrize("rho", [0.0, -1.0, np.nan, np.inf])
def test_pressure_rejects_invalid_density(rho: float) -> None:
    """Density must be finite and strictly positive."""
    with pytest.raises(ValueError, match="rho"):
        gas_module.pressure_from_density_temperature(rho, T_REF, GAS)


@pytest.mark.parametrize("temperature", [0.0, -1.0, np.nan, np.inf])
def test_sound_speed_rejects_invalid_temperature(temperature: float) -> None:
    """Temperature must be finite and strictly positive."""
    with pytest.raises(ValueError, match="T"):
        gas_module.speed_of_sound(temperature, GAS)


@pytest.mark.parametrize("pressure", [0.0, -1.0, np.nan, np.inf])
def test_internal_energy_rejects_invalid_pressure(pressure: float) -> None:
    """Pressure must be finite and strictly positive."""
    with pytest.raises(ValueError, match="p"):
        gas_module.specific_internal_energy(pressure, RHO_REF, GAS)

