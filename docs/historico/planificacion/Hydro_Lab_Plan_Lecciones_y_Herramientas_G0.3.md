# Hydro-Lab — Plan integrado de lecciones, experimentos y herramientas

**Generación:** G0.3  
**Fecha:** 22 de octubre de 2026  
**Estado:** propuesta consolidada para aprobación académica  
**Documento rector:** `Syllabus_IA_Avanzada_Ecopetrol_Uniandes_G2.3.md`  
**Antecedentes preservados:** `Hydro_Lab_Plan_Lecciones_y_Herramientas_G0.1.md`, `Hydro_Lab_Plan_Lecciones_y_Herramientas_G0.2.md`, `Hydro_Lab_Auditoria_Cobertura_Syllabus_G0.3.md`.

## 1. Propósito y principios innegociables

Este plan traduce **todos los ocho temas del syllabus G2.3** a lecciones de teoría autónomas, experimentos con Hydro-Lab y entregables técnicos verificables. No reemplaza el syllabus ni modifica sus tiempos. La teoría no será un manual de la aplicación. El laboratorio es un instrumento para someter a prueba preguntas derivadas de la teoría; la documentación de ingeniería se conserva por separado.

- **Producto A — Lección teórica:** explicación científica independiente de la interfaz, notación, hipótesis, resultados fundamentales, derivaciones seleccionadas, limitaciones, bibliografía y preguntas de discusión.
- **Producto B — Experimento docente:** pregunta contrastable, hipótesis, diseño, escenarios, semillas, comparadores, métricas, resultados precalculados y discusión; la práctica se realiza en Hydro-Lab.
- **Producto C — Herramienta y documentación técnica:** especificación, código, tests, reproducibilidad, interfaz experimental, artefactos y límites de validez.

No se confunde una **capacidad propuesta** con una capacidad **ya implementada**. S2.10 es la base probada; PPO, BO, meta-learning y OR son desarrollos pendientes hasta su validación.

## 2. Cobertura íntegra de los ocho temas institucionales

| ID | Tema del syllabus | Núcleo teórico obligatorio | Lección | Evidencia experimental |
|---|---|---|---|---|
| T1 | MDP avanzados | Estado, observación, acción, transición estocástica, recompensa, política, horizonte, descuento, restricciones, MDP/POMDP, seguridad y Bellman | L02 | EXP01: formalización, trayectorias y restricciones |
| T2 | Deep RL | Aproximación neuronal de funciones de valor y políticas, generalización, limitaciones tabulares, comparación crítica con reglas y MPC si se valida | L03 | EXP02: entrenamiento, escenarios pareados, estrés |
| T3 | Policy gradients | Objetivo esperado, log-derivative trick, retornos, baseline, ventaja, actor–critic, GAE y PPO con clipping | L04 | EXP02: PPO, semillas, convergencia y fallos |
| T4 | RL aplicado a decisiones secuenciales | Consecuencias diferidas, costos acumulados, demanda variable, exploración, perturbaciones y decisiones seguras | L01 y L02 | EXP01: decisión inmediata frente a retorno acumulado |
| T5 | Bayesian Optimization | Función costosa, presupuesto, sustituto probabilístico, incertidumbre, exploración/explotación, EI o UCB | L05 | EXP03: BO vs búsqueda aleatoria, mismo presupuesto |
| T6 | Meta-learning | Distribución de tareas, transferencia, ajuste fino, reentrenamiento, adaptación, Reptile o MAML de primer orden en problema reducido | L07 | EXP05: tareas nuevas disjuntas y curvas de adaptación |
| T7 | RL + Investigación de Operaciones | Decisión jerárquica, planificación de rutas/asignación, tiempo, batería, prioridades, coordinación con política adaptativa | L08 | EXP06: rutas factibles y valor neto de inspección |
| T8 | Optimización multiobjetivo | Conflicto de objetivos, dominancia, no dominancia, frontera de Pareto, preferencias y selección razonada | L06 | EXP04: conjunto no dominado y decisión argumentada |

**Regla de cobertura:** cada T1–T8 debe figurar en el texto de la lección y tener al menos una evidencia o demostración concreta. La tabla anterior es el contrato de trazabilidad, no la afirmación de que todos los contenidos ya están escritos.

## 3. Programación de las cuatro sesiones (sin modificar el syllabus)

**Fechas:** martes 27 y miércoles 28 de octubre de 2026. **Duración:** cuatro sesiones de 110 minutos; pausa de 20 minutos entre sesiones de cada jornada. Total de formación: 440 minutos. Los horarios de reloj quedan sujetos a confirmación de la Universidad.

### Sesión 1 — Martes 27: el problema de decidir (110 min)

**Temas:** T1 MDP avanzados; T4 RL aplicado a decisiones secuenciales.  
**Lecciones:** L01 *De predicción y control a decisión secuencial*; L02 *MDP, POMDP, restricciones y Bellman*.

| Minutos | Actividad |
|---|---|
| 0–10 | Apertura: predicción, optimización, control y decisión |
| 10–25 | Mundo físico sintético, política por reglas y restricciones |
| 25–50 | Formalización del MDP y observabilidad parcial |
| 50–70 | Retornos, valor, Bellman y consecuencias diferidas |
| 70–90 | EXP01: decisiones locales frente a desempeño acumulado |
| 90–105 | Seguridad, fallos de recompensa y MDP frente a POMDP |
| 105–110 | Síntesis y transición a PPO |

**Producto de aprendizaje:** formulación explícita del MDP, lectura de trayectorias y argumentación sobre por qué una acción barata hoy puede ser costosa mañana.

### Sesión 2 — Martes 27: de Bellman a las políticas neuronales (110 min)

**Temas:** T2 Deep RL; T3 Policy gradients.  
**Lecciones:** L03 *Aproximación neuronal y aprendizaje por refuerzo profundo*; L04 *Gradientes de política, actor–critic, GAE y PPO*.

| Minutos | Actividad |
|---|---|
| 0–15 | Limitaciones tabulares; redes para valor y política |
| 15–35 | Objetivo de política, gradiente, retornos y ventaja |
| 35–55 | Actor–critic y objetivo recortado de PPO |
| 55–75 | EXP02: entrenamiento precalculado, curvas y semillas |
| 75–95 | Comparación pareada con reglas y, si se valida, MPC simplificado |
| 95–105 | Prueba de estrés y generalización fuera de distribución |
| 105–110 | Alcances y límites de Deep RL |

**Producto de aprendizaje:** explicar qué optimiza PPO, qué evidencian las curvas y por qué la recompensa no sustituye las métricas de seguridad.

### Sesión 3 — Miércoles 28: optimizar evaluaciones y negociar objetivos (110 min)

**Temas:** T5 Bayesian Optimization; T8 optimización multiobjetivo.  
**Lecciones:** L05 *Optimización bayesiana y decisiones bajo presupuesto*; L06 *Dominancia, Pareto y preferencias*.

| Minutos | Actividad |
|---|---|
| 0–10 | Parámetros del controlador como decisión de configuración |
| 10–30 | Función costosa, sustituto, incertidumbre y presupuesto |
| 30–50 | Adquisición: EI o UCB |
| 50–70 | EXP03: BO frente a búsqueda aleatoria |
| 70–85 | Objetivos en conflicto: energía, servicio, desgaste e inspección |
| 85–100 | EXP04: dominancia, no dominancia y Pareto |
| 100–110 | Selección ejecutiva de una solución justificable |

**Producto de aprendizaje:** interpretar la incertidumbre del sustituto, la eficiencia de búsqueda y los compromisos entre indicadores.

### Sesión 4 — Miércoles 28: adaptación y coordinación (110 min)

**Temas:** T6 Meta-learning; T7 RL + Investigación de Operaciones.  
**Lecciones:** L07 *Transferencia, adaptación y metaaprendizaje*; L08 *Aprendizaje y optimización combinados: el robot de inspección*.

| Minutos | Actividad |
|---|---|
| 0–15 | Distribución de tareas: demanda, viscosidad y capacidad |
| 15–35 | Transferencia, ajuste fino y meta-learning; Reptile/MAML reducido |
| 35–55 | EXP05: adaptación a tareas no vistas |
| 55–70 | Grafo del robot, tiempo, batería y prioridades |
| 70–90 | EXP06: rutas OR y coordinación con políticas adaptativas |
| 90–100 | Comparación con no inspección, calendario y rutas OR |
| 100–110 | Síntesis entre reglas, MPC, RL, BO, meta-learning y OR |

**Producto de aprendizaje:** diferenciar transferencia de metaaprendizaje y explicar cuándo conviene aprender una decisión y cuándo resolverla por optimización explícita.

## 4. Índice y contrato de las ocho lecciones teóricas

Cada archivo será una lección de nivel avanzado, legible sin abrir Hydro-Lab, y tendrá: **pregunta rectora; motivación; objetivos; definiciones; teoría y matemáticas; ejemplo analítico; supuestos y límites; relación con otros temas; bibliografía; preguntas de discusión; referencia al experimento separado**. Se priorizarán demostraciones comprensibles y rigor sin convertir el curso en una capacitación de programación.

| Archivo propuesto | Contenido distintivo |
|---|---|
| `L01_Decision_Secuencial_G0.1.md` | Predicción vs control vs optimización; decisiones repetidas, costo futuro, incertidumbre, objetivos y políticas |
| `L02_MDP_POMDP_Bellman_G0.1.md` | Formulación estocástica, estado/observación, Markov, restricciones, retorno, valor y Bellman |
| `L03_Deep_RL_G0.1.md` | Aproximación funcional, redes para Q/V/π, estabilidad, generalización, comparación con reglas y MPC |
| `L04_Policy_Gradients_PPO_G0.1.md` | REINFORCE, baseline, actor–critic, ventaja, GAE, razón de políticas, PPO y clipping |
| `L05_Bayesian_Optimization_G0.1.md` | Modelos sustitutos, incertidumbre, adquisición, presupuesto, EI/UCB y criterios de parada |
| `L06_Multiobjetivo_Pareto_G0.1.md` | Objetivos múltiples, escalarización, dominancia, Pareto, preferencias y selección |
| `L07_Meta_Learning_G0.1.md` | Distribución de tareas, transferencia, fine-tuning, Reptile/MAML reducido, adaptación y evaluación |
| `L08_RL_Investigacion_Operaciones_G0.1.md` | Decisión jerárquica, rutas, asignación, restricciones, valor de información y coordinación |

## 5. Seis experimentos docentes (no manuales de uso)

| ID | Pregunta científica | Diseño mínimo y comparadores | Evidencia observable |
|---|---|---|---|
| EXP01 | ¿Una buena decisión inmediata produce buen resultado acumulado? | Mismo escenario y semillas; acciones/políticas alternativas; demanda y tarifa variables | Retorno, energía, entregas, violaciones y trazas |
| EXP02 | ¿Aprende PPO una política robusta y superior a las reglas? | Entrenamiento precomputado, múltiples semillas, separación train/test, reglas y MPC solo si validado | Curvas, dispersión, servicio, seguridad, energía, estrés y fallos |
| EXP03 | ¿BO aprovecha mejor un presupuesto pequeño de simulaciones? | BO y búsqueda aleatoria con presupuesto y escenarios iguales | Mejor valor encontrado, incertidumbre y evaluaciones |
| EXP04 | ¿Qué configuraciones son eficientes cuando hay objetivos en conflicto? | Evaluar varias configuraciones bajo métricas separadas; calcular no dominancia | Frontera aproximada y elección argumentada |
| EXP05 | ¿Se adapta mejor un metaaprendiz a tareas nuevas? | Metaentrenamiento/metaprueba disjuntos; comparar transferencia, ajuste fino, reentrenamiento y meta-learning reducido | Curva desempeño vs muestras de adaptación y variación |
| EXP06 | ¿Qué aporta planificar inspecciones y usar su información? | No inspeccionar, calendario, rutas OR y coordinación adaptativa; misma batería/tiempo | Factibilidad, costo, batería, incertidumbre y valor neto de información |

Las demostraciones serán reproducibles mediante datos y modelos precalculados. No se dependerá de instalaciones ni de entrenamientos largos durante las clases.

## 6. Hoja de ruta de las herramientas

**Base validada:** Hydro-Lab G2.4 / S2.10 (simulación, políticas de referencia, escenarios, robot y trazas). Mantener estable esta base; trabajar en extensiones con pruebas de regresión.

| Generación propuesta | Capacidad a desarrollar | Soporte docente | Condición de cierre |
|---|---|---|---|
| S2.11 | Interfaz de RL y entrenamiento/evaluación PPO | L03–L04, EXP02 | Entrenamiento reproducible, checkpoints, métricas independientes, evaluación pareada, tests |
| Posterior, por versionar | Herramienta de BO y evaluación multiobjetivo | L05–L06, EXP03–04 | Igual presupuesto, sustituto/adquisición visibles, Pareto correcto, tests |
| Posterior, por versionar | Banco de tareas y adaptación/meta-learning reducido | L07, EXP05 | Tareas disjuntas, comparadores y curvas de adaptación, tests |
| Posterior, por versionar | Planificador OR y coordinación con robot | L08, EXP06 | Rutas factibles, presupuesto y valor de información, tests |

**No inventar números de versión posteriores** hasta aprobar el diseño técnico. Si el entrenamiento PPO resulta demasiado costoso, conservar resultados reproducibles precalculados y declarar la limitación.

## 7. Primera especificación a producir: S2.11 PPO

Antes de escribir código, inspeccionar los contratos reales de S2.10 y producir `S2.11_PPO_Especificacion_G0.1.md` con: observación vs estado físico; acciones continuas y límites; transición; recompensa y desglose; restricciones y terminación; episodios; normalización; API Gymnasium; política/valor; entrenamiento y semillas; separación de escenarios; métricas; artefactos; interfaz; tests y criterios de aceptación.

En paralelo, redactar `L04_Policy_Gradients_PPO_G0.1.md` como **lección teórica** y `EXP02_PPO_Comparacion_G0.1.md` como **diseño experimental**, sin insertar instrucciones de navegación de la aplicación en la lección.

## 8. Criterios transversales y límites de validez

1. **Física/DGP:** explicitar balances, unidades, perturbaciones, demanda, tarifas, fallos, sensores y simplificaciones.
2. **Información:** distinguir estado verdadero de observación; inspección informa, no repara físicamente.
3. **Comparadores:** reglas y PPO; MPC solo si está implementado y validado; BO/aleatoria; adaptación/transferencia; políticas robot/OR.
4. **Diseño científico:** semillas, escenarios pareados, presupuestos equivalentes, particiones, variación entre corridas, sensibilidad, ablaciones y fallos.
5. **Métricas:** energía, servicio, desgaste, restricciones, costo de inspección, factibilidad, robustez y cómputo, por separado de la recompensa.
6. **Seguridad y generalización:** advertir sobre reward hacking, sobreajuste, distribución desplazada y ausencia de garantías de seguridad por penalizaciones blandas.
7. **Pedagogía:** cuatro sesiones de 110 minutos; doble lectura intuitiva y matemática; sin programación obligatoria ni entrenamientos largos en vivo.
8. **Alcance:** red completamente sintética; no modela una instalación industrial real de Ecopetrol; no enseñar construcción de dashboards, gemelos digitales o GNN como parte de estos ocho temas.

## 9. Organización documental sugerida

```text
docs/
  01_curso/
    planificacion/
      Hydro_Lab_Plan_Lecciones_y_Herramientas_G0.3.md
    lecciones/
      L01_..._G0.1.md ... L08_..._G0.1.md
    experimentos/
      EXP01_..._G0.1.md ... EXP06_..._G0.1.md
  02_desarrollo/
    S2.11_PPO_Especificacion_G0.1.md
  03_laboratorio/
    manuales/  # manual existente; revisión diferida
```

Los nombres de carpetas nuevos son **propuestos**; confirmar contra el árbol real del repositorio antes de incorporarlos. No sobrescribir generaciones anteriores.

## 10. Puertas de aprobación y secuencia inmediata

- [x] Los ocho temas T1–T8 aparecen explícitamente, con teoría y evidencia asignadas.
- [x] Los cuatro bloques respetan el minutaje detallado del syllabus G2.3.
- [x] Se separan lección, experimento y documentación de ingeniería.
- [x] Se identifican los nueve requisitos transversales de la auditoría G0.3.
- [ ] Aprobar académicamente este plan G0.3.
- [ ] Escribir y revisar las ocho lecciones; verificar bibliografía y derivaciones.
- [ ] Implementar, ejecutar y verificar los seis experimentos.
- [ ] Inspeccionar el repositorio S2.10 antes de fijar interfaces y versiones nuevas.
- [ ] Ensayar las cuatro sesiones completas con materiales precalculados y contingencia.

**Siguiente paso tras la aprobación:** especificación S2.11 y desarrollo teórico de L04; después, EXP02 y construcción de PPO. La planificación completa precede a la implementación, pero las lecciones y herramientas se desarrollan coordinadamente.

## 11. Fuentes internas

- `Syllabus_IA_Avanzada_Ecopetrol_Uniandes_G2.3.md`, especialmente secciones 5–10.
- `Hydro_Lab_Plan_Lecciones_y_Herramientas_G0.2.md`.
- `Hydro_Lab_Auditoria_Cobertura_Syllabus_G0.3.md`.
- Hydro-Lab G2.4 / S2.10: código y documentación existentes, pendientes de inspección técnica para S2.11.
