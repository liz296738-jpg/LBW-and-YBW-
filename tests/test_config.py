"""Tests for centralized physical and numerical configuration."""

import math

import pytest

from scramjet1d.config import GasProperties, NumericalConfig


def test_default_air_properties_and_heat_capacities() -> None:
    """Default air properties derive the expected constant heat capacities."""
    gas = GasProperties()

    assert gas.gamma == 1.4
    assert gas.R == 287.0
    assert gas.cv == pytest.approx(717.5)
    assert gas.cp == pytest.approx(1004.5)
    assert gas.cp - gas.cv == pytest.approx(gas.R)


@pytest.mark.parametrize("gamma", [1.0, 0.9, math.nan, math.inf])
def test_gas_rejects_gamma_not_greater_than_one(gamma: float) -> None:
    """A calorically perfect gas requires gamma greater than one."""
    with pytest.raises(ValueError, match="gamma"):
        GasProperties(gamma=gamma)


@pytest.mark.parametrize("R", [0.0, -287.0, math.nan, math.inf])
def test_gas_rejects_nonpositive_specific_gas_constant(R: float) -> None:
    """The specific gas constant must be strictly positive."""
    with pytest.raises(ValueError, match="R"):
        GasProperties(R=R)


@pytest.mark.parametrize(
    "kwargs",
    [{"cfl": 0.0}, {"tolerance": 0.0}, {"cfl": math.inf}, {"tolerance": math.nan}],
)
def test_numerical_config_rejects_nonpositive_controls(kwargs: dict[str, float]) -> None:
    """Reserved numerical controls must be strictly positive."""
    with pytest.raises(ValueError):
        NumericalConfig(**kwargs)
