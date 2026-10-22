"""S2.7 discrete inspection robot. Its sensor is a privileged simulator service;
controllers receive only the noisy result, never latent health.
One robot action is executed after each 15-minute hydraulic transition.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import deque
import numpy as np

STATIONS = ('BASE', 'P0', 'PN', 'PS')
# This is a logistics/access graph, NOT the hydraulic pipe graph.
ROADS = (('BASE', 'P0'), ('P0', 'PN'), ('P0', 'PS'))
PUMP_INDEX = {'P0': 0, 'PN': 1, 'PS': 2}
ROBOT_ACTIONS = ('wait', 'move_BASE', 'move_P0', 'move_PN', 'move_PS', 'inspect')

@dataclass
class InspectionRobot:
    position: str = 'BASE'
    battery: float = 100.
    moves: int = 0
    inspections: int = 0
    energy_used: float = 0.
    cost_um: float = 0.
    events: list[dict] = field(default_factory=list)
    move_battery: float = 4.
    inspect_battery: float = 8.
    inspection_sigma: float = .025
    move_cost_um: float = 1.
    inspection_cost_um: float = 3.

    def __post_init__(self):
        if self.position not in STATIONS:
            raise ValueError('Unknown station')
        if not 0 < self.inspection_sigma < .2:
            raise ValueError('Invalid sensor precision')

    def neighbors(self):
        return tuple(b if a == self.position else a for a,b in ROADS if self.position in (a,b))

    def shortest_route(self, target: str):
        if target not in STATIONS: raise ValueError('Unknown target')
        queue=deque([(self.position, ())]);seen={self.position}
        while queue:
            pos,path=queue.popleft()
            if pos==target:return path
            for a,b in ROADS:
                nxt=b if pos==a else a if pos==b else None
                if nxt is not None and nxt not in seen:
                    seen.add(nxt);queue.append((nxt,path+(nxt,)))
        raise ValueError('No accessible route')

    def act(self, action: str, *, health: tuple[float,...], belief, rng: np.random.Generator) -> dict:
        if action not in ROBOT_ACTIONS:raise ValueError('Unknown robot action')
        event={'action':action,'position_before':self.position,'position_after':self.position,
               'status':'WAIT','measurement':None,'pump':None,'cost_um':0.,'battery_before':self.battery}
        if action.startswith('move_'):
            target=action[5:]
            if target not in self.neighbors():
                event['status']='BLOCKED_ROUTE'
            elif self.battery < self.move_battery:
                event['status']='INSUFFICIENT_BATTERY'
            else:
                self.position=target;self.battery-=self.move_battery
                self.energy_used+=self.move_battery;self.moves+=1
                self.cost_um+=self.move_cost_um;event['cost_um']=self.move_cost_um
                event['status']='MOVED';event['position_after']=target
        elif action=='inspect':
            if self.position not in PUMP_INDEX:
                event['status']='NO_PUMP_AT_STATION'
            elif self.battery < self.inspect_battery:
                event['status']='INSUFFICIENT_BATTERY'
            else:
                idx=PUMP_INDEX[self.position]
                measurement=float(np.clip(health[idx]+rng.normal(0.,self.inspection_sigma),.65,1.))
                belief.inspect(idx,measurement)
                self.battery-=self.inspect_battery;self.energy_used+=self.inspect_battery
                self.inspections+=1;self.cost_um+=self.inspection_cost_um
                event.update(status='INSPECTED',measurement=measurement,pump=self.position,
                             cost_um=self.inspection_cost_um)
        event['battery_after']=self.battery
        event['belief_estimates']=list(map(float,belief.estimate))
        event['belief_uncertainty']=list(map(float,belief.uncertainty))
        self.events.append(event)
        return event


def choose_uncertainty_action(robot: InspectionRobot, belief) -> str:
    """Transparent heuristic: inspect largest uncertainty, travel via shortest path.
    Not an optimal value-of-information policy and not a learned agent.
    """
    idx=int(np.argmax(belief.uncertainty));target=STATIONS[idx+1]
    if robot.position==target:
        return 'inspect' if robot.battery>=robot.inspect_battery else 'wait'
    route=robot.shortest_route(target)
    return 'move_'+route[0] if route and robot.battery>=robot.move_battery else 'wait'


def choose_value_action(robot: InspectionRobot, belief, *, threshold: float = .043,
                        risk_weight: float = 1.5, inspection_budget: int = 3) -> str:
    """S2.10: cost-aware, observation-only teaching heuristic (NOT exact VOI).

    A candidate is worthwhile when uncertainty multiplied by a health-risk
    factor exceeds a threshold plus a travel/inspection opportunity penalty.
    Stop when no candidate clears the threshold. A visit can be repeated only
    if uncertainty grows enough to justify it; a hard budget bounds costs.
    No true health, future shocks or evaluation diagnostics are used.
    """
    if inspection_budget < 0 or threshold < 0 or risk_weight < 0:
        raise ValueError('Invalid cost-aware policy parameters')
    if robot.inspections >= inspection_budget:
        return 'wait'
    scores = []
    for idx, station in enumerate(STATIONS[1:]):
        route = robot.shortest_route(station)
        distance = len(route)
        battery_needed = distance * robot.move_battery + robot.inspect_battery
        if robot.battery < battery_needed:
            scores.append(float('-inf'))
            continue
        uncertainty = float(belief.uncertainty[idx])
        health = float(belief.estimate[idx])
        risk = 1. + risk_weight * max(0., .95 - health) / .30
        # Travel has a real cost: one UM per edge; inspection costs three UM.
        # Threshold is an illustrative decision score, not calibrated money.
        score = uncertainty * risk - .004 * distance
        scores.append(score)
    idx = int(np.argmax(scores))
    if scores[idx] <= threshold:
        return 'wait'
    target = STATIONS[idx+1]
    if robot.position == target:
        return 'inspect'
    route = robot.shortest_route(target)
    return 'move_' + route[0] if route else 'wait'
