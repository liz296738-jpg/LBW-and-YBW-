"""Central physical and numerical configuration values."""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class GasProperties:
    """Calorically perfect gas parameters; units: R in J/(kg K)."""

    gamma: float = 1.4
    R: float = 287.0

    def __post_init__(self) -> None:
        """Validate the thermodynamic constants."""
        if not isfinite(self.gamma) or self.gamma <= 1.0:
            raise ValueError("gamma must be finite and greater than 1")
        if not isfinite(self.R) or self.R <= 0.0:
            raise ValueError("R must be finite and strictly positive")

    @property
    def cv(self) -> float:
        """Constant-volume specific heat [J/(kg K)]."""
        return self.R / (self.gamma - 1.0)

    @property
    def cp(self) -> float:
        """Constant-pressure specific heat [J/(kg K)]."""
        return self.gamma * self.R / (self.gamma - 1.0)


@dataclass(frozen=True)
class NumericalConfig:
    """Numerical-control parameters reserved for later solver stages."""

    cfl: float = 0.5
    tolerance: float = 1.0e-4

    def __post_init__(self) -> None:
        """Validate positive controls without imposing a CFL upper bound."""
        if not isfinite(self.cfl) or self.cfl <= 0.0:
            raise ValueError("cfl must be finite and strictly positive")
        if not isfinite(self.tolerance) or self.tolerance <= 0.0:
            raise ValueError("tolerance must be finite and strictly positive")
