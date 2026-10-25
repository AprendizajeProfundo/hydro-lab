# Hydro-Lab — Auditoría exhaustiva de cobertura del syllabus

**Generación:** G0.3 — 22 de octubre de 2026  
**Fuentes:** `Syllabus_IA_Avanzada_Ecopetrol_Uniandes_G2.3.md` y `Hydro_Lab_Plan_Lecciones_y_Herramientas_G0.2.md`.  
**Estado:** propuesta para revisión; no reemplaza el syllabus ni certifica implementaciones.

## 1. Dictamen

Los **ocho temas institucionales** figuran en el plan G0.2, pero el nivel de detalle es insuficiente para certificar todos los subtemas, experimentos y criterios de evidencia del syllabus. Se requiere una matriz de trazabilidad antes de aprobar el plan. Esta auditoría distingue cobertura explícita del syllabus, compromiso docente y estado real del software.

## 2. Matriz de trazabilidad de los ocho temas

| ID | Tema obligatorio | Teoría exigida en G2.3 | Evidencia o práctica exigida | Sesión | Estado del plan G0.2 |
|---|---|---|---|---|---|
| T1 | MDP avanzados | Estados, observaciones, acciones, transiciones estocásticas, recompensa, horizonte, descuento, política, restricciones, MDP/POMDP y seguridad | Ficha formal del MDP; trayectorias y consecuencias diferidas | 1 | Nombrado; subtemas y evidencia por cerrar |
| T2 | Deep RL | Aproximación neuronal de valor y política; limitaciones tabulares; comparación crítica con reglas y MPC | Curvas de entrenamiento, generalización y comparación pareada | 2 | Nombrado; falta especificar líneas base y pruebas |
| T3 | Policy gradients | Objetivo de política, gradiente logarítmico, retornos, ventaja, actor–critic, PPO y clipping | Entrenamiento PPO precomputado, varias semillas, convergencia y fallos | 2 | Parcial; PPO no sustituye la teoría general de gradientes |
| T4 | RL para decisiones secuenciales | Consecuencias diferidas, demanda variable, costos acumulados, exploración, perturbaciones y decisiones seguras | Comparación de acciones de beneficio inmediato vs retorno acumulado; estrés por demanda y tarifa | 1–2 | Parcial; no confundir con T1 |
| T5 | Bayesian Optimization | Función costosa, presupuesto, sustituto probabilístico, incertidumbre, exploración/explotación, EI o UCB | Búsqueda aleatoria vs BO con igual presupuesto; mejor valor e incertidumbre | 3 | Nombrado; falta protocolo detallado |
| T6 | Meta-learning | Distribución de tareas, transferencia, fine-tuning, reentrenamiento, metaaprendizaje; Reptile o MAML de primer orden en problema reducido | Tareas metaentrenamiento/metaprueba disjuntas; adaptación frente a número de muestras y líneas base | 4 | Nombrado; falta especificar comparadores |
| T7 | RL + Investigación de Operaciones | Arquitectura jerárquica, rutas/asignación, restricciones de tiempo y batería, prioridades y decisiones adaptativas | Comparar no inspeccionar, calendario, rutas OR y coordinación; factibilidad y valor neto de información | 4 | Nombrado; falta integración formal |
| T8 | Optimización multiobjetivo | Objetivos en conflicto, dominancia, no dominancia, Pareto, preferencias y selección justificable | Conjunto no dominado y decisión ejecutiva razonada | 3 | Nombrado; falta procedimiento experimental |

## 3. Requisitos transversales que no deben desaparecer

**R1. Física y DGP:** red sintética, balances de masa, relaciones hidráulicas simplificadas, inventarios, demandas, tarifas, sensores, fallos y perturbaciones; unidades, restricciones y coherencia numérica.

**R2. Información:** estado real frente a observación, observabilidad parcial, incertidumbre y valor de inspeccionar; el robot no realiza mantenimiento real.

**R3. Comparadores:** reglas, MPC simplificado **solo si se valida**, PPO; búsqueda aleatoria frente a BO; transferencia, fine-tuning/reentrenamiento frente a meta-learning; políticas de inspección y OR.

**R4. Evidencia científica:** semillas, escenarios pareados, presupuestos comparables, separación entrenamiento/validación/prueba y tareas de metaentrenamiento/metaprueba, intervalos o variación entre corridas, sensibilidad, ablaciones y análisis de fallos.

**R5. Métricas independientes de la recompensa:** energía, entregas, integridad/desgaste, restricciones, inspección, tiempos de cómputo, robustez, factibilidad y valor neto de información.

**R6. Límites de validez:** reward hacking, sobreajuste, desplazamiento de distribución, seguridad operacional, simulación sintética no industrial y ausencia de garantías de restricciones duras mediante penalizaciones.

**R7. Modalidad:** cuatro sesiones de 110 minutos los días 27–28 de octubre de 2026, con pausa de 20 minutos por jornada; sin instalaciones ni entrenamientos largos en vivo; demostraciones reproducibles y artefactos precalculados.

**R8. Profundidad dual:** lectura operacional y lectura matemático-computacional, sin exigir programación a los participantes; teoría autónoma, práctica con Hydro-Lab, documentación técnica separada.

**R9. Alcance negativo explícito:** no enseñar construcción de dashboards, gemelos digitales ni GNN; no confundir el grafo físico con una red neuronal de grafos; no usar datos ni instalaciones reales de Ecopetrol.

## 4. Distribución verificable de las lecciones

| Sesión | Lecciones teóricas independientes de la app | Experimento integrado en Hydro-Lab |
|---|---|---|
| S1 (110 min) | L01 Predicción, control y decisión secuencial; L02 MDP, POMDP, restricciones y Bellman | EXP01 Acciones inmediatas frente a retornos y restricciones |
| S2 (110 min) | L03 Aproximación neuronal y Deep RL; L04 Gradientes de política, actor–critic y PPO | EXP02 Entrenamiento PPO precomputado, comparación pareada y estrés |
| S3 (110 min) | L05 Optimización bayesiana; L06 Optimización multiobjetivo y Pareto | EXP03 BO vs aleatoria; EXP04 compromisos no dominados |
| S4 (110 min) | L07 Transferencia y meta-learning; L08 RL + OR, planificación e información | EXP05 adaptación entre tareas; EXP06 rutas factibles y valor de inspección |

**Nota:** esta descomposición en ocho lecciones es una propuesta editorial; el syllabus define ocho temas, no necesariamente ocho lecciones. Se respetará el minutaje detallado de la sección 8 de G2.3.

## 5. Puertas de aprobación

- [ ] Cada T1–T8 tiene lección con objetivos, teoría, notación, ecuaciones, bibliografía y límites.
- [ ] Cada T1–T8 tiene evidencia experimental o demostración identificada y verificable.
- [ ] Cada R1–R9 se refleja en un entregable o en una regla editorial explícita.
- [ ] El material docente cabe en cuatro sesiones de 110 minutos.
- [ ] Los experimentos pueden ejecutarse con resultados precalculados y plan de contingencia.
- [ ] Las funciones futuras se distinguen de las ya implementadas en S2.10.
- [ ] No se promete MPC, meta-learning, PPO, BO u OR implementado antes de verificar su ejecución.

## 6. Recomendación

**No aprobar G0.2 como plan completo.** Utilizar esta auditoría G0.3 como anexo de trazabilidad y preparar una futura versión consolidada del plan que haga explícitos los ocho temas, sus subtemas, experimentos, criterios de aceptación y minutaje. Conservar G0.2 sin sobrescribir.
