# Intelligent Hydrocarbon Transportation Network
## Especificación matemática cerrada y contrato computacional — Generación 2, versión 0.4 (G2.4)

**Programa:** Inteligencia artificial avanzada aplicada a retos estratégicos  
**Contexto:** Ecopetrol — Universidad de los Andes · 27 y 28 de octubre de 2026  
**Autor:** Álvaro Montenegro · Learning Systems Institute (LSI) / Aprendizaje Profundo SAS  
**Fecha:** Bogotá, 18 de octubre de 2026  
**Documentos normativos internos:** `Syllabus_IA_Avanzada_Ecopetrol_Uniandes_G2.3.md`; `Laboratorio_Red_Inteligente_Hidrocarburos_Diseno_Cientifico_G2.3.md`  
**Estado:** **Especificación para implementación; NO equivale a simulador ejecutado, calibrado ni validado.**  
**Versionamiento:** preservar G0.2, G2.1, G2.2 y G2.3. Esta versión fija decisiones antes abiertas en G2.3. No introduce gemelos digitales, GNN ni tableros.

---

## 0. Decisión arquitectónica y criterios de aceptación

Se implementará **un único mundo sintético**: una red hidráulica de cinco nodos y dos ramas, dos inventarios, tres bombas y un robot de inspección discreto. Todos los experimentos usarán el mismo motor físico, DGP, registro de unidades y generador de escenarios. El robot y el metaaprendizaje operarán mediante vistas reducidas del mundo, sin crear plantas independientes.

**Principios innegociables:** (i) conservación de masa y ecuaciones hidráulicas verificadas; (ii) seguridad mediante restricciones y respaldo, no únicamente recompensa; (iii) diferencia explícita entre estado físico, observación y creencia; (iv) separación de entrenamiento, validación y prueba por tareas y semillas; (v) métricas desagregadas; (vi) comparaciones pareadas; (vii) resultados nunca inventados. Los números de este documento son **parámetros sintéticos de ingeniería didáctica**: su plausibilidad física es una hipótesis de diseño que debe verificarse.

**Definición de terminado de Fase 1:** ecuaciones, unidades, parámetros, dominios, interfaces, casos de prueba y decisiones de factibilidad están fijados. **Definición de terminado de Fase 2:** el código satisface los ensayos de aceptación de §14. No se confunden ambos hitos.


## 1. Topología, convenciones y variables

Se fijan $V=\{0,1,2,3,4\}$ y aristas orientadas

$$
E=\{(0,1),(1,2),(2,4),(1,3),(3,4)\}.
$$

El nodo 0 representa el tanque de origen, 1 el colector, 2 y 3 las estaciones de rama, y 4 el tanque receptor. Las bombas se ubican en las aristas $(0,1)$, $(1,2)$ y $(1,3)$; las otras dos aristas son pasivas. Hay válvulas antirretorno idealizadas; $q_e\geq 0$. Las dos ramas comparten la alimentación y terminan en el mismo tanque. La matriz de incidencia $B$ usa $-1$ en origen y $+1$ en destino:

$$
B=
\begin{pmatrix}
-1&0&0&0&0\\
1&-1&0&-1&0\\
0&1&-1&0&0\\
0&0&0&1&-1\\
0&0&1&0&1
\end{pmatrix}.
$$

En nodos internos $Bq=0$. En los extremos, $Bq=(-Q,0,0,0,Q)^\top$ y $Q=q_{01}=q_N+q_S$, con $q_N=q_{12}=q_{24}$ y $q_S=q_{13}=q_{34}$. Para aportes externos positivos $b$, la identidad de G2.3 es $Bq=-b$, con $b=(Q,0,0,0,-Q)^\top$.

Se trabajará con **altura hidráulica total simplificada** $\mathcal H_i=z_i+p_i/(\rho g)$, en metros de columna de líquido. La energía cinética en nodos se omite por hipótesis de reservorios/colectores de velocidad despreciable; las pérdidas de tubería incluyen efectos de velocidad. $p_i$ es manométrica y $z_i$ es elevación geométrica. No se asignarán presiones arbitrarias incompatibles con los balances.

### 1.1. Tanques y cotas

Los tanques son depósitos abiertos, con superficie a presión atmosférica, área transversal constante y sin dinámica de mezcla. Sus niveles y alturas de frontera son

$$
\mathcal H_0=z_{0,\mathrm{base}}+\frac{V_0}{A_0},\qquad
\mathcal H_4=z_{4,\mathrm{base}}+\frac{V_4}{A_4}.
$$

Se fijan $z_{0,\mathrm{base}}=10\,\mathrm m$, $z_{4,\mathrm{base}}=16\,\mathrm m$, $A_0=A_4=250\,\mathrm{m^2}$, $V_{0,0}=750\,\mathrm{m^3}$ y $V_{4,0}=500\,\mathrm{m^3}$. Por tanto, al inicio $\mathcal H_0=13\,\mathrm m$ y $\mathcal H_4=18\,\mathrm m$; el desnivel total inicial es $5\,\mathrm m$.

Límites operacionales: $V_0,V_4\in[200,1500]\,\mathrm{m^3}$. El área fija simplifica la variación de nivel y mantiene estados continuos.


### 1.2 Arquitectura general del laboratorio

![Arquitectura del laboratorio de transporte de hidrocarburos G2.4: red hidráulica, robot de inspección y componentes computacionales](arquitectura_laboratorio_G2.4.png)

*Figura 1. Representación conceptual de la infraestructura sintética, el robot de inspección y las capas de simulación, observación, decisión y evaluación.*



## 2. Modelo hidráulico reducido, cerrado y resoluble

### 2.1. Ley de pérdida de carga

Para la **implementación docente inicial** se adopta una ley turbulenta cuadrática por arista:

$$
h_{L,e}(q_e;\mu)=R_e(\mu)\,q_e|q_e|,\qquad
R_e(\mu)=R_e^0\left(\frac{\mu}{\mu_0}\right)^{0.20},
$$

con $q$ en $\mathrm{m^3/s}$ y $R$ en $\mathrm{s^2/m^5}$. La dependencia en viscosidad es **fenomenológica y sintética**, no una correlación universal de Darcy–Weisbach. Se adopta para mantener un solver robusto en CPU. La validación incluirá una comparación independiente con Darcy–Weisbach en varios puntos; si la discrepancia es excesiva, se recalibrará la ley reducida **antes** de entrenar algoritmos. No se afirmará que el exponente $0.20$ sea una ley física.

| Arista | $R_e^0$ ($\mathrm{s^2/m^5}$) | Bomba |
|---|---:|---|
| $0\to1$ | 900 | P0 |
| $1\to2$ | 800 | PN |
| $2\to4$ | 800 | — |
| $1\to3$ | 1100 | PS |
| $3\to4$ | 1100 | — |

Así, $R_N^0=1600$ y $R_S^0=2200$. La rugosidad, diámetros y longitudes quedan como **metadatos de contraste Darcy–Weisbach** y no intervienen por duplicado en la ley reducida. Para esa comprobación independiente se proponen longitudes $(2000,1500,1500,1800,1800)$ m y diámetro uniforme de 0.30 m; los $R_e^0$ anteriores **no se deducen** de estos valores. No se hará una afirmación de calibración cruzada hasta completar el contraste.

### 2.2. Bombas y controles

Cada bomba añade altura

$$
h_{P,k}(q,u,h)=h_k\,[a_k u^2-b_k q^2]_+,
\quad [x]_+=\max(0,x).
$$

Se fija $h_k\in[0.65,1]$, $u_k\in[0.60,1.00]$ cuando está disponible y $u_k=0$ cuando está desconectada. Los parámetros sintéticos son:

| Bomba | $a_k$ (m) | $b_k$ ($\mathrm{s^2/m^5}$) | Caudal asociado |
|---|---:|---:|---|
| P0 | 25 | 250 | $Q$ |
| PN | 16 | 500 | $q_N$ |
| PS | 16 | 500 | $q_S$ |

**Convención operacional:** las tres bombas permanecen disponibles y encendidas en el caso nominal; una indisponibilidad deshabilita la rama afectada o activa una configuración de respaldo factible. Una bomba apagada no se tratará como tubería libre con pérdida de carga nula: el estado de apagado **cierra su rama** en este prototipo. La bomba P0 indisponible impide transporte y se activa una transición de parada segura.

Eficiencia sintética, acotada:

$$
\eta_k(q,u,h)=\operatorname{clip}\!\left(
0.78-0.08(u-0.82)^2-0.04\left(\frac{q}{q_{k,\mathrm{ref}}}-1\right)^2
-0.08(1-h),\,0.55,\,0.82\right),
$$

con $q_{0,\mathrm{ref}}=0.12$ y $q_{N,\mathrm{ref}}=q_{S,\mathrm{ref}}=0.06$ $\mathrm{m^3/s}$. La potencia es $P_k=\rho g q_k h_{P,k}/\eta_k$ en W. No se añade consumo fijo de encendido en G2.4: se documenta como exclusión. Se penalizan cambios de consignas mediante un costo de maniobra separado.

### 2.3. Reducción a dos incógnitas

Sea $\Delta\mathcal H=\mathcal H_4-\mathcal H_0$. Para ramas disponibles, el balance entre reservorios exige

$$
h_{P,0}(Q,u_0,h_0)+h_{P,N}(q_N,u_N,h_N)
-R_{01}Q^2-(R_{12}+R_{24})q_N^2-\Delta\mathcal H=0,
$$

$$
h_{P,0}(Q,u_0,h_0)+h_{P,S}(q_S,u_S,h_S)
-R_{01}Q^2-(R_{13}+R_{34})q_S^2-\Delta\mathcal H=0,
$$

$$
Q=q_N+q_S,\qquad q_N,q_S\geq0.
$$

Se resolverá con `scipy.optimize.least_squares` sujeto a $0\le q_N,q_S\le 0.15$ $\mathrm{m^3/s}$, **y se aceptará una solución únicamente si los residuos físicos son pequeños y no hay límites operativos violados**. La cota numérica de búsqueda no reemplaza las restricciones físicas. Se probarán varias inicializaciones deterministas; los puntos de frontera y ramas cerradas se resolverán explícitamente como casos unidimensionales.

**Caso de control analítico:** con $\Delta\mathcal H=5$, $\mu=\mu_0$, $h_k=1$, $u_0=u_N=u_S=0.8$, ambas ramas abiertas, las ecuaciones se reducen a

$$
26.24-1150(q_N+q_S)^2-2100q_N^2=5,
$$
$$
26.24-1150(q_N+q_S)^2-2700q_S^2=5.
$$

De su diferencia se obtiene $q_N/q_S=\sqrt{2700/2100}$; sustituyendo se obtiene una raíz positiva única para ese caso. **El valor numérico exacto se verificará con un cálculo independiente durante Fase 2**. Este ejemplo sirve como prueba contra una implementación incorrecta de signos o acoplamiento.

### 2.4. Reconstrucción de alturas y presiones

Una vez resueltos los caudales:

$$
\mathcal H_1=\mathcal H_0+h_{P,0}-R_{01}Q^2,
$$
$$
\mathcal H_2=\mathcal H_1+h_{P,N}-R_{12}q_N^2,
\quad
\mathcal H_3=\mathcal H_1+h_{P,S}-R_{13}q_S^2.
$$

Las dos reconstrucciones de $\mathcal H_4$ deben coincidir dentro de tolerancia. Se fijan elevaciones internas $(z_1,z_2,z_3)=(11,13,13)$ m y se calcula $p_i=\rho g(\mathcal H_i-z_i)$. En nodos internos se requiere $0\le p_i\le 600\,000$ Pa; la presión de superficie de tanques es cero manométrica. Se limita velocidad media de cada arista a $v_e\le 3.0$ m/s, calculada con $D=0.30$ m; este límite restringe caudales a aproximadamente $0.212$ $\mathrm{m^3/s}$ y por ello **no** es el límite activo en el dominio de búsqueda de $0.15$ por rama. El caudal total también se verifica contra velocidad de la arista compartida; esta comprobación es obligatoria.

### 2.5. Factibilidad y seguridad

El solver devolverá uno de: `FEASIBLE`, `INFEASIBLE_PHYSICAL`, `NUMERICAL_FAILURE`. Las condiciones de aceptación son:

- residuos de balances de altura $\le10^{-6}$ m para los casos nominales y $\le10^{-4}$ m para pruebas de estrés;
- continuidad en cada nodo interno $\le10^{-9}$ $\mathrm{m^3/s}$ (por construcción);
- $q\ge0$, presiones dentro de rango, velocidad por arista, bombas disponibles y potencia no negativa;
- volúmenes de siguiente paso dentro de límites;
- estados y costos finitos, sin NaN ni infinitos.

**Seguridad en el entorno RL:** la acción de la política se transforma mediante un **filtro de acciones** reproducible: probar acción propuesta; si es inviable, buscar la consigna segura más cercana entre una malla determinista prevalidada y un conjunto de acciones de respaldo. Registrar `action_requested`, `action_executed`, `intervention_reason`, `intervention_distance`. Si no hay acción que mantenga factibilidad, se declara episodio terminado por contingencia, con costo explícito y sin fabricar caudales. La malla y su orden de desempate se congelarán antes del entrenamiento.

## 3. Discretización temporal y balances de inventario

Se fija $\Delta t=900$ s (15 minutos), horizonte de episodio $T=96$ pasos (24 h), descuento de RL $\gamma=0.99$ por paso. Los volúmenes evolucionan como

$$
V_{0,t+1}=V_{0,t}+900(s_t-Q_t),
$$
$$
V_{4,t+1}=V_{4,t}+900(Q_t-d_t^{\mathrm{served}}),
$$

con $s_t$ aporte exógeno al tanque de origen y $d_t^{\mathrm{served}}$ entrega desde el tanque de destino, ambos en $\mathrm{m^3/s}$. Se fija **demanda perdida por periodo**, sin pedidos acumulados.

**Cierre de inventario:** la entrega se calcula de forma conservadora mediante

$$
d_t^{\mathrm{served}}=
\min\!\left(d_t,\max\left(0,\frac{V_{4,t}+900Q_t-V_4^{\min}}{900}\right)\right).
$$

El caudal hidráulico $Q_t$ debe cumplir

$$
Q_t\le \frac{V_{0,t}-V_0^{\min}}{900}+s_t,
\qquad
Q_t\le\frac{V_4^{\max}-V_{4,t}}{900}+d_t^{\mathrm{served}}.
$$

La segunda desigualdad y la fórmula de entrega se resuelven de manera consistente; no se recorta inventario *después* de simular, porque ello rompería la conservación. La capacidad física y los caudales de suministro son parte del filtro de factibilidad. **Importante:** si la red no puede transportar y el tanque receptor puede abastecer demanda, la entrega sigue siendo posible hasta su reserva mínima.

Se fija aporte nominal $s_t=0.11$ $\mathrm{m^3/s}$, demanda media $\bar d=0.11$ $\mathrm{m^3/s}$ y cotas $0\le d_t\le0.17$; estos valores deben pasar la prueba de horizonte de 24 h sin sesgar la evaluación hacia escasez inevitable. La red hidráulica opera con caudales compatibles con estos inventarios; no se obliga a que el suministro exógeno coincida exactamente con el bombeo en cada paso.

## 4. Proceso generador de datos sintéticos (DGP)

**Todos los sorteos se realizan con generadores independientes de NumPy** derivados de una semilla maestra, con subflujos separados para escenarios, observaciones, fallas y optimizadores. Se registrará versión de bibliotecas y generador.

### 4.1. Parámetros físicos y perturbaciones

| Magnitud | Nominal | Distribución por episodio / dinámica |
|---|---|---|
| Densidad $\rho$ | 850 kg/m³ | Fija dentro de episodio; en entrenamiento uniforme [830,870] |
| Viscosidad $\mu_0$ | 0.020 Pa·s | Evolución log-AR(1), mediana inicial 0.020 |
| Gravedad $g$ | 9.81 m/s² | Constante |
| Demanda media $\bar d$ | 0.11 m³/s | Uniforme [0.09,0.13] en entrenamiento |
| Amplitud relativa $A_d$ | 0.15 | Uniforme [0.05,0.20] |
| Periodo $T_d$ | 24 h | Fijo |
| Persistencia $\varphi_d$ | 0.75 | Fija |
| Innovación demanda $\sigma_d$ | 0.006 m³/s | Normal; truncar demanda final a [0,0.17] |
| Persistencia log-viscosidad $\varphi_\mu$ | 0.97 | Fija |
| Innovación log-viscosidad $\sigma_\mu$ | 0.015 | Normal |
| Salud inicial $h_k$ | 0.95 | Uniforme [0.90,1.00] |
| Tarifa | 0.18 unidades monetarias/kWh | Bloques horarios §4.3 |

La demanda se genera como

$$
d_t=\operatorname{clip}\left\{
\bar d[1+A_d\sin(2\pi t/96+\phi_d)]+\zeta_t,\ 0,\ 0.17
\right\},
\quad
\zeta_{t+1}=0.75\zeta_t+0.006\varepsilon_{t+1},
$$

con $\phi_d\sim\mathrm{Uniform}(0,2\pi)$ y $\varepsilon\sim N(0,1)$. El estado inicial $\zeta_0$ se sortea de la distribución estacionaria normal con varianza $\sigma_d^2/(1-0.75^2)$.

La viscosidad satisface

$$
\log\mu_{t+1}=\log(0.020)+0.97[\log\mu_t-\log(0.020)]
+0.015\,\epsilon_{t+1}.
$$

Se trunca a $[0.008,0.080]$ Pa·s **registrando** los eventos de truncamiento. La fase de demanda, no el reloj de tarifa, cambia entre episodios.

### 4.2. Salud, deterioro e indisponibilidad

Para las tres bombas:

$$
h_{k,t+1}=\operatorname{clip}\left(
h_{k,t}-\kappa\,\left(\frac{q_{k,t}}{q_{k,\mathrm{ref}}}\right)^2
\left(\frac{u_{k,t}}{0.8}\right)^2+\omega_{k,t},
0.65,1\right),
$$

con $\kappa=2\times10^{-5}$ **por paso** y $\omega_{k,t}\sim N(0,2\times10^{-5})$; si la bomba está apagada, se fija desgaste cero. No hay reparación automática. El riesgo de indisponibilidad por paso se fija como hipótesis sintética:

$$
\lambda_{k,t}=\min\{0.002,\ 0.00005+0.001(1-h_{k,t})\}.
$$

Una vez indisponible, la bomba permanece así hasta fin de episodio; el entorno activa cierre de rama o parada de P0. **No** se extrapolan estas probabilidades a confiabilidad industrial. Para evitar que un evento raro vuelva irreproducible la demostración, se guardarán también escenarios de falla deterministas, con fecha de falla prefijada, **separados de la evaluación estocástica principal**.

### 4.3. Tarifa

Tarifa sintética conocida, en unidades monetarias (UM)/kWh:

$$
c_t=\begin{cases}
0.12,&0\le t<24,\\
0.18,&24\le t<64,\\
0.30,&64\le t<84,\\
0.15,&84\le t<96.
\end{cases}
$$

La energía por paso es $E_t=(\sum_k P_{k,t})\times(900/3.6\times10^6)$ kWh; costo $C_{E,t}=c_t E_t$ UM. Los intervalos son tiempos **relativos al episodio**, no horas reales de operación de Ecopetrol.

## 5. Observación, incertidumbre y creencias

El estado Markoviano completo del simulador contiene $(V_0,V_4,h_0,h_N,h_S,\mu,\zeta,\phi_d,\bar d,A_d,\text{disponibilidad},t,\ell,\text{batería})$ y los estados de los procesos de ruido que se decidan correlacionar. La **observación** del controlador hidráulico es

$$
o_t=(\widetilde V_0,\widetilde V_4,\widetilde d_t,c_t,
\widetilde Q_{t-1},\widetilde p_{1,t-1},
\widetilde p_{2,t-1},\widetilde p_{3,t-1},
u_{t-1},t/96,\widehat h_{0,t},\widehat h_{N,t},\widehat h_{S,t}).
$$

Las mediciones de volumen tienen ruido gaussiano $\sigma_V=2$ m³, demanda $\sigma_d^{\mathrm{sensor}}=0.003$ m³/s, caudal $\sigma_Q=0.002$ m³/s y presión $\sigma_p=3000$ Pa; todas se recortan a sus dominios físicos. El ruido se genera **después** de la transición física y nunca altera el estado verdadero. Las estimaciones de salud iniciales son $0.95$ y se actualizan mediante inspección o un filtro explícito documentado. **En G2.4 no se implementará un filtro bayesiano complejo**: un estimador exponencial acotado con incertidumbre escalar servirá como aproximación, cuya calibración deberá evaluarse.

El modelo completo es POMDP; la sesión 1 mostrará su **versión plenamente observable** como MDP didáctico. PPO sobre $o_t$ es una política reactiva bajo observabilidad parcial y no se describirá como solución exacta del POMDP. Se puede añadir una ventana corta de observaciones como línea base de memoria sin cambiar el DGP.

**Orden causal del paso:** observar $o_t$ generado del estado actual → elegir acción solicitada → filtrar acción → resolver hidráulica → calcular entrega e inventarios → computar costos y recompensa → evolucionar exógenas y salud → registrar transición → producir $o_{t+1}$. No se utilizará demanda futura ni salud verdadera en la política desplegada.

## 6. Acciones, objetivos y límites

Acción hidráulica continua solicitada $a_t=(u_0,u_N,u_S)\in[0.60,1.00]^3$. Para entrenamiento PPO, las acciones se parametrizan en $[-1,1]^3$ y se transforman linealmente. Las bombas indisponibles se representan mediante máscara de disponibilidad; no se permite que la red decida reactivar una bomba fallada.

**Recompensa por paso en UM**, antes de normalización para el algoritmo:

$$
r_t=-\left[C_{E,t}+w_D\,900(d_t-d_t^{\mathrm{served}})
+w_U\sum_k |u_{k,t}-u_{k,t-1}|
+w_I C_{I,t}\right].
$$

Se fijan valores **iniciales para pruebas**, no optimizados: $w_D=4$ UM/m³ de déficit, $w_U=0.5$ UM por unidad de cambio absoluto y $w_I=1$ para costo de inspección ya expresado en UM. Los pesos deberán pasar una auditoría de escalas: se reportarán costos **por separado** y se verificará que ningún método obtenga buen retorno ocultando déficit o violaciones. La terminación por falta de acción segura tiene costo terminal adicional de 200 UM, registrado por separado.

**Restricciones duras:** balances hidráulicos, $V_i\in[200,1500]$, $q_e\ge0$, $p_i\in[0,600]$ kPa para nodos internos, velocidad por arista $\le3$ m/s, disponibilidad, batería no negativa y rutas válidas. **Restricciones blandas:** energía, déficit, cambios de actuadores, distancia y tiempo de inspección. Se reportarán tasas de intervención y terminación; las intervenciones no se ocultarán dentro de la recompensa.

Para comparación, se fija horizonte de retorno de 96 pasos y $\gamma=0.99$ para RL; las **métricas físicas y monetarias** se acumulan **sin descuento** para no favorecer métodos por convención de aprendizaje.

## 7. Tres controladores y condiciones de comparación

### 7.1. Política por reglas (línea base obligatoria)

Reglas con tres consignas: nominal $(0.8,0.8,0.8)$; ahorro $(0.72,0.72,0.72)$; alta transferencia $(0.92,0.90,0.90)$. Se seleccionan según inventario de destino, demanda observada y tarifa, con umbrales iniciales $V_4^{\mathrm{low}}=400$ m³ y $V_4^{\mathrm{high}}=800$ m³. Una lógica determinista de histéresis evita cambios repetidos. El filtro de seguridad se aplica de forma idéntica a todos los métodos. Los umbrales finales se seleccionan en **validación**, nunca en prueba.

### 7.2. PPO (obligatorio)

Entorno Gymnasium con `reset(seed, options)` y `step(action)`, `Box(3)` y observación vectorial documentada. Política MLP pequeña (dos capas de 64 unidades), `tanh`, actor–critic; entrenamiento con PPO de implementación estándar y registro de semillas, normalización, hiperparámetros, número de pasos y políticas guardadas. **Estos hiperparámetros son punto de partida, no garantía de convergencia**. La evaluación usa acciones deterministas o una regla de muestreo congelada, igual para todos los episodios.

### 7.3. MPC (referencia opcional condicionada a validación)

En cada paso resuelve un problema de horizonte corto $H=4$ con pronóstico de demanda y modelo reducido, costos y restricciones. Puede ser computacionalmente caro y no convexo; se medirá factibilidad y tiempo por decisión. **Si no supera validación, se omite de la comparación empírica** y se explica conceptualmente. No se asignará un resultado simulado de MPC sin solver operativo.

## 8. Optimización bayesiana y multiobjetivo

Se optimizará la política de reglas sobre un vector **continuo e interpretable**

$$
\theta=(u_{\mathrm{eco}},u_{\mathrm{nom}},u_{\mathrm{alta}})\in
[0.65,0.80]\times[0.75,0.90]\times[0.85,1.00],
$$

aplicado de manera común a las tres bombas (con factores fijos de rama, si se requieren, congelados antes de evaluar). El evaluador $f(\theta)$ devuelve costo medio de 8 escenarios de validación **con las mismas semillas para cada $\theta$**; si hay inviabilidad, se registra una penalización declarada y un indicador de factibilidad. Se comparan **BO con proceso gaussiano** y búsqueda aleatoria con 5 puntos iniciales compartidos y 20 evaluaciones adicionales cada uno. La adquisición será Expected Improvement para minimización, con manejo explícito de ruido si se usan semillas distintas por evaluación. Las evaluaciones finales se realizan en un conjunto independiente de prueba.

**Multiobjetivo:** cada configuración se evalúa mediante

$$
F(\theta)=\big(\mathbb E[\mathrm{UM\ energía}],
\mathbb E[\mathrm{m^3\ no\ servidos}],
\mathbb E[\mathrm{UM\ maniobras}]\big),
$$

sujeto a tasa de intervenciones y factibilidad. Se mostrará el conjunto **no dominado entre las configuraciones realmente evaluadas**; no se lo denominará frente de Pareto verdadero. Para incluir inspección, se añadirá costo de inspección como cuarto objetivo **solo en la cuarta sesión** y con comparaciones que distingan políticas de operación e inspección.

## 9. Meta-learning: tarea, algoritmo y contraste

La tarea $\tau$ es una parametrización del **mismo simulador**: $(\bar d,A_d,\mu_0,h_{N,0},h_{S,0})$. El experimento principal de meta-learning se ejecutará en un **subproblema reducido de selección de consignas** con política diferenciable pequeña y un horizonte reducido de 12 pasos, manteniendo ecuaciones y costos del simulador. Para permitir gradientes de adaptación estables, se utilizará un objetivo sustituto diferenciable validado frente a retornos simulados, o una aproximación por gradientes de política; **no se diferenciará automáticamente a través de `least_squares` como si fuera una operación diferenciable garantizada**.

Método candidato: **Reptile de primer orden** con bucle interno de adaptación por gradiente y actualización externa hacia parámetros adaptados. Deben especificarse en el código: pérdida interna, número de tareas por lote, pasos de adaptación, tamaño de paso, meta-paso, semillas y presupuesto de interacciones. **Reptile con una simple pérdida supervisada ajena al control no contará como metaaprendizaje de este laboratorio**.

Líneas base con el mismo presupuesto de muestras en la nueva tarea: (a) política fija entrenada multitarea sin adaptación, (b) fine-tuning desde inicialización multitarea ordinaria, (c) entrenamiento desde cero. Curvas a 0, 5, 10, 20 y 40 episodios de adaptación; reportar media e intervalos por tareas de metaprueba. Si no se logra un algoritmo estable, se declarará limitación y se usará una **demostración validada de optimización de inicializaciones de parámetros del controlador** como metaaprendizaje, siempre que haya tareas de entrenamiento/prueba disjuntas y optimización explícita para adaptación rápida. No se etiquetará como Reptile si no se ejecutó Reptile.

## 10. Robot discreto, investigación de operaciones e información

El grafo de acceso $G_R$ es distinto del grafo hidráulico. Se fijan ubicaciones $R=\{\mathrm{base},P0,PN,PS\}$ y aristas no dirigidas con tiempos de viaje (minutos):

| Tramo | Tiempo | Energía de batería |
|---|---:|---:|
| base–P0 | 6 | 6 |
| P0–PN | 8 | 8 |
| P0–PS | 10 | 10 |
| PN–PS | 12 | 12 |
| base–PS | 14 | 14 |

Cada inspección toma 5 min y 4 unidades de batería. Capacidad inicial 60 unidades; presupuesto de misión 45 min; se exige regreso a base. La inspección mide salud $h_k$ con error $N(0,0.02^2)$, recortado a $[0.65,1]$; no modifica físicamente $h_k$ ni repara. Su costo sintético es $0.5$ UM/min de viaje más $2$ UM por inspección, independiente del costo hidráulico.

**OR:** resolver exactamente por enumeración todas las rutas factibles que visiten cada bomba a lo sumo una vez (solo tres sitios), con presupuesto de tiempo y batería. Maximizar beneficio esperado de inspección menos costo, donde el beneficio se calcula mediante cambios en decisiones hidráulicas **posteriores**, no únicamente reducción de varianza. La inspección y la operación están acopladas por la creencia sobre salud.

**RL + OR:** OR genera ruta factible y restricciones; un controlador adaptativo (reglas o RL, si está validado) decide ejecutar o replantear tras observaciones. La contribución de RL robótico solo se afirmará si se compara con OR sin RL bajo las mismas perturbaciones. Una ruta optimizada **no equivale por sí sola a RL + OR**: para cubrir el tema institucional se presentará explícitamente el papel de decisiones secuenciales aprendidas en la coordinación hidráulica y de OR en rutas, con evidencia del acoplamiento.

**Limitación deliberada:** la duración de viajes es un múltiplo fraccional del paso hidráulico de 15 min. El módulo de misión opera en tiempo de minutos y entrega eventos de observación al siguiente límite de control de 15 min; la espera se registra. No se simulará un robot continuo ni un sistema de eventos físicos de alta fidelidad.

## 11. Partición experimental, métricas y análisis estadístico

### 11.1. Particiones

- **Entrenamiento:** 200 tareas paramétricas generadas con semilla maestra 20261018; para cada tarea, semillas de trayectorias independientes.
- **Validación:** 40 tareas nuevas, semilla maestra 20261019.
- **Prueba IID:** 80 tareas nuevas de la misma familia, semilla maestra 20261020.
- **Prueba OOD:** 40 tareas con $\bar d\in[0.13,0.15]$ y $\mu_0\in[0.04,0.06]$ Pa·s, semilla maestra 20261021; la extrapolación se declara explícitamente.
- **Meta-test:** las 80 tareas IID de prueba y 40 OOD, sin participación en adaptación de hiperparámetros ni selección de políticas.

Los números anteriores fijan **tamaños objetivo**, no evidencia de que ya existan esos archivos. Los conjuntos se materializarán en manifiestos inmutables con hash. **Evitar fuga:** ninguna tarea de prueba se utilizará para seleccionar reglas, hiperparámetros, normalizadores ni BO; el metaentrenamiento emplea únicamente entrenamiento y validación.

### 11.2. Métricas primarias y secundarias

**Primarias:** costo total no descontado (UM/episodio), fracción de demanda servida, energía específica (kWh/m³ entregado). **Seguridad:** intervenciones por episodio, terminaciones de contingencia, violaciones de presión/inventario y fallos numéricos; deben reportarse aunque el retorno sea alto. **Secundarias:** cambios de consignas, variabilidad, tiempo por decisión, costo de entrenamiento, tiempo de inspección y costo neto de información. **BO:** mejor valor encontrado contra evaluaciones y presupuesto total. **Meta-learning:** rendimiento contra episodios de adaptación en tareas no vistas. **Multiobjetivo:** dominancia, tamaño de conjunto no dominado y dispersión.

### 11.3. Comparaciones y incertidumbre

Se usan **escenarios pareados**: para cada tarea y trayectoria se reutilizan exactamente las perturbaciones exógenas y estados iniciales entre métodos; los efectos de acciones sobre salud se calculan por método. Se guardan todas las trayectorias. Para una diferencia de costo por episodio $\Delta_i=C_{A,i}-C_{B,i}$ se informa $\bar\Delta$ e intervalo de confianza por **bootstrap pareado estratificado por tarea**; los episodios de una misma tarea no se tratarán como observaciones independientes. Se documentan número de tareas, semillas de entrenamiento y variabilidad entre entrenamientos. No se declarará superioridad universal por una comparación aislada.

**Análisis de fallos:** escenarios donde PPO pierde, BO no mejora, meta-learning transfiere negativamente, la inspección no compensa y la hidráulica es inviable. Son resultados científicamente válidos, no fallas editoriales.

## 12. Interfaces y estructura de software

```text
hydro_lab_g2/
├── pyproject.toml
├── configs/
│   ├── network_g24.yaml
│   ├── dgp_g24.yaml
│   ├── safety_g24.yaml
│   └── experiments_g24.yaml
├── src/hydro_lab/
│   ├── types.py            # dataclasses y unidades
│   ├── hydraulics.py       # ecuaciones y solver
│   ├── inventory.py        # balances conservativos
│   ├── scenarios.py        # DGP y manifiestos
│   ├── observations.py     # sensores y estimación
│   ├── safety.py           # validación y respaldo
│   ├── environment.py      # API Gymnasium
│   ├── controllers.py      # reglas y MPC opcional
│   ├── robot_or.py         # grafo, rutas y tiempos
│   ├── objectives.py       # costos, Pareto y BO
│   └── evaluation.py       # evaluación pareada
├── experiments/
│   ├── s1_mdp.py
│   ├── s2_ppo.py
│   ├── s3_bo_pareto.py
│   └── s4_meta_or.py
├── tests/
│   ├── test_incidence.py
│   ├── test_hydraulics.py
│   ├── test_inventory.py
│   ├── test_safety.py
│   ├── test_reproducibility.py
│   └── test_robot_or.py
├── results/                # salidas versionadas y hashes
└── notebooks/              # demostraciones docentes ligeras
```

**Contrato del solver:**

```python
solve_hydraulics(
    V0: float, V4: float, viscosity: float,
    health: tuple[float, float, float],
    availability: tuple[bool, bool, bool],
    u: tuple[float, float, float]
) -> HydraulicResult
# status, q_edges, heads, pressures, powers,
# residual_max, constraint_violations, diagnostics
```

**Contrato del entorno:**

```python
obs, info = env.reset(seed=..., options={"scenario_id": ...})
obs_next, reward, terminated, truncated, info = env.step(action)
# info incluye costos desagregados, verdad física solo para evaluación,
# acción solicitada/ejecutada, seguridad, solver y semilla/escenario.
```

El simulador es independiente de PPO, BO y OR. Las evaluaciones comparten un archivo de escenarios, el mismo filtro de seguridad y un formato común de resultados. Las dependencias objetivo son Python 3.11+, NumPy, SciPy, Gymnasium, Matplotlib, pandas y una biblioteca PPO abierta y estable; BO y OR utilizarán bibliotecas ligeras o enumeración exacta según presupuesto. La compatibilidad CPU se verificará antes de fijar versiones.

## 13. Orden de construcción

1. **Motor físico puro:** hidráulica, balances de inventario, energía y restricciones.
2. **Pruebas unitarias y casos analíticos:** conservación, signos, soluciones simétricas, ramas cerradas.
3. **DGP y escenarios inmutables:** semillas, tareas, observaciones y fallas.
4. **Política por reglas y trazas:** un episodio completo de 96 pasos con diagnóstico.
5. **Entorno Gymnasium y PPO:** entrenamiento y evaluación pareada.
6. **BO y Pareto:** evaluador compartido y presupuesto idéntico.
7. **Meta-learning reducido:** adaptación y comparaciones genuinas.
8. **Robot + OR:** rutas, inspecciones, creencias y coordinación.
9. **Visualizaciones y materiales:** únicamente figuras que apoyen las cuatro sesiones.

Se preservará cada resultado por generación; no se sobrescribirán políticas o escenarios con nuevos experimentos sin cambiar versión o hash.

## 14. Pruebas de aceptación antes de entrenar

| ID | Prueba | Criterio |
|---|---|---|
| T01 | Matriz de incidencia y flujo | $Bq=(-Q,0,0,0,Q)^\top$ hasta $10^{-9}$ m³/s |
| T02 | Balance de energía | Residuos $\le10^{-6}$ m en nominal |
| T03 | Reconstrucción por ambas ramas | Dos estimaciones de $\mathcal H_4$ difieren $\le10^{-6}$ m |
| T04 | Presiones y velocidad | Ninguna violación aceptada como `FEASIBLE` |
| T05 | Inventario en un paso | Error de balance $\le10^{-9}$ m³ |
| T06 | Conservación global | Cambio $V_0+V_4$ igual a $900(s-d^{\mathrm{served}})$ dentro de $10^{-8}$ m³ |
| T07 | No negatividad | Caudales, volúmenes y potencia físicamente válidos |
| T08 | Fallo de bomba P0 | Parada segura explícita, no caudal inventado |
| T09 | Rama cerrada | Solver unidimensional coherente y sin flujo por rama inactiva |
| T10 | Semilla | Misma configuración y semilla → trayectorias idénticas |
| T11 | Separación de tareas | Intersecciones train/val/test vacías por identificador y parámetros generados |
| T12 | Seguridad | Acción imposible registrada, corregida o terminada; nunca ocultada |
| T13 | Robot | Rutas factibles respetan 45 min, 60 unidades y regreso |
| T14 | Observación | La política no accede a salud verdadera ni demanda futura |
| T15 | Horizonte | Episodios completos o terminaciones con causa y costo |
| T16 | Baseline | Política por reglas produce trazas y costos reproducibles |
| T17 | Robustez solver | Casos frontera y perturbaciones sin NaN; fallos clasificados |
| T18 | Sensibilidad temporal | Comparación de resultados agregados con $\Delta t=5,15,30$ min; diferencias justificadas |
| T19 | Plausibilidad hidráulica | Contraste independiente con Darcy–Weisbach; discrepancias documentadas y decisión de aceptar/recalibrar |
| T20 | Perfil CPU | Tiempo por paso y episodio medido en el equipo de desarrollo; ruta de respaldo preparada |

**Puerta de avance:** T01–T17 deben aprobarse antes de entrenamiento. T18–T20 deben completarse antes de cerrar material docente y formular afirmaciones sobre plausibilidad y viabilidad de demostración. Una falla de T19 puede requerir cambiar parámetros y crear G2.5; no se alterarán silenciosamente los resultados G2.4.

## 15. Riesgos técnicos y decisiones congeladas

**R1 — Inconsistencia física:** los parámetros fenomenológicos pueden no aproximar Darcy–Weisbach en el rango de operación. Mitigación: T19, reporte y eventual recalibración versionada.

**R2 — Falta de factibilidad:** inventarios, bombas y demanda pueden producir contingencias frecuentes. Mitigación: mapas de factibilidad y ensayos Monte Carlo **antes** de PPO; no modificar distribuciones después de ver el desempeño de un método.

**R3 — Seguridad de RL:** acciones proyectadas cambian el proceso de decisión. Mitigación: registrar acción efectiva, exponer frecuencia de intervenciones y, si es necesario, entrenar directamente sobre un espacio de consignas seguras.

**R4 — Meta-learning no converge:** no confundir fine-tuning con metaaprendizaje. Mitigación: subproblema reducido y líneas base; reportar resultado negativo si corresponde.

**R5 — Robot consume tiempo docente:** OR exacto con tres sitios y robot discreto; no SLAM ni visión.

**R6 — Exceso de componentes:** cuatro sesiones de 110 minutos; ninguna nueva familia algorítmica fuera de los ocho temas institucionales. MPC es opcional.

**R7 — Unidades de energía y potencia:** verificar conversión W→kWh y UM; nunca confundir potencia instantánea con energía por periodo.

**R8 — Fuga de información:** políticas y optimizadores no acceden a estado latente ni a tareas de prueba; observaciones de inspección solo disponibles después del evento.

## 16. Matriz de trazabilidad académica

| Sesión | Tema obligatorio | Componentes matemáticos y artefactos |
|---|---|---|
| 1, 27 oct. | MDP avanzados | $S,A,P,R,\gamma$, estado y observación, Bellman, restricciones |
| 1, 27 oct. | RL y decisiones secuenciales | Trayectorias, costo diferido, política por reglas |
| 2, 27 oct. | Deep RL | Entorno Gymnasium, aproximación MLP, PPO y líneas base |
| 2, 27 oct. | Policy gradients | Log-derivative, ventaja, actor–critic, objetivo PPO |
| 3, 28 oct. | Bayesian Optimization | GP, Expected Improvement, evaluación costosa, búsqueda aleatoria |
| 3, 28 oct. | Optimización multiobjetivo | Dominancia, costos separados, conjunto no dominado |
| 4, 28 oct. | Meta-learning | Distribución de tareas, adaptación rápida y baselines |
| 4, 28 oct. | RL + Investigación de Operaciones | Rutas OR factibles y política secuencial de operación/inspección |

Cada día contiene **110 min + 20 min de pausa + 110 min**, sin añadir temas de gemelos digitales, GNN ni dashboards.

## 17. Referencias metodológicas de trabajo

- Sutton, R. S., y Barto, A. G. (2018). *Reinforcement Learning: An Introduction*, 2.ª ed.
- Puterman, M. L. (1994). *Markov Decision Processes*.
- Schulman, J. et al. (2017). *Proximal Policy Optimization Algorithms*.
- Rasmussen, C. E., y Williams, C. K. I. (2006). *Gaussian Processes for Machine Learning*.
- Snoek, J. et al. (2012). *Practical Bayesian Optimization of Machine Learning Algorithms*.
- Deb, K. et al. (2002). *A Fast and Elitist Multiobjective Genetic Algorithm: NSGA-II*.
- Finn, C. et al. (2017). *Model-Agnostic Meta-Learning for Fast Adaptation of Deep Networks*.
- Nichol, A. et al. (2018). *On First-Order Meta-Learning Algorithms*.
- Bertsimas, D., y Tsitsiklis, J. N. (1997). *Introduction to Linear Optimization*.
- White, F. M. *Fluid Mechanics*, ediciones de referencia; Darcy–Weisbach y análisis dimensional.

---

**Resultado de G2.4:** queda fijado un contrato matemático y computacional implementable. Los valores son candidatos sintéticos congelados para la **primera implementación**, no parámetros calibrados. La siguiente actividad es programar y ejecutar T01–T20, documentar desviaciones y, si se requieren correcciones sustanciales, emitir G2.5 sin sobrescribir esta generación.
