# Hydro-Lab — Plan integrado de lecciones y herramientas

**Generación:** G0.1  
**Fecha:** 22 de octubre de 2026  
**Proyecto:** Aprendizaje Profundo — Hydro-Lab  
**Repositorio:** https://github.com/AprendizajeProfundo/hydro-lab  
**Estado:** propuesta de trabajo para aprobación; no sustituye el syllabus G2.3.

## 1. Propósito

Construir de manera coordinada las lecciones, las demostraciones y las herramientas computacionales del curso *Inteligencia artificial avanzada aplicada a retos estratégicos*, utilizando un único entorno experimental: *Intelligent Hydrocarbon Transportation Network* (Hydro-Lab).

El punto de partida es Hydro-Lab G2.4/S2.10, con 96 pruebas superadas localmente. La revisión final del manual S2.10 y de la guía de estudiantes queda diferida y se retomará después de construir las herramientas prioritarias.

## 2. Principios de desarrollo

1. **Un mundo experimental común.** Todas las extensiones comparten el entorno hidráulico, las métricas y los escenarios; no se crearán simuladores inconexos.
2. **Una lección, una pregunta científica.** Cada unidad comienza con un problema observable y una hipótesis contrastable.
3. **El código no sustituye la explicación.** Cada lección incluye intuición, formulación matemática, experimento, interpretación y límites.
4. **Reproducibilidad.** Registrar semillas, configuración, versiones, episodios y resultados; separar entrenamiento de evaluación.
5. **Versionado por generaciones.** Conservar las versiones aprobadas y documentar las decisiones de diseño.
6. **Demostraciones confiables.** Disponer de resultados precalculados y planes alternativos para las sesiones en vivo.
7. **Seguridad conceptual.** El entorno es sintético y educativo, no una herramienta de operación industrial.

## 3. Organización propuesta del repositorio

```text
hydro-lab/
├── dashboard/
├── src/hydro_lab/
├── tests/
├── examples/
├── configs/
├── docs/
│   ├── 01_curso/
│   │   ├── syllabus/
│   │   └── planificacion/
│   │       └── Plan_Lecciones_y_Herramientas_G0.1.md
│   ├── 02_fundamentos/
│   ├── 03_laboratorio/
│   ├── 04_actividades/
│   │   └── experimentos/
│   ├── 05_instructores/
│   │   ├── sesiones/
│   │   └── demostraciones/
│   ├── 06_referencias/
│   ├── 07_lecciones/
│   │   ├── S01_MDP/
│   │   ├── S02_Deep_RL_PPO/
│   │   ├── S03_Optimizacion/
│   │   └── S04_Adaptacion_y_OR/
│   └── historico/
└── sprints/  # archivo histórico local, excluido de Git
```

Las carpetas nuevas son una propuesta; se crearán cuando tengan contenido real. `sprints/` permanece excluida mediante `.gitignore`.

## 4. Estructura estándar de cada lección

Cada lección se entrega como un archivo `LXX_Titulo_G0.1.md` y contiene:

1. Identificación, sesión, duración y prerrequisitos.
2. Pregunta central y resultados de aprendizaje verificables.
3. Situación física o de decisión en Hydro-Lab.
4. Intuición y desarrollo conceptual.
5. Modelo matemático y supuestos explícitos.
6. Demostración guiada con pasos reproducibles.
7. Experimento: hipótesis, diseño, variables, métricas y semillas.
8. Interpretación de resultados y posibles fallos.
9. Actividad breve del estudiante y criterios de comprobación.
10. Referencias y vínculos al código, figuras y datos.

El guion del instructor se almacena por separado cuando contenga soluciones, tiempos detallados o instrucciones reservadas.

## 5. Correspondencia inicial entre sesiones y herramientas

| Sesión del syllabus G2.3 | Núcleo conceptual | Herramienta o extensión | Evidencia docente |
|---|---|---|---|
| 1. De la física al MDP | Estado, acción, transición, recompensa, restricciones, horizonte | Instrumentación de episodios y formulación del MDP sobre S2.10 | Trayectorias comparadas y consecuencias diferidas |
| 2. De Bellman a las políticas neuronales | Valor, política, aproximación funcional, Deep RL y PPO | **S2.11: agente PPO, entrenamiento y evaluación** | Curvas de aprendizaje, política entrenada frente a controladores de referencia |
| 3. Aprender dónde evaluar y negociar objetivos | Optimización bayesiana y multiobjetivo | Experimentos de búsqueda, sustitutos y Pareto | Historial de evaluaciones, incertidumbre y compromisos entre objetivos |
| 4. Adaptarse y coordinar decisiones | Meta-learning, transferencia y RL + investigación de operaciones | Adaptación entre escenarios y planificación de inspección | Desempeño antes/después de adaptación y comparación con planificador |

Esta tabla expresa el diseño de implementación propuesto. No implica que las extensiones posteriores a S2.10 estén ya disponibles.

## 6. Primera generación de desarrollo: S2.11 — PPO

### 6.1. Objetivo científico

Estudiar si una política neuronal entrenada mediante PPO puede aprender a operar la red hidráulica sintética y cómo se compara con las políticas existentes en escenarios conocidos y no vistos.

### 6.2. Contrato de entorno por especificar

- **Observación:** determinar qué variables puede conocer el agente en cada paso, diferenciando estado físico y observación disponible.
- **Acción:** definir el control de las bombas, su rango y la forma de imponer restricciones físicas.
- **Recompensa:** descomponer el objetivo en servicio, energía, salud, riesgo y penalizaciones, evitando confundir métrica de entrenamiento con métricas de evaluación.
- **Episodio:** conservar la semántica temporal de S2.10 (15 minutos por paso; hasta 96 pasos) y documentar terminaciones anticipadas.
- **Escenarios:** separar conjuntos de entrenamiento, validación y evaluación fuera de muestra.
- **Líneas base:** comparar contra controladores existentes con las mismas condiciones iniciales y semillas.
- **Métricas:** retorno, servicio, energía, contingencias, variabilidad entre semillas y costo computacional.

Ninguna de estas decisiones se considera cerrada hasta revisar las interfaces y restricciones reales de S2.10.

### 6.3. Entregables S2.11

1. `docs/03_laboratorio/arquitectura/Especificacion_PPO_S2.11_G0.1.md` — contrato técnico y decisiones.
2. `docs/07_lecciones/S02_Deep_RL_PPO/L01_De_Bellman_a_PPO_G0.1.md` — lección completa.
3. Código de entrenamiento y evaluación desacoplado del núcleo S2.10, con configuración reproducible.
4. Pruebas unitarias, de integración y pruebas de no regresión sobre S2.10.
5. Datos o artefactos de demostración y visualizaciones interpretables.
6. Guion docente y actividad práctica, separados de la lección.

### 6.4. Criterios de aceptación

- Las 96 pruebas actuales continúan pasando.
- Se puede entrenar y cargar una política sin modificar manualmente el código del simulador.
- El entrenamiento es reproducible hasta los límites documentados de las bibliotecas y el hardware.
- Se comparan varias semillas de evaluación; no se comunica un resultado aislado como evidencia concluyente.
- Los fallos y límites de PPO se muestran explícitamente.
- La demostración puede ejecutarse con una política preentrenada si el entrenamiento en vivo resulta lento.

## 7. Método de trabajo y control de versiones

Para cada extensión se sigue este orden:

1. **Especificación científica y pedagógica** (`G0.1`).
2. **Revisión y aprobación** de observaciones, acciones, recompensas, escenarios y criterios.
3. **Implementación incremental** con pruebas.
4. **Experimento reproducible** y análisis de resultados.
5. **Lección y guion docente completos**.
6. **Revisión de coherencia** con el syllabus y actualización del repositorio.

Cada archivo aprobado conserva su identidad de generación; los cambios sustantivos se registran en nuevas versiones, sin sobrescribir el historial de investigación.

## 8. Próxima tarea inmediata

Examinar `src/hydro_lab/environment.py`, `src/hydro_lab/observations.py`, `src/hydro_lab/control_center.py`, las funciones de recompensa y la interfaz Gymnasium existente. Con base en ese examen, cerrar el contrato PPO S2.11 antes de escribir el entrenador.

## 9. Referencias internas

- `docs/01_curso/syllabus/Syllabus_IA_Avanzada_Ecopetrol_Uniandes_G2.3.md`
- `docs/03_laboratorio/arquitectura/Red_Hidrocarburos_Especificacion_Matematica_Computacional_G2.4.md`
- `docs/03_laboratorio/manuales/Manual_Hydro_Lab_S2.10_V2-0.md`
- Repositorio oficial: https://github.com/AprendizajeProfundo/hydro-lab
