"""Immutable G2.4 topology. Incidence convention: -1 source, +1 destination."""
from __future__ import annotations
import numpy as np
from numpy.typing import NDArray

NODES: tuple[int, ...] = (0, 1, 2, 3, 4)
EDGES: tuple[tuple[int, int], ...] = ((0, 1), (1, 2), (2, 4), (1, 3), (3, 4))
PUMP_EDGES: dict[str, tuple[int, int]] = {"P0": (0, 1), "PN": (1, 2), "PS": (1, 3)}
PASSIVE_EDGES: tuple[tuple[int, int], ...] = ((2, 4), (3, 4))

def incidence_matrix() -> NDArray[np.int64]:
    """Return 5x5 node-edge incidence matrix B with columns in EDGES order."""
    b = np.zeros((len(NODES), len(EDGES)), dtype=np.int64)
    for j, (src, dst) in enumerate(EDGES):
        b[src, j] = -1
        b[dst, j] = +1
    return b

def edge_flows(q_north: float, q_south: float) -> NDArray[np.float64]:
    """Return q=(Q,qN,qN,qS,qS) in m³/s; only nonnegative finite flows accepted."""
    values = np.asarray([q_north, q_south], dtype=float)
    if not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("Branch flows must be finite and nonnegative.")
    north, south = values
    return np.array([north + south, north, north, south, south], dtype=float)

def boundary_balance(q_north: float, q_south: float) -> NDArray[np.float64]:
    """Return expected B@q=(-Q,0,0,0,Q), m³/s."""
    total = q_north + q_south
    return np.array([-total, 0., 0., 0., total], dtype=float)
