"""Inferencia didáctica para contrastes pareados entre semillas independientes.

Las pruebas t requieren diferencias aproximadamente normales para n pequeño.
No extrapolar la inferencia a sistemas industriales ni a otros escenarios.
"""
from __future__ import annotations

import math
from collections.abc import Sequence
import numpy as np
from scipy.stats import t as student_t


def paired_inference(differences: Sequence[float], *, label: str = 'B − A', alpha: float = 0.05) -> dict:
    d = np.asarray(differences, dtype=float)
    if d.ndim != 1 or d.size == 0 or not np.all(np.isfinite(d)):
        raise ValueError('Se requiere un vector no vacío de diferencias finitas.')
    if not 0 < alpha < 1:
        raise ValueError('alpha debe estar entre cero y uno.')
    n = int(d.size)
    mean = float(d.mean())
    result = dict(contrast=label, n=n, differences=d.tolist(), mean=mean,
                  alpha=alpha, sd=None, se=None, df=None, t=None, p=None,
                  ci_low=None, ci_high=None, status='insufficient')
    if n < 2:
        return result
    sd = float(d.std(ddof=1))
    se = sd / math.sqrt(n)
    result.update(sd=sd, se=se, df=n-1)
    if se == 0:
        # Varianza nula: el estadístico t clásico no está definido.
        result['status'] = 'zero_variance'
        return result
    statistic = mean / se
    critical = float(student_t.ppf(1-alpha/2, n-1))
    result.update(t=float(statistic), p=float(2*student_t.sf(abs(statistic), n-1)),
                  ci_low=float(mean-critical*se), ci_high=float(mean+critical*se),
                  status='ok')
    return result


def holm_adjust(p_values: Sequence[float | None]) -> list[float | None]:
    """Holm step-down; no asigna significación a contrastes no calculables."""
    result: list[float | None] = [None] * len(p_values)
    valid = [(i, float(p)) for i, p in enumerate(p_values) if p is not None and math.isfinite(float(p))]
    if any(not 0 <= p <= 1 for _, p in valid):
        raise ValueError('Los valores p deben pertenecer a [0,1].')
    ordered = sorted(valid, key=lambda item: item[1])
    running = 0.0
    for rank, (i, p) in enumerate(ordered):
        running = max(running, (len(ordered)-rank)*p)
        result[i] = min(1.0, running)
    return result


def fixed_feedback_differences(report: dict) -> list[float]:
    by = {(int(e['seed']), e['policy']): float(e['reward']) for e in report['episodes']}
    return [by[int(s), 'demand_feedback'] - by[int(s), 'constant'] for s in report['seeds']]


def inspection_differences(report: dict) -> list[float]:
    return [float(x) for x in report['paired_net_reward_differences_um']]


def robust_differences(report: dict, regime: str) -> list[float]:
    return [float(x) for x in report['summary'][regime]['paired_robust_value_minus_robust_off']['differences_um']]


def interpretation(result: dict, *, adjusted_p: float | None = None) -> str:
    n = result['n']
    if n < 2:
        return 'Solo hay una pareja: no es posible estimar la variabilidad ni realizar una prueba t pareada.'
    if result['status'] == 'zero_variance':
        return ('Las diferencias observadas son idénticas entre semillas. La desviación estándar es cero; '
                'el estadístico t y su intervalo clásico no están definidos. No se asigna un valor p artificial.')
    p = result['p'] if adjusted_p is None else adjusted_p
    level = result['alpha']
    direction = 'favorece a B' if result['mean'] > 0 else 'favorece a A'
    if p < level:
        core = (f'La diferencia media observada {direction}. Bajo los supuestos de la prueba t pareada, '
                f'existe evidencia estadística de una diferencia media distinta de cero al nivel {level:.0%}'
                + (' después del ajuste de Holm' if adjusted_p is not None else '') + '.')
    else:
        core = (f'No hay evidencia estadística suficiente para establecer una diferencia media distinta de cero '
                f'al nivel {level:.0%}' + (' después del ajuste de Holm' if adjusted_p is not None else '')
                + '. Esto NO demuestra igualdad ni equivalencia de estrategias.')
    caveat = (' Las inferencias se refieren al conjunto de escenarios sintéticos y al mecanismo de semillas '
              'considerado; no garantizan superioridad en cada episodio, seguridad ni validez industrial. '
              'La relevancia operativa debe evaluarse por separado.')
    if n < 10:
        caveat += (' Con menos de diez parejas, la estimación es especialmente sensible a valores extremos '
                   'y al supuesto de normalidad de las diferencias.')
    return core + caveat
