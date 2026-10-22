"""S2.6 headless orchestration for the Streamlit teaching interface.

Never pass info/evaluation_truth to the policy; traces are evaluation artifacts.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
import numpy as np
from .environment import HydroLabEnv
from .benchmark import POLICIES, paired_benchmark, save_report
from .scenarios import Scenario, generate_scenario
from .robot import InspectionRobot, ROBOT_ACTIONS, choose_uncertainty_action, choose_value_action

POLICY_CHOICES = ('constant', 'demand_feedback', 'health_aware', 'health_robust', 'manual')
ROBOT_POLICIES = ('off', 'manual', 'uncertainty', 'value')


def normalized_action(speeds):
    """Physical pump speeds in [0.6,1.0] -> normalized Gymnasium actions."""
    a = np.asarray(speeds, dtype=float)
    if a.shape != (3,) or not np.isfinite(a).all() or np.any(a < .6) or np.any(a > 1.):
        raise ValueError('Three finite pump speeds in [0.6,1.0] required')
    return np.asarray(np.clip((a - .8)/.2, -1., 1.), dtype=np.float32)


def safe_filename(prefix: str, seed: int) -> str:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    return f'{prefix}_seed_{int(seed)}_{stamp}.json'


@dataclass
class EpisodeSession:
    seed: int
    policy_name: str = 'demand_feedback'
    nominal: bool = False
    max_steps: int = 96
    robot_policy: str = 'off'
    scenario: Scenario | None = None
    robot: InspectionRobot = field(init=False, repr=False)
    robot_rng: np.random.Generator = field(init=False, repr=False)
    env: HydroLabEnv = field(init=False, repr=False)
    observation: np.ndarray = field(init=False, repr=False)
    records: list[dict] = field(default_factory=list)
    finished: bool = False
    reward_total: float = 0.
    terminated: bool = False
    truncated: bool = False

    def __post_init__(self):
        if self.policy_name not in POLICY_CHOICES:
            raise ValueError('Unknown policy')
        if not 1 <= self.max_steps <= 96:
            raise ValueError('max_steps must be 1..96')
        if self.robot_policy not in ROBOT_POLICIES:
            raise ValueError('Unknown robot policy')
        self.robot = InspectionRobot()
        self.robot_rng = np.random.default_rng(np.random.SeedSequence([int(self.seed), 2707]))
        self.env = HydroLabEnv(max_steps=self.max_steps)
        if self.scenario is not None and self.nominal:
            raise ValueError('scenario and nominal cannot be combined')
        if self.scenario is not None and self.scenario.seed != self.seed:
            raise ValueError('Scenario seed must match episode seed')
        options = {'scenario': self.scenario} if self.scenario is not None else ({'scenario': generate_scenario(self.seed, steps=self.max_steps, nominal=True)} if self.nominal else None)
        self.observation, _ = self.env.reset(seed=int(self.seed), options=options)

    def step(self, manual_speeds=(.8,.8,.8), robot_action: str = 'wait') -> dict:
        if self.finished:
            raise RuntimeError('Episode already finished; create a new episode')
        if self.robot_policy == 'manual' and robot_action not in ROBOT_ACTIONS:
            raise ValueError('Unknown robot action')
        if self.policy_name == 'manual':
            action = normalized_action(manual_speeds)
        else:
            action = POLICIES[self.policy_name](self.observation.copy())
        before = self.observation.copy()
        next_obs, reward, terminated, truncated, info = self.env.step(action)
        robot_event = None
        if self.robot_policy != 'off':
            chosen = (choose_uncertainty_action(self.robot, self.env.belief)
                      if self.robot_policy == 'uncertainty' else
                      choose_value_action(self.robot, self.env.belief)
                      if self.robot_policy == 'value' else robot_action)
            if chosen not in ROBOT_ACTIONS:
                raise ValueError('Unknown robot action')
            # The simulator sensor is the only privileged bridge to true health.
            # It emits a noisy measurement; the controller sees only the updated belief.
            robot_event = self.robot.act(chosen, health=self.env.health,
                                         belief=self.env.belief, rng=self.robot_rng)
            reward = float(reward) - robot_event['cost_um']
            if not (terminated or truncated):
                next_obs = next_obs.copy()
                next_obs[12:15] = self.env.belief.estimate.astype(np.float32)
        self.reward_total += float(reward)
        self.terminated = bool(terminated)
        self.truncated = bool(truncated)
        self.finished = self.terminated or self.truncated
        self.observation = next_obs
        truth = info.get('evaluation_truth', {})
        rec = {
            'step': len(self.records)+1,
            'hour': (len(self.records)+1)*.25,
            'reward': float(reward),
            'cumulative_reward': self.reward_total,
            'observed_demand_m3_s': float(before[2]),
            'observed_volume0_m3': float(before[0]),
            'observed_volume4_m3': float(before[1]),
            'observed_tariff_um_kwh': float(before[3]),
            'controller_health_observation': list(map(float, before[12:15])),
            'action_requested': list(map(float, info['action_requested'])),
            'action_executed': list(map(float, info['action_executed'])),
            'intervention_reason': info.get('intervention_reason'),
            'energy_kwh': float(info.get('energy_kwh', 0.)),
            'served_m3': float(info.get('served_m3', 0.)),
            'unserved_m3': float(info.get('unserved_m3', 0.)),
            'mass_error_m3': float(info.get('mass_error_m3', 0.)),
            'costs': {**dict(info['costs']), 'inspection_um': (robot_event or {}).get('cost_um', 0.)},
            'robot': robot_event,
            'hydraulic_status': info.get('hydraulic_status', 'TERMINATED'),
            'terminated': self.terminated,
            'truncated': self.truncated,
            'termination_reason': info.get('termination_reason'),
            # Offline diagnostics, never used by controller.
            'evaluation_true_volumes_m3': list(map(float,truth.get('volumes_m3', ()))),
            'evaluation_true_health': list(map(float,truth.get('health', ()))),
            'evaluation_availability': list(map(bool,truth.get('availability', ()))),
        }
        self.records.append(rec)
        return rec

    def advance(self, steps: int = 1, manual_speeds=(.8,.8,.8), robot_action: str = 'wait') -> list[dict]:
        if not 1 <= steps <= 96:
            raise ValueError('steps must be 1..96')
        new = []
        for _ in range(steps):
            if self.finished:
                break
            new.append(self.step(manual_speeds, robot_action=robot_action))
        return new

    def report(self) -> dict:
        return {
            'schema': 'hydro-lab-s2.8-episode-v1',
            'robot_policy': self.robot_policy,
            'robot_summary': {'position':self.robot.position, 'battery':self.robot.battery,
                'moves':self.robot.moves,'inspections':self.robot.inspections,
                'cost_um':self.robot.cost_um, 'energy_used':self.robot.energy_used},
            'seed': int(self.seed), 'policy': self.policy_name,
            'nominal': self.nominal, 'max_steps': self.max_steps,
            'steps': len(self.records), 'finished': self.finished,
            'terminated': self.terminated, 'truncated': self.truncated,
            'reward_total': self.reward_total,
            'total_energy_kwh': sum(r['energy_kwh'] for r in self.records),
            'total_unserved_m3': sum(r['unserved_m3'] for r in self.records),
            'interventions': sum(r['intervention_reason'] is not None for r in self.records),
            'records': self.records,
        }

    def json_bytes(self) -> bytes:
        return (json.dumps(self.report(), ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')

    def close(self):
        self.env.close()


def run_comparison(seeds: tuple[int, ...]) -> dict:
    return paired_benchmark(seeds)


def persist_episode(session: EpisodeSession, folder: str | Path = 'results') -> Path:
    path = Path(folder) / safe_filename('control_center_episode', session.seed)
    return save_report(session.report(), path)
