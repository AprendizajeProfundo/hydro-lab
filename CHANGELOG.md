# Registro de generaciones y entregas

## S2.1 — G2.4 (2026-10-19)

- Proyecto Python con empaquetado `src/`, dependencias y pruebas.
- Topología, incidencia y parámetros nominales según especificación G2.4.
- Matriz de CI macOS / Windows / Linux.
- Sin solver ni algoritmos; ninguna ecuación de G2.4 modificada.
- Estado de validación: pruebas locales ejecutadas; CI multiplataforma pendiente.

## S2.2 — G2.4 (2026-10-19)

- Nuevo `hydraulics.py`: pérdidas cuadráticas, curvas de bombas, eficiencia y potencia.
- Solver de dos ramas y solver unidimensional para ramas cerradas.
- Reconstrucción de alturas, presiones y verificaciones físicas.
- Estados de factibilidad y parada segura explícita.
- Pruebas hidráulicas; se conservan las 13 pruebas S2.1.
- Limitación: inventarios y seguridad de transición pendientes S2.3.

## S2.3 — G2.4 (2026-10-19)

- Conservative inventory transition and delivered demand without clipping.
- Independent seeded stochastic streams for demand, viscosity, health and failures.
- 15-minute sequential dynamics, health deterioration, failure masks and energy/tariff costs.
- Deterministic safety grid with safe shutdown and explicit terminal contingency.
- JSON traces with overwrite protection and new tests.
- S2.1/S2.2 unchanged; no Gymnasium, PPO or robot yet.

## S2.4 — G2.4 (2026-10-19)

- Gymnasium `HydroLabEnv`: normalized `Box(3)` actions, 15-dimensional observation, reset/step API.
- Sensor noise uses a separate seeded stream; the underlying scenario and physical dynamics are unchanged.
- Health belief is initialized to 0.95 and can update from inspections; no hidden true health is used in the observation.
- Reuses the S2.3 deterministic safety grid and conservative inventory transition.
- `evaluation_truth` in `info` is **offline diagnostics only**; do not expose it to training policies.
- Gymnasium contract, observation, seed and conservation tests added.

## S2.5 — Scientific acceptance and baselines
- Two observation-only policies: constant and demand-feedback.
- Paired scenario-seed benchmarking, reward/cost accounting, termination and safety metrics.
- Reproducible JSON reports with no-overwrite behavior.
- Fifteen additional tests for leakage boundaries, accounting, reproducibility and report integrity.
- No PPO training; no claim of industrial calibration or policy optimality.


## S2.6 — Hydro-Lab Control Center
- Nuevo `hydro_lab.control_center` para episodios paso a paso, trazas JSON,
  acciones manuales y benchmark pareado.
- Nuevo `dashboard/app.py` con Streamlit y Plotly.
- Extra opcional `ui` para instalar dependencias de la interfaz.
- Pruebas unitarias del controlador de interfaz sin modificar las pruebas S2.1–S2.5.

## S2.7 — Robot de inspección y observación activa (2026-10-20)
- Robot discreto con grafo logístico independiente de tuberías, batería, movimientos, inspecciones y costos.
- Inspecciones ruidosas actualizan `HealthBelief`, sin reparación física ni acceso de la política a salud verdadera.
- Modo manual y heurística de priorización por incertidumbre; modo apagado compatible con S2.6.
- Nueva pestaña de robot en Streamlit, eventos y exportación de reportes S2.7.
- Pruebas nuevas en `tests/test_robot_s27.py`; validación integral pendiente de ejecución en entorno con Gymnasium.

## S2.8 — Integración experimental de observación activa y control hidráulico
- Nuevo controlador `health_aware` que utiliza las estimaciones observadas de salud, sin acceder a estados verdaderos.
- Contrato temporal explícito: inspección al final del paso, efecto en el siguiente paso.
- Nuevo experimento factorial pareado de cuatro brazos con recompensa neta y costos robóticos.
- Nuevas gráficas de estimación e incertidumbre y controles de benchmark S2.8.
- Cinco pruebas automatizadas adicionales; ejecución completa pendiente de validación en Mac.
- Se conservan las correcciones manuales del S2.7 recibido.

## S2.9 — Scientific validation of active observation
- Added controlled synthetic degraded and accelerated-wear scenarios (predeclared, not field calibrated).
- Added reproducible 2×2 controller/robot factorial benchmark across matched seeds and three regimes.
- Separately reports hydraulic benefit, robot cost, net benefit, energy, unmet demand, and action changes.
- Added machine-readable JSON, CSV, Markdown report; refuses to overwrite existing results.
- Added regression tests and command-line experiment runner; S2.8 remains unchanged.

## S2.10 — Control robusto y observación costo-consciente

- Se agrega controlador `health_robust` (redistribución conservadora por salud estimada).
- Se agrega política robótica `value` (heurística costo-consciente que puede esperar, con límite de inspecciones).
- Se extiende la interfaz Streamlit con ambas opciones.
- Se añade `examples/compare_s210.py`, `teaching_comparison.py` y pruebas específicas.
- Se preservan los algoritmos y experimentos de S2.9; S2.10 es una carpeta nueva.
- La política `value` NO es un cálculo exacto del valor esperado de la información.
