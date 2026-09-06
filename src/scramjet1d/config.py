"""Central configuration values reserved for later development stages."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GasProperties:
    """Calorically perfect gas parameters; units: R in J/(kg K)."""

    gamma: float = 1.4
    R: float = 287.0


@dataclass(frozen=True)
class NumericalConfig:
    """Numerical-control parameters reserved for later solver stages."""

    cfl: float = 0.5
    tolerance: float = 1.0e-4

