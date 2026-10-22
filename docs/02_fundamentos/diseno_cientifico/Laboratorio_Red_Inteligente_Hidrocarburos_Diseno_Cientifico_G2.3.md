# Intelligent Hydrocarbon Transportation Network

## Diseño científico del laboratorio integrado — Generación 2, versión 0.3 (G2.3)

**Programa:** Inteligencia artificial avanzada aplicada a retos estratégicos  
**Sesión:** Dominio técnico avanzado  
**Contexto:** Ecopetrol — Universidad de los Andes  
**Naturaleza:** Documento de investigación, modelación y diseño experimental; **no es material educativo**  
**Documento académico de referencia:** `Syllabus_IA_Avanzada_Ecopetrol_Uniandes_G2.3.md`  
**Autor:** Álvaro Montenegro  
**Cargo:** CEO — Learning Systems Institute (LSI) y Aprendizaje Profundo SAS  
**Fecha:** Bogotá, 18 de octubre de 2026  
**Estado:** Diseño científico G2.3 propuesto; **simulador y resultados aún no implementados ni validados**  
**Control de generaciones:** G0.2, G2.1, G2.2 y los experimentos G0.1 permanecen intactos. G2.3 se deriva de G2.1, no de la arquitectura de gemelo digital de G2.2.

---

## Resumen ejecutivo

Este documento especifica un **entorno de simulación científico, reproducible, sintético y deliberadamente compacto** para estudiar el control de una red de transporte de hidrocarburos y su coordinación con un robot autónomo de inspección. El laboratorio unifica cinco familias de experimentos dentro de **cuatro sesiones de 110 minutos**: decisiones secuenciales, aprendizaje profundo por refuerzo, optimización bayesiana y multiobjetivo, adaptación entre tareas y planificación híbrida RL–investigación de operaciones. Se propone una arquitectura **jerárquica** en la cual un coordinador fija objetivos y prioridades, un controlador opera la red hidráulica y un robot ejecuta inspecciones que reducen incertidumbre sobre la condición de los equipos.

La tesis experimental no es que RL deba superar a MPC o a la optimización matemática. Es que un mismo sistema acoplado permite estudiar, bajo protocolos comparables, **qué método resulta apropiado, bajo qué información, restricciones y costos computacionales**. La coherencia física, la observabilidad, la factibilidad y la evaluación fuera de distribución precederán a cualquier afirmación de desempeño.

**Alcance explícito:** no representa activos de Ecopetrol, no emplea datos operacionales ni permite inferir seguridad o rendimiento de instalaciones reales. Las magnitudes, parámetros y topología que siguen son **propuestas iniciales**, no valores calibrados.

## 1. Preguntas científicas e hipótesis refutables

**P1 — Control.** ¿Cuánto mejora —si mejora— una política PPO respecto a reglas operativas y MPC, ante demanda variable y perturbaciones, bajo información y límites de acción comparables?

**H1.** PPO puede aprender comportamientos competitivos en distribuciones de entrenamiento amplias; MPC puede dominar cuando el modelo es preciso y las restricciones están bien representadas. **No se presupone ganador.**

**P2 — Optimización.** ¿Puede la optimización bayesiana seleccionar configuraciones de control con menos evaluaciones costosas que la búsqueda aleatoria?

**H2.** Para una función de desempeño suficientemente regular y una dimensión moderada, BO puede mejorar la eficiencia muestral; su ventaja podría desaparecer ante ruido alto, discontinuidades o dimensión excesiva.

**P3 — Objetivos en conflicto.** ¿Qué compromisos emergen entre energía, cumplimiento de entregas, maniobras, exposición a restricciones y costo de inspección?

**H3.** Existirán soluciones no dominadas con intercambios mensurables; no habrá necesariamente una única política óptima independiente de preferencias.

**P4 — Adaptación.** ¿Un método de meta-learning reduce muestras o tiempo de adaptación frente a entrenamiento desde cero y fine-tuning convencional en tareas no vistas?

**H4.** La ventaja dependerá de la similitud estructural entre las tareas de metaentrenamiento y metaprueba. El simple reentrenamiento **no** se denominará meta-learning.

**P5 — Información y coordinación.** ¿Cuándo compensa inspeccionar una estación antes de modificar su régimen de operación?

**H5.** La utilidad de inspeccionar depende del **valor de la información para las decisiones posteriores**, no únicamente de la probabilidad de deterioro. Una planificación con información puede mejorar el resultado neto, descontados desplazamiento y tiempo de inspección.

Cada hipótesis será contrastada mediante métricas separadas, intervalos de incertidumbre y escenarios de prueba fijados antes de comparar métodos.

## 2. Alcance físico y fronteras de validez

Se adopta una **red de líquido monofásico e incompresible**, a temperatura de referencia, con densidad constante por episodio y viscosidad variable entre escenarios o lentamente en el tiempo. En cada paso de control se supone equilibrio hidráulico cuasiestacionario. Los inventarios y el estado de salud de equipos evolucionan dinámicamente. Las decisiones se toman en intervalos de duración $\Delta t$.

**Se incluyen:** conservación de masa, elevación geométrica, pérdidas por fricción, curvas simplificadas de bomba, almacenamiento, demandas, energía, restricciones, incertidumbre, sensores imperfectos y accesibilidad del robot.

**Se excluyen:** golpes de ariete, dinámica de ondas de presión, flujo multifásico, transporte térmico detallado, mezclas complejas de crudos, corrosión mecanicista, detección certificada de fugas, despacho comercial real y protocolos de control industrial. Un fallo de bomba será un **evento sintético de pérdida de capacidad**, no una representación de integridad operacional real.

El objetivo es un **banco de pruebas computacional sintético** con plausibilidad física suficiente para formular y comparar algoritmos. **No se desarrollará ni enseñará un gemelo digital**: no hay activo físico conectado, sincronización operacional ni obligación de implementar una segunda representación del sistema. Tampoco se incluyen GNN ni desarrollo de dashboards como contenidos.

## 3. Topología mínima propuesta

Se define un grafo dirigido $G=(V,E)$ con **cinco nodos** y **cinco aristas**, sujeto a revisión durante la validación:

- $v_0$: tanque de origen y alimentación;
- $v_1$: estación de impulsión inicial;
- $v_2$: estación de bombeo en rama norte;
- $v_3$: estación de bombeo en rama sur;
- $v_4$: tanque de destino y punto de entrega.

Las aristas son $e_{01},e_{12},e_{24},e_{13},e_{34}$. Las ramas $v_1\to v_2\to v_4$ y $v_1\to v_3\to v_4$ son alternativas, pero comparten alimentación y destino. La conexión hidráulica de cada rama deberá tener válvulas o actuadores equivalentes modelados explícitamente si se pretende controlar la distribución de caudal. No basta con declarar arbitrariamente dos caudales independientes.

![Arquitectura conceptual del laboratorio integrado](arquitectura-conceptual.svg)

*Figura 1. Esquema conceptual de la arquitectura G2. El SVG debe situarse en la misma carpeta que este archivo. No es un plano hidráulico ni fija la topología numérica definitiva.*

La geometría física (longitudes, diámetros, rugosidades, desniveles) y el grafo de tránsito del robot serán **dos grafos diferentes**. Las rutas de inspección no deben confundirse con el interior de las tuberías.

## 4. Modelo hidráulico reducido

### 4.1. Variables y convenciones

Se trabaja en unidades SI. Para cada arista $e$, $q_e$ denota caudal volumétrico en m³/s; $p_i$ presión manométrica en Pa; $z_i$ elevación en m; $\rho$ densidad en kg/m³; $\mu$ viscosidad dinámica en Pa·s; $D_e$ diámetro en m; $L_e$ longitud en m; $\epsilon_e$ rugosidad absoluta en m. Los caudales se orientan de acuerdo con el grafo; en el modelo inicial se restringen a $q_e\ge 0$ mediante válvulas antirretorno idealizadas o condiciones operativas admisibles.

La matriz de incidencia $B\in\mathbb{R}^{|V|\times|E|}$ usa $-1$ en el origen y $+1$ en el destino de cada arista. Si $b_i$ denota **aporte neto al nodo desde fuentes externas o almacenamiento** (positivo para aporte, negativo para extracción), el balance estacionario en nodos sin acumulación se expresa como

$$
Bq=-b,\qquad b_i=0\ \text{en nodos internos sin aporte ni extracción}.
$$

En nodos con tanques, $b_i$ se conecta con el balance dinámico definido más adelante. La convención se verifica en una arista $i\to j$: $Bq$ vale $-q$ en el origen y $+q$ en el destino; por tanto, $b_i=+q$ y $b_j=-q$ representan respectivamente aporte externo y extracción. Esta convención se someterá a pruebas unitarias.

### 4.2. Pérdidas de carga

Para una arista sin bomba, una formulación Darcy–Weisbach es

$$
\Delta p_{e,\mathrm{fric}}=f_e\frac{L_e}{D_e}\frac{\rho v_e|v_e|}{2},
\qquad v_e=\frac{4q_e}{\pi D_e^2}.
$$

Se define $\mathrm{Re}_e=\rho |v_e|D_e/\mu$. En régimen laminar, $f_e=64/\mathrm{Re}_e$; en régimen turbulento, $f_e$ se obtiene mediante una correlación apropiada y documentada, por ejemplo Colebrook–White o una aproximación explícita. La región de transición requiere tratamiento consistente y pruebas de continuidad numérica. Para evitar división por cero se define el límite analítico o regularización controlada en $q_e=0$.

El balance de energía entre extremos de una arista con bomba se plantea como

$$
\frac{p_j-p_i}{\rho g}+(z_j-z_i)
=h_{P,e}(q_e,u_e,h_e)-h_{L,e}(q_e,\rho,\mu),
$$

donde $h_{P,e}$ es la altura añadida por bombeo y $h_{L,e}$ la pérdida de carga. **No se impondrán simultáneamente caudales y presiones incompatibles**: los caudales y presiones serán solución conjunta de los balances.

### 4.3. Curvas de bomba y eficiencia

Como primer modelo sintético, para cada bomba $k$:

$$
h_{P,k}(q_k,u_k,h_k)=h_k\left(a_k u_k^2-b_k q_k^2\right),
$$

con velocidad relativa $u_k\in[u_k^{\min},u_k^{\max}]$, estado de salud $h_k\in(0,1]$ y parámetros positivos $a_k,b_k$. La región admisible deberá asegurar altura no negativa, límites de operación y comportamiento coherente con una curva realista. El modelo no pretende describir una bomba específica.

La potencia eléctrica aproximada es

$$
P_k=\frac{\rho g q_k h_{P,k}}{\eta_k(q_k,u_k,h_k)},
$$

con eficiencia acotada $\eta_k\in[\eta_{\min},\eta_{\max}]\subset(0,1)$. Se debe definir un consumo de reposo o arranque cuando sea pertinente y prohibir que la función de eficiencia produzca singularidades o potencia negativa.

### 4.4. Inventarios y entregas

Para un tanque $i$ con volumen $V_{i,t}$:

$$
V_{i,t+1}=V_{i,t}+\Delta t\left(Q^{\mathrm{in}}_{i,t}-Q^{\mathrm{out}}_{i,t}+s_{i,t}\right),
$$

con $V_i^{\min}\le V_{i,t}\le V_i^{\max}$. La entrega efectivamente servida $d_t^{\mathrm{served}}$ no puede superar demanda $d_t$, disponibilidad hidráulica ni inventario factible. El déficit es $\max(0,d_t-d_t^{\mathrm{served}})$. Se debe elegir explícitamente si la demanda no servida se pierde o se acumula como pedido pendiente; **G2.3 mantiene demanda perdida por periodo** para evitar introducir una cola de pedidos no modelada.

### 4.5. Solución numérica y factibilidad

Para cada acción se resolverá un sistema de ecuaciones algebraicas no lineales de continuidad y energía, con límites de caudal, presión, velocidad y almacenamiento. El solver devolverá **estado factible, inviabilidad certificada según tolerancias o fallo numérico**; estas categorías no son equivalentes.

Una acción físicamente imposible no se convertirá en una transición normal con simple penalización. El entorno aplicará un mecanismo explícito de seguridad: *action masking* cuando sea discreto, proyección factible cuando pueda justificarse o rechazo y política de respaldo. La proyección cambia la acción efectivamente ejecutada y debe registrarse para que el aprendizaje sea consistente.

**Decisión abierta D-01:** escoger entre una formulación hidráulica nodal con variables $(p,q)$ y una formulación reducida por ramas, verificando equivalencia en casos sencillos.

## 5. Dinámica estocástica y proceso generador de datos

El estado físico completo propuesto es

$$
x_t=(V_t,h_t,\mu_t,d_t,c_t,a_t^{\mathrm{equip}},\xi_t),
$$

donde $V_t$ son inventarios, $h_t$ salud de bombas, $\mu_t$ viscosidad, $d_t$ demanda, $c_t$ tarifa energética, $a_t^{\mathrm{equip}}$ disponibilidad de equipos y $\xi_t$ variables exógenas latentes. Los caudales y presiones $q_t,p_t$ se obtienen del subproblema hidráulico y pueden incorporarse al estado observado, aunque no sean estados dinámicos independientes bajo la hipótesis cuasiestacionaria.

### 5.1. Procesos exógenos

Se propone una demanda no negativa con estacionalidad y componente autorregresivo:

$$
d_t=\max\left\{0,\bar d\left[1+A_d\sin\left(\frac{2\pi t\Delta t}{T_d}+\phi_d\right)\right]+\zeta_t\right\},
$$

$$
\zeta_{t+1}=\varphi_d\zeta_t+\sigma_d\varepsilon_{t+1}^{(d)},\qquad |\varphi_d|<1.
$$

La viscosidad puede evolucionar lentamente mediante un proceso autorregresivo **en escala logarítmica** para preservar positividad:

$$
\log\mu_{t+1}=m_\mu+\varphi_\mu(\log\mu_t-m_\mu)+\sigma_\mu\varepsilon_{t+1}^{(\mu)}.
$$

La tarifa $c_t$ puede seguir un calendario determinista conocido más perturbación limitada. Los escenarios de prueba deben incluir cambios de nivel, amplitud y persistencia, no únicamente nuevas semillas.

### 5.2. Deterioro y fallas

Para una bomba $k$, el estado de salud evoluciona como

$$
h_{k,t+1}=\operatorname{clip}\left(h_{k,t}-\Delta t\,\kappa_k\,\psi(q_{k,t},u_{k,t})+\omega_{k,t},\ h_{\min},1\right),
$$

con $\psi\ge0$ creciente con una medida de exigencia operativa y ruido pequeño de signo controlado. Los eventos de indisponibilidad se generan por un proceso de riesgo documentado, condicionado —si se decide— por salud y carga. **La distribución de fallas no debe elegirse para favorecer un algoritmo.**

Una inspección **no repara automáticamente** el equipo: modifica la información disponible. Una reparación, si se incorpora en una versión futura, será una acción distinta con tiempo, costo y restricciones explícitos.

### 5.3. Ruido y observación parcial

El controlador recibe

$$
y_t=H(x_t,q_t,p_t)+\nu_t,
$$

con ruido de sensores, retrasos o mediciones faltantes bajo escenarios definidos. El estado de salud $h_{k,t}$ no será observado directamente salvo mediante inspección de calidad superior. Se documentarán errores de medición y calibración; los resultados de inspección no serán oráculos perfectos por defecto.

**Cuidado metodológico:** si la observación no es Markoviana, un PPO puramente reactivo opera bajo información parcial. Se comparará con una representación de historial o estimador de estado; no se declarará que el vector observado satisface la propiedad de Markov sin evidencia.

### 5.4. Tabla inicial de parámetros y rangos

Los valores numéricos quedan **deliberadamente sin fijar** hasta el análisis dimensional y de sensibilidad. Se propone el siguiente registro obligatorio:

| Parámetro | Unidad | Criterio de selección y prueba |
|---|---|---|
| $\Delta t$ | min | Intervalo operativo candidato: 15; verificar convergencia frente a 5 y 30 |
| $L_e$ | km | Longitudes sintéticas diferenciadas por rama; convertir a m en solver |
| $D_e$ | m | Diámetros que permitan regímenes de flujo y velocidades plausibles |
| $\epsilon_e$ | mm | Rugosidad positiva, documentada y sensible al modelo de fricción |
| $\rho$ | kg/m³ | Escenarios de líquido monofásico; coherencia con viscosidad |
| $\mu_t$ | Pa·s | Distribución positiva, incluyendo escenarios no vistos |
| $a_k,b_k$ | Según curva | Ajustar para soluciones hidráulicas factibles y no degeneradas |
| $\eta_k$ | Adimensional | Estrictamente entre cero y uno |
| $V_i^{\min},V_i^{\max}$ | m³ | Volúmenes consistentes con flujos y horizonte |
| $d_t$ | m³/s | Demanda compatible con capacidad y escenarios de escasez |
| $c_t$ | moneda/kWh | Tarifas sintéticas y cronograma reproducible |
| $\sigma_d,\sigma_\mu$ | Según proceso | Definir perturbaciones suaves, severas y fuera de distribución |

**Regla editorial:** en tablas, unidades en texto normal para evitar errores KaTeX en VS Code; símbolos y ecuaciones con `$...$` y `$$...$$`.

## 6. Arquitectura jerárquica y escalas temporales

Se distinguen tres capas y dos escalas de decisión, sujetas a revisión:

1. **Coordinador central:** cada $K$ pasos hidráulicos, define prioridades de entrega, presupuesto energético, ventanas y prioridades de inspección. Utiliza información agregada y estimaciones de incertidumbre; no gobierna directamente actuadores a alta frecuencia.
2. **Controlador hidráulico:** en cada paso $\Delta t$, selecciona velocidades de bomba, configuraciones de rama o consignas admisibles. Su acción pasa por el verificador de factibilidad hidráulica.
3. **Robot de inspección:** en un grafo de accesibilidad separado, selecciona movimientos y acciones de inspección dentro de las tareas priorizadas, con duración y batería. Su información actualiza el estimador central.

La política global puede expresarse como composición condicionada:

$$
\pi(a_t^{\mathrm{hyd}},a_t^{\mathrm{rob}}\mid o_{0:t})
=\pi_{\mathrm{hyd}}(a_t^{\mathrm{hyd}}\mid b_t,g_t)\,
\pi_{\mathrm{rob}}(a_t^{\mathrm{rob}}\mid b_t,g_t,\ell_t),
$$

bajo una **aproximación de factorización condicionada**, no como independencia física de las decisiones. Aquí $b_t$ es una representación de creencias o estimaciones, $g_t$ la consigna central y $\ell_t$ el estado logístico del robot. La actualización conjunta del estado posterior preserva el acoplamiento entre ambas decisiones.

### 6.1. El robot y su modelo

Sea $G_R=(V_R,E_R)$ un grafo de caminos accesibles entre instalaciones. El estado robótico incluye posición, batería, tarea, tiempos restantes y disponibilidad de rutas. El planificador OR resuelve una versión pequeña de *orienteering*, ruta con presupuesto o asignación y secuenciación de inspecciones. La política aprendida puede ejecutar o reajustar el plan frente a tiempos de viaje inciertos, bloqueos y observaciones nuevas.

No se incluirán, en esta generación, cinemática continua, SLAM, manipulación física ni mantenimiento mecánico. **Robótico** significa aquí un agente móvil autónomo de inspección en una red logística abstraída, no un robot industrial certificado.

### 6.2. Valor de la información

Para una acción de inspección $a^{\mathrm{insp}}$ y una creencia $b$, el valor esperado de la información se define conceptualmente como

$$
\operatorname{VOI}(a^{\mathrm{insp}};b)
=\mathbb E_{y\mid b,a^{\mathrm{insp}}}\left[\max_{\pi}\,U(\pi\mid b^{y})\right]
-\max_{\pi}\,U(\pi\mid b)
-C(a^{\mathrm{insp}}),
$$

con utilidad definida sobre el **mismo horizonte y las mismas decisiones posteriores**. Esta forma supone que la inspección afecta inicialmente la información, no la física. Cuando hay retrasos y efectos operativos durante el desplazamiento, el cálculo deberá incorporar explícitamente esos costos de oportunidad y transiciones. El valor de información no debe confundirse con la entropía reducida: una observación puede reducir incertidumbre sin alterar la decisión óptima.

## 7. Formulación de decisión secuencial

Se define un proceso parcialmente observable y restringido con estado $s_t=(x_t,\ell_t)$, acción conjunta $a_t$, transición $P(s_{t+1}\mid s_t,a_t)$, observación $O(o_t\mid s_t)$, recompensa $r_t$ y restricciones $g_j(s_t,a_t)\le0$. Para el tratamiento introductorio, un caso con observación completa podrá presentarse como MDP de referencia.

La recompensa inicial candidata es

$$
r_t=-w_E C_{E,t}-w_D C_{D,t}-w_S C_{S,t}-w_M C_{M,t}-w_I C_{I,t},
$$

con energía, déficit de entrega, cambios de actuadores, maniobras y costos de inspección. Se usarán escalas normalizadas o unidades monetarias consistentes y pesos documentados. **Las restricciones críticas no se relegarán a penalizaciones:** presión, caudal, capacidad, inventario, batería y accesibilidad deberán tratarse mediante factibilidad explícita.

El objetivo de política es

$$
\max_\pi\ \mathbb E_\pi\left[\sum_{t=0}^{T-1}\gamma^t r_t\right],
\quad\text{sujeto a }g_j(s_t,a_t)\le0\text{ cuando sea exigible}.
$$

Se distinguirán **restricciones duras por paso**, límites agregados de exposición y objetivos blandos. Para explicar Bellman se utilizará la versión Markoviana completamente observable, sin atribuir la misma ecuación simple a un proceso parcialmente observable sin definir su estado de creencia.

## 7A. Contrato de simplicidad y trazabilidad pedagógica

El laboratorio se considerará **adecuado para el curso** solo si supera, además de la validación física, estas restricciones de diseño:

1. **Un solo mundo:** mismo grafo hidráulico, variables físicas y DGP en las cuatro sesiones; las diferencias de algoritmos no crean plantas incompatibles.
2. **Estado compacto:** para las demostraciones se publicará una tabla corta de variables observables, latentes y controlables; no se exige instrumentación industrial detallada.
3. **Acciones interpretables:** velocidades o consignas de bombas y prioridades de inspección; los actuadores se justifican por su efecto hidráulico y sus límites.
4. **Robot discreto:** posiciones, aristas de tránsito, batería y eventos de inspección; sin SLAM, visión, cinemática ni GNN.
5. **PPO sobre un subproblema manejable:** entrenado antes del curso, con semillas múltiples y métricas de costo, servicio y seguridad.
6. **Meta-learning reducido pero genuino:** tareas con cambios paramétricos, separación de metaentrenamiento y metaprueba, adaptación de pocos pasos y baselines con presupuesto igualado.
7. **BO de dimensión pequeña:** parámetros del controlador con interpretación y dominio acotado; no optimizar cientos de pesos neuronales.
8. **OR como método explícito:** problema de rutas o asignación con restricciones; RL se utiliza solo donde exista una decisión adaptativa justificada.
9. **Evidencia antes de exposición:** no se prometerán mejoras de PPO, BO, meta-learning o inspección sin resultados de prueba.
10. **Tiempo realista:** cada demostración tendrá duración máxima, respaldo reproducible y una conclusión que el participante pueda interpretar sin programar.

### 7A.1. Registro de artefactos científicos por sesión

| Sesión | Entradas y artefactos | Resultado que se debe poder explicar |
|---|---|---|
| 1 | `network.yaml`, `scenarios.yaml`, reglas, trayectorias | MDP y consecuencias acumuladas |
| 2 | políticas PPO, reglas, MPC opcional, episodios pareados | Gradiente de política, aprendizaje y robustez |
| 3 | evaluador de configuraciones, trazas BO y búsqueda aleatoria, conjunto Pareto | Presupuesto de evaluación y objetivos en conflicto |
| 4 | tareas separadas, trazas de adaptación, grafo de rutas, planes OR | Transferencia frente a metaaprendizaje y coordinación híbrida |

## 8. Experimentos y métodos de referencia

### E1 — Control de red: reglas, MPC y PPO

**Pregunta:** ¿cómo cambia el desempeño ante demandas, precios y salud de equipos variables?

- **Reglas:** control por umbrales, bandas de inventario y prioridad fija de ramas; parámetros fijados con datos de validación, no prueba.
- **MPC:** optimización recedente de horizonte $H$ sobre modelo reducido, con restricciones explícitas y pronósticos; se registrará el tiempo de solución y el tratamiento de no convexidad.
- **PPO:** política continua para consignas admisibles; observaciones normalizadas, entorno Gymnasium, entrenamiento previo, semillas múltiples y evaluación sin exploración.
- **Comparación:** mismo simulador de evaluación, demandas, condiciones iniciales y presupuesto de información. El costo de entrenamiento y el costo por decisión se reportarán por separado.

**Métricas:** energía por volumen entregado, fracción de demanda servida, costo total, presión máxima, número y severidad de intervenciones de seguridad, variación de actuadores, tiempo de cómputo y dispersión entre episodios. No se concluirá superioridad a partir de una única curva de recompensa.

### E2 — Optimización bayesiana de configuraciones

Se seleccionará un vector de **pocos parámetros continuos** de un controlador (por ejemplo, horizonte y pesos normalizados del MPC cuando tengan interpretación y dominio apropiados, o parámetros de una política heurística). Cada evaluación consistirá en un conjunto fijo de episodios sintéticos, no una medición real. BO utilizará un sustituto probabilístico y una adquisición documentada; la búsqueda aleatoria será la línea base con **igual presupuesto de evaluaciones**.

Se evitará usar BO para optimizar indiscriminadamente cientos de parámetros de una red neuronal. Se compararán rendimiento final, *simple regret* estimado, variabilidad y costo total de evaluaciones. Se separarán semillas del optimizador de las semillas de los escenarios.

### E3 — Optimización multiobjetivo

Se estudiará el vector

$$
F(\pi)=\left(\mathbb E[C_E],\ \mathbb E[C_D],\ \mathbb E[C_I],\ \mathbb E[C_S]\right),
$$

con restricciones de factibilidad. Se compararán configuraciones no dominadas, se visualizará una aproximación al frente de Pareto y se discutirá el efecto de las preferencias. Se distinguirá **frente aproximado** de frente verdadero desconocido. Si se usa NSGA-II, se reportarán presupuesto y semilla; si se utiliza BO multiobjetivo, se justificará su mayor costo computacional.

### E4 — Meta-learning y adaptación

Una **tarea** $\tau$ será una configuración coherente del entorno: distribución de demanda, rango de viscosidad, eficiencia de bombas, perturbaciones y accesibilidad, manteniendo explícitas las variables que cambian y las invariantes. Se definirán distribuciones $p_{\mathrm{train}}(\tau)$ y $p_{\mathrm{test}}(\tau)$ con **tareas disjuntas**, además de escenarios fuera de distribución.

Se implementará un método auténtico de metaaprendizaje, por ejemplo Reptile o MAML de primer orden sobre una política reducida, **solo si la complejidad y estabilidad se verifican**. Las líneas base serán entrenamiento desde cero, política fija y fine-tuning convencional con presupuesto igual de interacciones en la tarea nueva. La métrica principal será la curva de desempeño **frente al número de muestras de adaptación**, no únicamente el resultado después de un entrenamiento arbitrariamente largo.

**Riesgo explícito:** meta-RL con PPO completo puede exceder el presupuesto computacional y pedagógico. Si no se obtiene un resultado estable y reproducible, se mantendrá una demostración pequeña y honesta de meta-learning dentro del mismo mundo, sin atribuirle ventajas no observadas.

### E5 — Robot, OR y aprendizaje bajo incertidumbre

Se compararán al menos cuatro variantes: (i) no inspeccionar, (ii) calendario fijo de inspecciones, (iii) rutas optimizadas por OR con prioridades fijas, (iv) coordinación con prioridades basadas en información y ejecución adaptativa. Si se añade una política RL robótica, se comparará **manteniendo constante el planificador** para aislar su contribución.

**Métricas:** tiempo de inspección, distancia recorrida, batería, porcentaje de tareas cumplidas, incertidumbre posterior, costo operacional total y mejora **neta** frente a no inspeccionar. Se evitará interpretar una menor entropía como beneficio económico sin demostrar su efecto en decisiones.

### E6 — Ablaciones transversales

Se desactivarán, uno a uno, estimación de salud, inspecciones, adaptación, variación de demanda y proyección de acciones, según la seguridad del entorno. Cada ablación tendrá una pregunta causal explícita. Las comparaciones usarán escenarios pareados y evitarán modificar simultáneamente múltiples componentes.

## 9. Protocolo estadístico y reproducibilidad

### 9.1. Separación de escenarios

Los conjuntos **entrenamiento, validación y prueba** se definirán por escenarios generadores, no solo por semillas. En meta-learning se añadirá partición independiente de tareas. Los parámetros seleccionados por BO o búsqueda de hiperparámetros se decidirán **sin consultar los resultados finales de prueba**.

### 9.2. Diseño de evaluación

- Predefinir variables de respuesta primarias y secundarias, horizonte, reglas de parada y condiciones de fallo.
- Utilizar escenarios pareados entre algoritmos (*common random numbers*) cuando el acoplamiento estocástico sea válido.
- Evaluar con múltiples semillas de entrenamiento y de simulación; fijar el número definitivo tras un piloto de variabilidad.
- Reportar distribuciones, diferencias pareadas e intervalos de confianza o incertidumbre por remuestreo a nivel de **episodio o escenario independiente**, evitando tratar pasos temporales autocorrelacionados como réplicas independientes.
- Documentar fallos de convergencia del solver, episodios truncados y acciones rechazadas; no eliminarlos silenciosamente.
- Registrar versiones de paquetes, configuración, semillas, hardware, duración de entrenamiento y artefactos de política.

### 9.3. Robustez y generalización

Se propondrán escenarios nominales, de estrés y fuera de distribución: incremento de viscosidad, demanda extrema, degradación de bomba, ruido de sensor, pérdida temporal de capacidad, inspección imprecisa y bloqueo de ruta. La evaluación debe revelar cuándo una política falla y **si el mecanismo de respaldo conserva factibilidad**.

### 9.4. Validez interna y externa

La validez interna depende de la coherencia del DGP, comparaciones justas y ausencia de fuga de información. La validez externa hacia sistemas industriales **no se infiere** de resultados sintéticos. El experimento solo puede respaldar afirmaciones sobre el mundo modelado y las distribuciones evaluadas.

## 10. Validación del simulador antes del aprendizaje

Se establece una secuencia obligatoria de aceptación:

| Puerta | Prueba | Criterio de aceptación propuesto |
|---|---|---|
| V0 | Dimensiones y signos | Todas las ecuaciones dimensionalmente consistentes; convención de incidencia verificada |
| V1 | Conservación de masa | Residuales de nodos y tanques bajo tolerancias relativas y absolutas declaradas |
| V2 | Hidráulica | Presiones y caudales satisfacen energía y fricción; sin soluciones espurias |
| V3 | Bombas | Altura, eficiencia y potencia físicamente admisibles en dominio operativo |
| V4 | Límites | Ninguna acción ejecutada viola restricciones duras sin registrarse como fallo de seguridad |
| V5 | Casos analíticos | Redes simples de una tubería y una bomba concuerdan con soluciones de referencia |
| V6 | Sensibilidad | Mayor fricción incrementa pérdida de presión a caudal fijado; pruebas de monotonicidad pertinentes |
| V7 | Aleatoriedad | Semillas reproducibles; distribuciones de ruido y escenarios verificadas |
| V8 | Paso temporal | Inventarios estables al refinar $\Delta t$ dentro del dominio de validez |
| V9 | Observabilidad | El agente no recibe variables latentes o resultados futuros por error |
| V10 | Robot | Rutas válidas, tiempos, batería, observaciones y restricciones comprobados |

Los umbrales numéricos se establecerán **antes de ejecutar las comparaciones finales**. Si falla una puerta crítica, se detiene el entrenamiento y se corrige el simulador, preservando registro de cambios.

## 11. Arquitectura de software propuesta

```text
hydro_lab_g2/
├── README.md
├── docs/
│   ├── scientific_design_G2.3.md
│   ├── assumptions_and_units.md
│   └── validation_protocol.md
├── configs/
│   ├── network.yaml
│   ├── scenarios.yaml
│   └── experiments.yaml
├── src/hydro_lab/
│   ├── physics/          # balances, bombas, fricción y solver
│   ├── dynamics/         # inventarios, demanda, salud y ruido
│   ├── sensing/          # sensores, creencias e inspecciones
│   ├── robotics/         # grafo de acceso, batería y rutas
│   ├── hierarchy/        # coordinador y contratos de interfaz
│   ├── environments/     # interfaz Gymnasium y seguridad
│   ├── controllers/      # reglas, MPC, PPO
│   ├── optimization/     # BO y multiobjetivo
│   ├── adaptation/       # tareas, transferencia y meta-learning
│   ├── evaluation/       # métricas, diseños y ablaciones
│   └── dashboard/        # vistas de operación y aprendizaje
├── tests/
│   ├── unit/
│   ├── physics/
│   ├── integration/
│   └── regression/
├── scripts/
└── artifacts/            # resultados versionados; no datos reales
```

Las interfaces mínimas incluirán `reset(seed, scenario)`, `step(action)`, observación, recompensa, `terminated`, `truncated` e `info` con métricas físicas y acciones realmente ejecutadas. El solucionador hidráulico y el DGP deberán poder probarse **sin importar Gymnasium ni PPO**. Los componentes de optimización consumirán una API de evaluación común, con presupuestos explícitos.

## 12. Evidencias visuales mínimas

Se prepararán **cinco familias de gráficas científicas**, no una plataforma de tableros: (i) caudales, presiones, inventarios y costo; (ii) curvas y métricas de control reglas–MPC–PPO; (iii) BO, adquisición y Pareto; (iv) adaptación por muestras; (v) ruta robótica y valor neto de inspección. Cada figura identificará variables verdaderas del simulador, observaciones ruidosas, estimaciones y acciones. No se desarrollarán interfaces de usuario complejas.

## 13. Programación del laboratorio y correspondencia exacta con el syllabus G2.3

**Jornadas:** martes 27 y miércoles 28 de octubre de 2026. Cada jornada contiene dos sesiones de **110 minutos** con una pausa intermedia de **20 minutos**. La hora de inicio está pendiente de confirmación institucional. El tiempo total es de **440 minutos académicos y 40 minutos de pausas**.

### Día 1 — 27 de octubre

| Sesión | Minutos | Componente científico que debe estar listo |
|---|---:|---|
| **1. MDP avanzados y decisiones secuenciales** | 110 | Modelo físico sintético, política por reglas, estados y transiciones, Bellman, restricciones, trayectorias con costos diferidos |
| **Pausa** | **20** | |
| **2. Deep RL y policy gradients** | 110 | PPO preentrenado, ecuaciones de gradiente y objetivo recortado, comparación reglas–MPC–PPO, estrés y fallos |

### Día 2 — 28 de octubre

| Sesión | Minutos | Componente científico que debe estar listo |
|---|---:|---|
| **3. Bayesian Optimization y multiobjetivo** | 110 | Función de evaluación de configuraciones, sustituto y adquisición, búsqueda aleatoria, soluciones no dominadas |
| **Pausa** | **20** | |
| **4. Meta-learning y RL + Investigación de Operaciones** | 110 | Distribuciones de tareas disjuntas, Reptile o MAML reducido con líneas base, robot con rutas OR y observaciones útiles |

**Correspondencia minuto a minuto:** el desglose didáctico detallado y las preguntas de contraste se encuentran en la sección 8 del syllabus G2.3. El presente documento no duplica las explicaciones docentes: especifica qué debe producir, validar y exponer el software para cada demostración.

**Regla de prioridad:** un solo simulador coherente; las variantes didácticas serán **proyecciones o configuraciones reducidas del mismo sistema**, nunca aplicaciones independientes. El robot se activa únicamente en la cuarta sesión y su presencia no condiciona la ejecución de las tres primeras.

### 13.1. Matriz de aceptación docente

| Sesión | Evidencia mínima obligatoria | Si falla un componente |
|---|---|---|
| 1 | MDP explícito, simulación con reglas y trayectorias verificadas | Caso hidráulico reducido y trayectorias previamente validadas |
| 2 | PPO reproducible y métricas separadas; MPC si supera validación | PPO y reglas; MPC como referencia conceptual sin comparación empírica |
| 3 | BO vs búsqueda aleatoria con igual presupuesto; conjunto no dominado | Evaluaciones precomputadas reproducibles y visualizaciones estáticas |
| 4 | Adaptación genuina frente a líneas base; rutas OR factibles y efecto de inspección | Meta-learning en subproblema reducido del mismo mundo; rutas OR sin afirmar RL robótico no implementado |

No se aceptará reemplazar un experimento fallido por resultados ficticios. Los materiales de respaldo deben proceder de ejecuciones verificadas.

## 14. Riesgos, decisiones pendientes y criterios de reducción de alcance

| ID | Riesgo o decisión | Tratamiento propuesto |
|---|---|---|
| D-01 | Formulación nodal o reducida de hidráulica | Comparar con casos analíticos y seleccionar la más transparente que conserve acoplamiento |
| D-02 | Parametrización físicamente coherente | Estudio dimensional, sensibilidad y calibración sintética documentada |
| D-03 | No convexidad e inviabilidad hidráulica | Solver robusto, diagnósticos y política de respaldo |
| D-04 | Estado latente y estimación | Establecer sensores y creencias antes de comparar controladores |
| D-05 | Escala temporal del coordinador y robot | Definir cronograma de eventos y sincronización determinista |
| D-06 | Complejidad de PPO y meta-RL | Prototipo reducido; no atribuir éxito si no se demuestra |
| D-07 | Costos de BO | Limitar dimensión y presupuesto; comparar con búsqueda aleatoria |
| D-08 | Interpretación del valor de información | Comparar mejora de decisión neta, no solo reducción de incertidumbre |
| D-09 | Seguridad y aprendizaje | Factibilidad fuera de recompensa, con registro de acciones filtradas |
| D-10 | Duración docente | Ensayar cuatro sesiones de 110 min con 20 min de pausa en cada jornada; rutas de contingencia |

**Regla de reducción de alcance:** si la implementación completa amenaza el rigor o el tiempo, se preservan primero (a) física validada, (b) control reglas–MPC–PPO, (c) optimización y (d) una demostración robótica funcional. Meta-learning podrá usar una tarea reducida dentro del mismo entorno, siempre con metaentrenamiento real y comparación honesta. Ningún tema se presentará como experimentalmente validado si solo se expuso conceptualmente.

## 15. Plan de desarrollo y puertas de avance

**Fase A — Modelo físico y pruebas.** Congelar topología candidata, unidades, ecuaciones, parámetros y solver; superar V0–V8. **Entregable:** DGP reproducible con casos de referencia.

**Fase B — Observabilidad y seguridad.** Implementar sensores, estado latente, filtros de acción y métricas; superar V9. **Entregable:** entorno reproducible con escenarios y líneas base.

**Fase C — Control.** Implementar reglas, MPC y PPO; comparar con protocolo pareado. **Entregable:** informe de desempeño y fallos.

**Fase D — Optimización.** Integrar BO y análisis multiobjetivo sobre objetivos y parámetros explícitos. **Entregable:** resultados con presupuestos y frentes aproximados.

**Fase E — Adaptación.** Definir distribución de tareas, implementar método de meta-learning y líneas base; evaluar eficiencia muestral. **Entregable:** curvas de adaptación con incertidumbre.

**Fase F — Robot y coordinación.** Construir grafo logístico, OR, observaciones de inspección y política adaptativa; superar V10. **Entregable:** comparaciones de inspección y valor de información.

**Fase G — Integración docente.** Consolidar gráficas, notebooks, resultados precomputados y ensayo de dos jornadas de cuatro horas. **Entregable:** paquete didáctico separado del documento científico.

No se fija un calendario de ejecución hasta evaluar la complejidad real de las fases A y B.

## 16. Bibliografía científica de diseño

### Decisión secuencial, RL y control

1. Sutton, R. S., & Barto, A. G. (2018). *Reinforcement Learning: An Introduction* (2nd ed.). MIT Press. http://incompleteideas.net/book/the-book-2nd.html
2. Puterman, M. L. (1994). *Markov Decision Processes: Discrete Stochastic Dynamic Programming*. Wiley.
3. Schulman, J., Wolski, F., Dhariwal, P., Radford, A., & Klimov, O. (2017). *Proximal Policy Optimization Algorithms*. arXiv:1707.06347. https://arxiv.org/abs/1707.06347
4. Rawlings, J. B., Mayne, D. Q., & Diehl, M. M. (2017). *Model Predictive Control: Theory, Computation, and Design* (2nd ed.). Nob Hill Publishing.
5. Altman, E. (1999). *Constrained Markov Decision Processes*. Chapman & Hall/CRC.
6. Kaelbling, L. P., Littman, M. L., & Cassandra, A. R. (1998). Planning and acting in partially observable stochastic domains. *Artificial Intelligence, 101*(1–2), 99–134. https://doi.org/10.1016/S0004-3702(98)00023-X

### Hidráulica y simulación

7. White, F. M. (2011). *Fluid Mechanics* (7th ed.). McGraw-Hill. Referencia general de balances y flujo interno.
8. Wylie, E. B., Streeter, V. L., & Suo, L. (1993). *Fluid Transients in Systems*. Prentice Hall. Referencia para reconocer fenómenos **excluidos** del modelo cuasiestacionario.
9. Chaudhry, M. H. (2014). *Applied Hydraulic Transients* (3rd ed.). Springer. https://doi.org/10.1007/978-1-4614-8538-4. Contexto de validez y límites de modelación hidráulica.

### Optimización, adaptación y planificación

10. Frazier, P. I. (2018). *A Tutorial on Bayesian Optimization*. arXiv:1807.02811. https://arxiv.org/abs/1807.02811
11. Deb, K., Pratap, A., Agarwal, S., & Meyarivan, T. (2002). A fast and elitist multiobjective genetic algorithm: NSGA-II. *IEEE Transactions on Evolutionary Computation, 6*(2), 182–197. https://doi.org/10.1109/4235.996017
12. Finn, C., Abbeel, P., & Levine, S. (2017). Model-Agnostic Meta-Learning for Fast Adaptation of Deep Networks. *Proceedings of Machine Learning Research, 70*, 1126–1135. https://proceedings.mlr.press/v70/finn17a.html
13. Nichol, A., Achiam, J., & Schulman, J. (2018). On First-Order Meta-Learning Algorithms. arXiv:1803.02999. https://arxiv.org/abs/1803.02999
14. LaValle, S. M. (2006). *Planning Algorithms*. Cambridge University Press. https://lavalle.pl/planning/
15. Bertsimas, D., & Tsitsiklis, J. N. (1997). *Introduction to Linear Optimization*. Athena Scientific.
16. Howard, R. A. (1966). Information value theory. *IEEE Transactions on Systems Science and Cybernetics, 2*(1), 22–26. https://doi.org/10.1109/TSSC.1966.300074

**Uso de la bibliografía:** fundamenta decisiones metodológicas y límites de modelos; **no certifica** los parámetros sintéticos ni constituye evidencia empírica del desempeño del laboratorio.

## 17. Declaración de estado y próximo hito

**Decisiones conservadas en G2.3:** laboratorio único, topología pequeña con dos ramas, hidráulica cuasiestacionaria, inventarios dinámicos, observabilidad parcial, jerarquía central–control–robot, inspección como adquisición de información, comparaciones con reglas/MPC/PPO, BO, multiobjetivo, meta-learning auténtico y OR; validación previa a entrenamiento.

**Reducción pedagógica G2.3:** quedan fuera gemelos digitales, GNN, dashboards como producto y cualquier integración física externa. El diseño conserva el robot de inspección como subproblema discreto de información y rutas; la arquitectura jerárquica no exige desarrollar tres controladores aprendidos. La programación responde al syllabus G2.3 (27 y 28 de octubre, cuatro sesiones de 110 minutos).

**Aún no demostrado:** que el sistema numérico sea estable, que los parámetros produzcan escenarios plausibles, que PPO o meta-learning converjan, que BO supere líneas base, que la inspección aporte utilidad neta o que el paquete completo pueda ejecutarse dentro del presupuesto docente. Ninguna de estas afirmaciones debe anticiparse.

**Próximo hito científico recomendado:** documento **G2.4 — Especificación matemática cerrada, parametrización y protocolo de validación del DGP**, seguido de implementación y pruebas del simulador **antes** de desarrollar controladores aprendidos.

---

**Álvaro Montenegro**  
CEO — Learning Systems Institute (LSI) y Aprendizaje Profundo SAS  
**Correo:** ammontenegrod@gmail.com  
**Celular:** +57 300 571 2192

*Documento científico de diseño · G2.3 · Bogotá, 18 de octubre de 2026*
