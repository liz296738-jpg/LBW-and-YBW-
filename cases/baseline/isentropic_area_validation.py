"""Run controlled isentropic quasi-1D area-physics validation without plotting."""

from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from scramjet1d.config import GasProperties
from scramjet1d.flux import euler_flux
from scramjet1d.geometry import AreaProfile
from scramjet1d.isentropic import isentropic_nozzle_reference
from scramjet1d.solver import quasi_1d_rhs_transmissive
from scramjet1d.spatial import quasi_1d_residual
from scramjet1d.state import primitive_to_conservative


P0 = 300_000.0
T0 = 500.0


def profile(num_cells: int) -> AreaProfile:
    """Return a smooth diverging area profile over a unit-length uniform grid."""
    face_area = np.linspace(1.0, 1.2, num_cells + 1)
    return AreaProfile(0.5 * (face_area[:-1] + face_area[1:]), face_area)


def momentum_rms(residual: np.ndarray) -> float:
    """Return RMS of a residual momentum component in SI units."""
    return float(np.sqrt(np.mean(residual[..., 1] ** 2)))


def exact_face_error(num_cells: int, gas: GasProperties) -> float:
    """Return controlled analytical-face geometry consistency error."""
    geometry = profile(num_cells)
    cell = isentropic_nozzle_reference(geometry.cell_area, 1.0, 0.5, P0, T0, gas, "subsonic")
    face = isentropic_nozzle_reference(geometry.face_area, 1.0, 0.5, P0, T0, gas, "subsonic")
    U_cell = primitive_to_conservative(cell.rho, cell.u, cell.p, gas)
    F_face = euler_flux(primitive_to_conservative(face.rho, face.u, face.p, gas), gas)
    return momentum_rms(quasi_1d_residual(U_cell, F_face, geometry, 1.0 / num_cells, gas))


def rusanov_error(num_cells: int, gas: GasProperties) -> float:
    """Return actual baseline interior Rusanov consistency error."""
    geometry = profile(num_cells)
    cell = isentropic_nozzle_reference(geometry.cell_area, 1.0, 0.5, P0, T0, gas, "subsonic")
    U_cell = primitive_to_conservative(cell.rho, cell.u, cell.p, gas)
    return momentum_rms(quasi_1d_rhs_transmissive(U_cell, geometry, 1.0 / num_cells, gas)[2:-2])


def observed_orders(errors: list[float]) -> list[float]:
    """Return successive refinement orders for halved uniform-grid spacing."""
    return [float(np.log(errors[i] / errors[i + 1]) / np.log(2.0)) for i in range(len(errors) - 1)]


def print_reference(label: str, mach: float, gas: GasProperties) -> None:
    """Print inlet/outlet state and mass-flow variation for a branch reference."""
    area = np.linspace(1.0, 1.2, 41)
    state = isentropic_nozzle_reference(area, 1.0, mach, P0, T0, gas, label)
    mass_flow = state.rho * state.u * area
    variation = (np.max(mass_flow) - np.min(mass_flow)) / abs(np.mean(mass_flow))
    print(f"{label}: inlet A={area[0]:.6g}, M={state.Mach[0]:.8f}, u={state.u[0]:.8f}, p={state.p[0]:.8f}")
    print(f"{label}: outlet A={area[-1]:.6g}, M={state.Mach[-1]:.8f}, u={state.u[-1]:.8f}, p={state.p[-1]:.8f}")
    print(f"{label}: mass-flow relative variation={variation:.3e}")


def main() -> None:
    """Run both branch references and both controlled convergence checks."""
    gas = GasProperties()
    print_reference("subsonic", 0.5, gas)
    print_reference("supersonic", 2.0, gas)
    exact_errors = [exact_face_error(count, gas) for count in (40, 80, 160)]
    rusanov_errors = [rusanov_error(count, gas) for count in (80, 160, 320)]
    print(f"exact-face RMS (40/80/160)={exact_errors}")
    print(f"exact-face orders={observed_orders(exact_errors)}")
    print(f"Rusanov interior RMS (80/160/320)={rusanov_errors}")
    print(f"Rusanov interior orders={observed_orders(rusanov_errors)}")


if __name__ == "__main__":
    main()
