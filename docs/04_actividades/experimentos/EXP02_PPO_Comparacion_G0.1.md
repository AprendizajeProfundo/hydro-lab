# EXP02 — ¿Aprende PPO una política mejor y robusta?

**Generación:** G0.1 · **Lecciones:** L03–L04 · **Plataforma:** Hydro-Lab S2.11 (por desarrollar)

## Pregunta científica

¿En qué condiciones una política PPO entrenada en Hydro-Lab supera a los controladores de referencia, y qué ocurre cuando cambian las condiciones de operación?

## Hipótesis y advertencia

**H1:** PPO puede mejorar el retorno esperado en escenarios similares a los de entrenamiento. **H2:** una mejora del retorno no garantiza mejor servicio, menor desgaste o menos intervenciones de seguridad. **H3:** el desempeño puede deteriorarse ante escenarios fuera de distribución. Son hipótesis, no resultados obtenidos.

## Diseño mínimo

1. Congelar una versión del entorno, la recompensa y los parámetros físicos.
2. Definir particiones disjuntas de entrenamiento, validación y prueba, con semillas documentadas.
3. Entrenar varias réplicas independientes de PPO; guardar checkpoints, normalizadores, hiperparámetros y registros.
4. Evaluar PPO y los controladores de referencia sobre **los mismos escenarios de prueba**.
5. Reportar retorno, energía, servicio, déficit, maniobras, intervenciones y terminaciones por separado; mostrar distribución entre escenarios y semillas.
6. Repetir la evaluación bajo perturbaciones no utilizadas para seleccionar el modelo.
7. Discutir fallos, sobreajuste, costo de entrenamiento y límites de seguridad.

## Evidencia para la clase

- Curva de aprendizaje con variabilidad entre réplicas.
- Comparación pareada de desempeño en escenarios reservados.
- Trayectoria detallada de un episodio ilustrativo, incluyendo acciones solicitadas y ejecutadas.
- Un caso de éxito y un caso de fallo o deterioro bajo estrés.

## Actividad conceptual

Antes de observar los resultados, pedir a los estudiantes que predigan qué ocurrirá con energía, déficit e intervenciones cuando el agente prioriza la recompensa. Después contrastar la predicción con los gráficos. La práctica se ejecuta en Hydro-Lab; no requiere escribir código ni comprender las ecuaciones de PPO.

## Estado

**Diseño experimental inicial.** No existen todavía resultados PPO verificados en esta generación; no inventar curvas, cifras ni conclusiones.
