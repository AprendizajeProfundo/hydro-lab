"""Noisy controller-facing observations, independent from physical scenario streams."""
from dataclasses import dataclass
import numpy as np

OBSERVATION_NAMES = (
    'volume0_measured_m3','volume4_measured_m3','demand_measured_m3_s',
    'tariff_um_kwh','previous_flow_measured_m3_s',
    'previous_p1_measured_pa','previous_p2_measured_pa','previous_p3_measured_pa',
    'previous_u0','previous_uN','previous_uS','time_fraction',
    'health_estimate_p0','health_estimate_pN','health_estimate_pS',
)

@dataclass
class HealthBelief:
    """Conservative non-Bayesian estimator; no access to latent pump health."""
    estimate: np.ndarray
    uncertainty: np.ndarray

    @classmethod
    def initial(cls):
        return cls(np.full(3, .95, dtype=np.float64), np.full(3, .05, dtype=np.float64))

    def predict(self):
        self.uncertainty = np.minimum(.35, self.uncertainty + .001)

    def inspect(self, pump_index: int, measured_health: float, alpha: float = .8):
        if pump_index not in (0,1,2) or not np.isfinite(measured_health):
            raise ValueError('Invalid inspection')
        measured_health = float(np.clip(measured_health, .65, 1.))
        self.estimate[pump_index] = np.clip((1-alpha)*self.estimate[pump_index] + alpha*measured_health, .65, 1.)
        self.uncertainty[pump_index] = max(.02, (1-alpha)*self.uncertainty[pump_index])


def observe(*, volume0: float, volume4: float, demand: float, price: float,
            previous_flow: float, previous_pressures: tuple[float,float,float],
            previous_action: tuple[float,float,float], t: int,
            belief: HealthBelief, rng: np.random.Generator) -> np.ndarray:
    """15-dimensional noisy observation, no hidden state or future information.

    Pressure from closed branches is represented as zero (sensor unavailable);
    no fictitious physical pressure is created by this convention.
    """
    pressure = [float(np.clip(x + rng.normal(0.,3000.), 0.,600000.)) if np.isfinite(x) else 0.
                for x in previous_pressures]
    result = np.array([
        np.clip(volume0+rng.normal(0.,2.),200.,1500.),
        np.clip(volume4+rng.normal(0.,2.),200.,1500.),
        np.clip(demand+rng.normal(0.,.003),0.,.17),
        price,
        np.clip(previous_flow+rng.normal(0.,.002),0.,.30),
        *pressure,*previous_action,t/96.,*belief.estimate,
    ], dtype=np.float32)
    return result
