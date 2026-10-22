"""G2.4 fixed synthetic parameters. No calibration or hydraulic solver in S2.1."""
from __future__ import annotations
from dataclasses import dataclass, field
from .topology import EDGES

@dataclass(frozen=True)
class TankParameters:
    base_elevation_m: float
    area_m2: float = 250.0
    initial_volume_m3: float = 500.0
    min_volume_m3: float = 200.0
    max_volume_m3: float = 1500.0

    def __post_init__(self) -> None:
        if self.area_m2 <= 0 or not self.min_volume_m3 <= self.initial_volume_m3 <= self.max_volume_m3:
            raise ValueError("Invalid tank geometry or inventory limits.")

    def head_m(self, volume_m3: float) -> float:
        if not self.min_volume_m3 <= volume_m3 <= self.max_volume_m3:
            raise ValueError("Volume outside operating range.")
        return self.base_elevation_m + volume_m3 / self.area_m2

@dataclass(frozen=True)
class PumpParameters:
    name: str
    edge: tuple[int, int]
    a_m: float
    b_s2_m5: float
    reference_flow_m3_s: float

@dataclass(frozen=True)
class NetworkParameters:
    """G2.4 nominal constants; tuples preserve edge/pump ordering."""
    density_kg_m3: float = 850.0
    gravity_m_s2: float = 9.81
    reference_viscosity_pa_s: float = 0.020
    resistance_viscosity_exponent: float = 0.20
    resistances_s2_m5: tuple[float, ...] = (900., 800., 800., 1100., 1100.)
    lengths_m: tuple[float, ...] = (2000., 1500., 1500., 1800., 1800.)
    diameter_m: float = 0.30
    internal_elevations_m: tuple[float, float, float] = (11., 13., 13.)
    max_internal_pressure_pa: float = 600_000.
    max_velocity_m_s: float = 3.0
    time_step_s: int = 900
    episode_steps: int = 96
    discount_factor: float = 0.99
    supply_nominal_m3_s: float = 0.11
    demand_nominal_m3_s: float = 0.11
    origin: TankParameters = field(default_factory=lambda: TankParameters(10., 250., 750.))
    receiver: TankParameters = field(default_factory=lambda: TankParameters(16., 250., 500.))
    pumps: tuple[PumpParameters, ...] = field(default_factory=lambda: (
        PumpParameters("P0", (0, 1), 25., 250., 0.12),
        PumpParameters("PN", (1, 2), 16., 500., 0.06),
        PumpParameters("PS", (1, 3), 16., 500., 0.06),
    ))

    def __post_init__(self) -> None:
        if len(self.resistances_s2_m5) != len(EDGES) or len(self.lengths_m) != len(EDGES):
            raise ValueError("One resistance and length per edge required.")
        if any(r <= 0 for r in self.resistances_s2_m5):
            raise ValueError("Resistances must be positive.")
        if tuple(p.edge for p in self.pumps) != ((0, 1), (1, 2), (1, 3)):
            raise ValueError("Pump topology differs from G2.4.")
