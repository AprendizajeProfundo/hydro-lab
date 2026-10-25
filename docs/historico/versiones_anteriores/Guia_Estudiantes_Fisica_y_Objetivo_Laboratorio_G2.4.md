# Una red de hidrocarburos que aprende a decidir
## Guía introductoria de física, matemáticas y propósito del laboratorio — G2.4

**Curso:** Inteligencia artificial avanzada aplicada a retos estratégicos  
**Universidad de los Andes · Ecopetrol**  
**Fechas:** 27 y 28 de octubre de 2026  
**Tipo de documento:** lectura preparatoria y material de consulta para estudiantes  
**Nivel:** introductorio en hidráulica; se presuponen conocimientos básicos de álgebra, funciones y probabilidad, pero **no** formación en ingeniería de petróleos.  
**Versión:** G2.4 — guía pedagógica complementaria. No sustituye la especificación técnica G2.4.

> **Idea central.** Nuestro propósito no es formar especialistas en oleoductos en ocho horas. Construiremos un mundo físico sintético, lo suficientemente comprensible para preguntarnos cómo una inteligencia artificial aprende a tomar decisiones secuenciales, cómo se optimizan configuraciones costosas de evaluar y cómo se coordinan algoritmos de aprendizaje con investigación de operaciones.

---

## 1. La historia que estudiaremos

Imagina una instalación que recibe un líquido semejante a un hidrocarburo en un tanque, lo impulsa por tuberías, lo divide entre dos rutas y vuelve a reunirlo en un tanque de destino. En el camino hay bombas que consumen electricidad. La demanda cambia durante el día; la electricidad no cuesta lo mismo a todas horas; las bombas pueden deteriorarse; los instrumentos de medición cometen errores.

Un operador debe decidir **a qué velocidad hacer funcionar las bombas**, cuándo ahorrar energía, cuándo aumentar el transporte y cómo reaccionar si cambia la demanda o una bomba se encuentra en mal estado. También cuenta con un **robot de inspección** que puede visitar equipos y obtener información adicional, aunque desplazarse e inspeccionar cuesta tiempo y dinero.

Ninguna decisión es aislada. Ahorrar energía ahora puede dejar el tanque receptor demasiado vacío para atender una demanda futura. Bombear mucho ahora puede elevar costos o forzar los límites operativos. Inspeccionar una bomba puede ser útil si lo aprendido cambia las decisiones posteriores; si no cambia nada, quizá fue un gasto innecesario.

Ese es el problema científico: **decidir hoy teniendo en cuenta sus consecuencias mañana, bajo incertidumbre y restricciones**.

### Qué es realista y qué no

La instalación es **enteramente ficticia**: no corresponde a un activo, un plano, un dato operacional ni una calibración de Ecopetrol. Las ecuaciones recogen principios físicos reconocibles, pero simplifican muchos fenómenos. No modelaremos transporte multifásico, ondas de presión, golpes de ariete, cavitación detallada, temperatura espacial, corrosión real, control industrial certificado ni navegación robótica continua.

En particular, el simulador se considera **cuasiestacionario en hidráulica**: dentro de cada intervalo calcula un equilibrio aproximado de caudales y presiones; entre intervalos sí cambian los inventarios, la demanda, la viscosidad y la condición de los equipos. Esto **no** equivale a resolver toda la dinámica transitoria del fluido.

## 2. Conozcamos nuestra instalación

Usaremos cinco **nodos**, numerados del 0 al 4, y cinco **aristas** o tramos de tubería:

```text
                         Bomba PN
                    ┌───[PN]───(2)──────┐
                    │                   │
Tanque de origen    │                   │   Tanque receptor
      (0)───[P0]───(1)                  (4)
                    │                   │
                    └───[PS]───(3)──────┘
                         Bomba PS
```

Las conexiones exactas son $(0,1)$, $(1,2)$, $(2,4)$, $(1,3)$ y $(3,4)$. La **bomba P0** impulsa el líquido desde el tanque de origen hasta la bifurcación del nodo 1. La **bomba PN** impulsa la rama norte y la **bomba PS** la rama sur. Las dos ramas se reúnen en el tanque del nodo 4.

El robot no circula por dentro de las tuberías. Recorre **caminos de acceso**, que forman otra red, y puede visitar P0, PN y PS. Esto permite distinguir la **red hidráulica**, por donde se mueve el líquido, de la **red de movilidad**, por donde se desplaza el robot.

| Elemento | Qué significa | Para qué importa |
|---|---|---|
| Nodo | Lugar donde se conectan tuberías o existe almacenamiento | Permite escribir balances y presiones |
| Arista | Tramo de tubería orientado | Por allí circula un caudal |
| Tanque | Depósito que acumula líquido | Permite atender demanda aun si el flujo cambia |
| Bomba | Equipo que añade energía al líquido | Hace posible transportar y consume electricidad |
| Válvula antirretorno | Dispositivo idealizado que impide flujo inverso | Simplifica la dirección de circulación |
| Sensor | Instrumento que observa una variable con error | La IA no ve directamente todo el estado real |
| Robot | Vehículo que visita equipos | Obtiene información, pero consume recursos |

La flecha de una arista indica nuestra **convención de sentido positivo**. No es una garantía de que todo fluido físico siempre circule así: el modelo incorpora válvulas ideales y prohíbe caudales negativos.

## 3. Las seis magnitudes que necesitamos comprender

### 3.1. Volumen: cuánto líquido hay

El **volumen**, $V$, se mide en metros cúbicos ($\mathrm{m^3}$). Un metro cúbico equivale a 1.000 litros.

En nuestro modelo hay dos inventarios principales: $V_0$, en el tanque de origen, y $V_4$, en el tanque receptor. Al comenzar un episodio nominal, contienen 750 y 500 $\mathrm{m^3}$, respectivamente. Por seguridad, cada uno debe mantenerse entre 200 y 1.500 $\mathrm{m^3}$.

### 3.2. Caudal: cuánto pasa por unidad de tiempo

El **caudal volumétrico**, $q$, se mide en $\mathrm{m^3/s}$. No es la cantidad total almacenada, sino la cantidad que atraviesa una sección de tubería **cada segundo**.

La relación básica es:

$$
\text{volumen transportado}=\text{caudal}\times\text{tiempo}.
$$

Si una tubería transporta $0.10\ \mathrm{m^3/s}$ durante 15 minutos, mueve:

$$
0.10\times(15\times60)=90\ \mathrm{m^3}.
$$

Es importante no confundir **caudal** ($\mathrm{m^3/s}$) con **velocidad del fluido** ($\mathrm{m/s}$). Se relacionan mediante $q=Av$, donde $A$ es el área transversal de la tubería.

### 3.3. Presión: cómo empuja el líquido

La **presión**, $p$, expresa fuerza por unidad de área. Se mide en pascales (Pa) o kilopascales (kPa); $1\ \mathrm{kPa}=1.000\ \mathrm{Pa}$.

Una bomba eleva la energía del líquido y, según las condiciones, puede aumentar la presión disponible para vencer desniveles y fricción. La presión no es lo mismo que el caudal: puede haber presión elevada con poco caudal, y un caudal considerable con presiones diferentes a lo largo del sistema.

### 3.4. Densidad: cuánta masa ocupa un volumen

La **densidad**, $\rho$, es masa dividida entre volumen. Su unidad es $\mathrm{kg/m^3}$. Usaremos un valor sintético nominal de $850\ \mathrm{kg/m^3}$.

La densidad importa para relacionar presión, altura hidráulica y potencia de bombeo.

### 3.5. Viscosidad: resistencia interna al movimiento

La **viscosidad dinámica**, $\mu$, mide, de forma simplificada, la resistencia interna de un líquido a deformarse mientras fluye. Se expresa en Pa·s. En el modelo, su valor nominal es $0.020\ \mathrm{Pa\,s}$.

En general, una viscosidad mayor puede aumentar las pérdidas de energía durante el transporte. **La fórmula exacta que usaremos para representarlo es una aproximación sintética**, no una ley universal de oleoductos.

### 3.6. Energía y potencia: cuánto cuesta impulsar el líquido

La **potencia**, $P$, mide la rapidez de consumo de energía y se expresa en vatios (W) o kilovatios (kW). La **energía** consumida durante un intervalo se expresa en kilovatios-hora (kWh).

$$
\text{energía (kWh)}=\text{potencia (kW)}\times\text{duración (h)}.
$$

Si un equipo consume 20 kW durante 15 minutos, utiliza $20\times0.25=5$ kWh. Si la tarifa es 0.18 unidades monetarias por kWh, el costo será $5\times0.18=0.90$ unidades monetarias. Las tarifas del laboratorio son ficticias.

## 4. Primera ley física: la materia no aparece ni desaparece

La **conservación de masa** es nuestra primera regla. Como aproximamos el líquido como prácticamente incompresible y con densidad casi constante dentro de cada episodio, podemos escribir balances de **volumen**.

En el nodo 1, el flujo que llega desde el origen se divide en dos ramas:

$$
Q=q_N+q_S.
$$

Aquí $Q$ es el caudal total; $q_N$, el de la rama norte; y $q_S$, el de la sur. Si llegan $0.11\ \mathrm{m^3/s}$, podrían circular $0.06$ por el norte y $0.05$ por el sur. Lo que no puede ocurrir es que lleguen $0.11$ y salgan $0.15$ sin otra fuente de líquido.

El líquido no desaparece al llegar al tanque receptor. Se acumula allí o se entrega para atender demanda. Por eso necesitamos balances de inventario.

### 4.1. Balance del tanque de origen

$$
V_{0,t+1}=V_{0,t}+\Delta t(s_t-Q_t).
$$

- $V_{0,t}$: volumen disponible al comienzo del intervalo.
- $s_t$: suministro que llega desde fuera del sistema.
- $Q_t$: caudal que sale hacia las tuberías.
- $\Delta t$: duración del intervalo, 900 segundos.

**Ejemplo:** el tanque contiene 750 $\mathrm{m^3}$, recibe $0.11\ \mathrm{m^3/s}$ y envía $0.10\ \mathrm{m^3/s}$ durante 15 minutos. Su volumen aumenta en $900(0.11-0.10)=9\ \mathrm{m^3}$; termina con 759 $\mathrm{m^3}$.

### 4.2. Balance del tanque receptor

$$
V_{4,t+1}=V_{4,t}+\Delta t(Q_t-d_t^{\mathrm{served}}).
$$

La variable $d_t^{\mathrm{served}}$ representa la **demanda realmente atendida**, que puede ser inferior a la demanda solicitada $d_t$ si falta inventario.

**Ejemplo:** llegan $0.10\ \mathrm{m^3/s}$ y se entregan $0.12\ \mathrm{m^3/s}$. El tanque pierde $900(0.02)=18\ \mathrm{m^3}$ durante ese intervalo. Esto es posible si tiene reservas suficientes.

**Lección:** un tanque funciona como un amortiguador entre lo que se bombea y lo que se consume.

## 5. Segunda ley física: transportar un líquido requiere energía

### 5.1. La idea de altura hidráulica

En lugar de trabajar todo el tiempo con presión y elevación por separado, la hidráulica utiliza la **altura hidráulica** o *head*:

$$
\mathcal H=z+\frac{p}{\rho g}.
$$

- $\mathcal H$: altura hidráulica, en metros.
- $z$: altura geométrica respecto a una referencia, en metros.
- $p$: presión manométrica, en Pa.
- $\rho$: densidad, en $\mathrm{kg/m^3}$.
- $g$: aceleración de la gravedad, aproximadamente $9.81\ \mathrm{m/s^2}$.

Esta fórmula suma dos formas de energía mecánica **por unidad de peso**: la asociada a la altura y la asociada a la presión. Es una simplificación de la ecuación de energía de Bernoulli, pues no incluimos explícitamente la energía cinética en los nodos.

**Interpretación intuitiva:** un líquido puede tener energía porque está a una mayor elevación, porque está presurizado o por ambas razones. Una bomba agrega altura hidráulica; la fricción de la tubería la consume.

### 5.2. Los tanques tienen una altura que depende de su nivel

Para nuestros tanques abiertos:

$$
\mathcal H_0=z_{0,\mathrm{base}}+\frac{V_0}{A_0},
\qquad
\mathcal H_4=z_{4,\mathrm{base}}+\frac{V_4}{A_4}.
$$

El cociente $V/A$ es la altura del líquido dentro de un tanque de sección constante.

En la configuración inicial:

$$
\mathcal H_0=10+\frac{750}{250}=13\ \mathrm m,
$$

$$
\mathcal H_4=16+\frac{500}{250}=18\ \mathrm m.
$$

El tanque receptor está inicialmente **cinco metros de altura hidráulica por encima** del de origen. Por tanto, necesitamos bombas capaces de aportar energía suficiente para superar ese desnivel **y** las pérdidas de fricción.

### 5.3. La fricción se opone al movimiento

La tubería consume parte de la energía del fluido. En el simulador usaremos:

$$
h_{L,e}=R_e(\mu)\,q_e|q_e|.
$$

Aquí $h_{L,e}$ es la **pérdida de carga** en metros, $q_e$ es el caudal y $R_e$ resume la resistencia hidráulica de ese tramo. Como las válvulas ideales impiden caudal negativo, en nuestro dominio $q_e\ge0$ y la expresión equivale a $R_e q_e^2$.

**¿Por qué aparece un cuadrado?** En muchos regímenes turbulentos las pérdidas crecen aproximadamente con el cuadrado de la velocidad, y el caudal es proporcional a la velocidad para una tubería de área fija. **No es exacto para todos los fluidos y condiciones**.

Para representar la viscosidad, el simulador utiliza:

$$
R_e(\mu)=R_e^0\left(\frac{\mu}{\mu_0}\right)^{0.20}.
$$

El exponente 0.20 fue elegido como **simplificación didáctica fenomenológica**. No debe presentarse como fórmula universal de ingeniería petrolera. Antes de considerar válido el simulador, se comparará su comportamiento con una formulación hidráulica independiente.

**Ejemplo numérico:** si $R_e=900\ \mathrm{s^2/m^5}$ y $q=0.10\ \mathrm{m^3/s}$, la pérdida es $900(0.10)^2=9\ \mathrm m$. Si duplicáramos el caudal sin cambiar $R_e$, la pérdida crecería cuatro veces. Esa es una razón por la cual bombear más puede resultar costoso.

### 5.4. La bomba aporta energía

Nuestra representación simplificada de una bomba es:

$$
h_{P,k}=h_k\,[a_k u_k^2-b_k q_k^2]_+.
$$

- $h_{P,k}$: altura añadida por la bomba, en metros.
- $u_k$: consigna de velocidad relativa de la bomba.
- $q_k$: caudal que pasa por ella.
- $a_k,b_k$: parámetros sintéticos de su curva.
- $h_k$: índice de salud del equipo, entre 0.65 y 1.
- $[x]_+$: significa tomar el mayor valor entre $x$ y cero.

Cuando $u_k$ aumenta, la bomba puede aportar más altura. Cuando el caudal aumenta, la altura disponible disminuye según esta curva simplificada. Si la salud se deteriora, también se reduce la capacidad efectiva.

**Importante:** $h_k$ es un índice abstracto de condición, **no** una medición industrial estandarizada. En el caso nominal las bombas están encendidas; cuando una bomba de rama está indisponible, el prototipo cierra esa rama.

### 5.5. Balance energético de las dos rutas

La energía que agregan las bombas debe cubrir la diferencia de altura entre tanques y las pérdidas de tubería.

Para la rama norte:

$$
h_{P,0}+h_{P,N}
=
(\mathcal H_4-\mathcal H_0)
+R_{01}Q^2+(R_{12}+R_{24})q_N^2.
$$

Para la rama sur:

$$
h_{P,0}+h_{P,S}
=
(\mathcal H_4-\mathcal H_0)
+R_{01}Q^2+(R_{13}+R_{34})q_S^2.
$$

Estas ecuaciones son la esencia física del laboratorio. Las bombas deben vencer el desnivel y las pérdidas. Como ambas ramas llegan al mismo tanque, **no podemos escoger arbitrariamente sus caudales**: los caudales resultan de resolver simultáneamente estas ecuaciones y la conservación de volumen $Q=q_N+q_S$.

Una bomba puede consumir más electricidad y, sin embargo, no aumentar proporcionalmente el transporte. La relación entre decisión y resultado es **no lineal**.

## 6. ¿Cuánta electricidad consume una bomba?

La potencia hidráulica ideal es proporcional al caudal, a la altura añadida y a la densidad:

$$
P_{\mathrm{hid}}=\rho g q h_P.
$$

Pero una bomba no es perfectamente eficiente. Su potencia eléctrica aproximada en nuestro modelo es:

$$
P_k=\frac{\rho g q_k h_{P,k}}{\eta_k},
$$

donde $\eta_k$ es la **eficiencia**: una fracción entre 0 y 1. Si $\eta_k=0.75$, la bomba necesita más potencia de entrada que la potencia útil entregada al fluido.

Para los 15 minutos del intervalo:

$$
E_t=\frac{900}{3.6\times10^6}\sum_k P_{k,t}
\quad\text{(kWh, con $P$ en W)}.
$$

Y el costo eléctrico es:

$$
C_{E,t}=c_tE_t.
$$

Aquí $c_t$ es la tarifa sintética de electricidad. **El mismo consumo puede costar distinto según la hora.** Por ello, el problema no consiste simplemente en bombear lo máximo posible.

## 7. El tiempo cambia el problema: de física a decisiones secuenciales

El simulador avanza en pasos de **15 minutos**. Un episodio tiene 96 pasos, es decir, **24 horas**.

En cada paso sucede, conceptualmente, lo siguiente:

1. El sistema se encuentra en cierto estado: volúmenes, salud de bombas, viscosidad, demanda y tarifa.
2. Los sensores producen observaciones, con errores.
3. El controlador decide consignas para las bombas.
4. Un filtro de seguridad verifica la acción; puede modificarla o rechazarla.
5. El solucionador hidráulico calcula caudales, presiones y consumo.
6. Se actualizan inventarios y costos; evolucionan demanda, viscosidad y salud.
7. El proceso se repite.

**Diferencia crucial:** las ecuaciones hidráulicas calculan qué ocurre **si tomamos una decisión**. La inteligencia artificial busca decidir **qué conviene hacer**, considerando las consecuencias futuras.

### ¿Qué significa que una decisión sea buena?

No existe una sola respuesta. Queremos simultáneamente:

- Atender la demanda.
- Evitar inventarios demasiado bajos o demasiado altos.
- Consumir menos electricidad.
- Evitar maniobras excesivas y riesgos operativos.
- Mantener capacidad de respuesta ante cambios y fallas.

Algunos objetivos compiten entre sí. La mejor decisión depende de las prioridades, del horizonte y de las restricciones.

## 8. ¿Qué sabe realmente el controlador?

El simulador conoce su **estado verdadero**: inventarios exactos, viscosidad, salud real de las bombas, demanda y demás variables. En la práctica, un controlador no observa todo perfectamente.

Los sensores pueden informar niveles, presiones, caudales y demanda con ruido. La salud de una bomba es especialmente difícil de conocer sin inspección.

Debemos distinguir:

| Concepto | Pregunta | Ejemplo |
|---|---|---|
| Estado real | ¿Cómo está realmente el sistema? | La bomba PN tiene salud 0.79 |
| Observación | ¿Qué datos recibió el agente? | Presión medida con error |
| Estimación o creencia | ¿Qué supone el agente acerca de lo que no ve? | PN probablemente está deteriorada |
| Acción | ¿Qué puede cambiar el agente? | Aumentar la consigna de P0 |
| Consecuencia | ¿Qué ocurrió después? | Mayor flujo, mayor costo y cambio de inventario |

Esta distinción explica por qué la **incertidumbre** no es un detalle accesorio. El agente puede tomar decisiones razonables con información incompleta y aun así equivocarse.

En una versión didáctica mostraremos un **MDP** (proceso de decisión de Markov), que presupone un estado suficientemente informativo. El problema con observaciones parciales es más cercano a un **POMDP**. No hace falta dominar esas siglas antes del curso; basta comprender que **ver el mundo** y **conocer el mundo** no son equivalentes.

## 9. ¿Qué hace el robot?

El robot tiene una tarea concreta: **visitar bombas para obtener mediciones adicionales de su condición**.

En el laboratorio, el robot:

- Parte de una base.
- Se mueve por una red de caminos, distinta de las tuberías.
- Consume tiempo y batería.
- Puede inspeccionar P0, PN y PS.
- Regresa a la base dentro de su presupuesto operativo.

Cada inspección toma cinco minutos y consume recursos. El robot no repara bombas y no mide mágicamente su salud sin error. Una inspección produce una **observación adicional**, que puede cambiar la estimación del controlador.

### Ejemplo: información que vale dinero

Imagina que la bomba PN parece deteriorada. Hay dos opciones:

**Sin inspección:** el controlador debe decidir con incertidumbre. Quizá reduzca el uso de la rama norte por precaución.

**Con inspección:** el robot visita PN, mide su condición y actualiza la estimación. Si PN está sana, tal vez convenga utilizarla más; si está deteriorada, quizá convenga favorecer la rama sur.

La inspección **tiene valor** solo si su información mejora decisiones futuras lo suficiente como para compensar su costo. No debemos confundir **obtener más datos** con **tomar mejores decisiones**.

### ¿Por qué aparece investigación de operaciones?

El robot debe elegir una **ruta factible**: no puede teletransportarse, gastar batería inexistente ni exceder el tiempo disponible. La investigación de operaciones (OR) proporciona métodos para optimizar rutas, asignaciones y recursos sujetos a restricciones.

El aprendizaje por refuerzo puede aportar decisiones adaptativas a medida que aparecen observaciones nuevas. **OR y RL no compiten necesariamente: pueden colaborar.**

## 10. Las cuatro sesiones: una sola historia, ocho ideas

| Jornada | Sesión | Pregunta que aprenderemos a responder | Método |
|---|---|---|---|
| 27 de octubre | 1 | ¿Cómo representar decisiones que afectan el futuro? | MDP avanzados y RL secuencial |
| 27 de octubre | 2 | ¿Puede una red neuronal aprender una política de bombeo? | Deep RL y policy gradients (PPO) |
| 28 de octubre | 3 | ¿Cómo buscar buenas configuraciones con pocas evaluaciones y varios objetivos? | Bayesian Optimization y optimización multiobjetivo |
| 28 de octubre | 4 | ¿Cómo adaptarse rápidamente a nuevas condiciones y coordinar inspecciones? | Meta-learning y RL + OR |

Cada sesión dura **110 minutos**. Entre las dos sesiones de cada jornada habrá **20 minutos de pausa**. Total: ocho horas presenciales.

### 10.1. MDP y aprendizaje por refuerzo

Un **MDP** organiza el problema en estado, acción, transición, recompensa y política. La **política** es una regla que decide qué acción tomar en cada situación.

Una política por reglas podría decir: *si el tanque receptor está bajo y la demanda es alta, aumenta el bombeo*. El aprendizaje por refuerzo busca aprender una política a partir de consecuencias acumuladas, no solo de reglas escritas manualmente.

Una recompensa didáctica puede representarse como:

$$
r_t=-\left(
\text{costo eléctrico}
+\text{penalización por demanda no servida}
+\text{costo de maniobras}
+\text{costo de inspección}
\right).
$$

La recompensa es un instrumento de entrenamiento; **no sustituye las restricciones de seguridad**. Una acción físicamente imposible no se vuelve aceptable porque el agente espere una recompensa alta.

### 10.2. Deep RL y PPO

Cuando hay muchos estados posibles, no podemos almacenar una tabla con la mejor acción para cada uno. **Deep RL** utiliza redes neuronales para representar políticas o valores.

**Policy gradients** significa ajustar los parámetros de una política en la dirección que mejora su desempeño esperado. **PPO** (*Proximal Policy Optimization*) es una familia de algoritmos que busca realizar esas actualizaciones de manera controlada.

En clase no entrenaremos un modelo grande desde cero. Compararemos políticas preparadas previamente y examinaremos curvas, costos, servicio y fallos. Una curva de recompensa creciente **no prueba por sí sola** que el controlador sea seguro o generalice bien.

### 10.3. Optimización bayesiana

Supongamos que queremos elegir tres consignas de bombeo para una política por reglas: modo económico, normal y alta transferencia. Evaluar cada configuración requiere simular episodios completos, lo que tiene un costo computacional.

**Bayesian Optimization (BO)** construye un modelo estadístico de cómo cambia el resultado según los parámetros. Ese modelo no solo predice resultados: también representa **incertidumbre**. Con ella decide dónde conviene evaluar a continuación.

La pregunta es: *con un presupuesto pequeño de pruebas, ¿cómo encontramos una configuración prometedora?* Compararemos BO con búsqueda aleatoria usando el **mismo número de evaluaciones**.

### 10.4. Optimización multiobjetivo

Una configuración puede gastar poca energía pero dejar demanda sin atender. Otra puede servir casi toda la demanda, pero a un costo alto.

En lugar de ocultar esa tensión dentro de un único número, analizaremos varios objetivos. Una solución **domina** a otra si no es peor en ninguno de los objetivos y es estrictamente mejor en al menos uno.

El conjunto de soluciones evaluadas que no son dominadas por otras es nuestro **conjunto no dominado**. No lo llamaremos el frente de Pareto verdadero, porque no habremos explorado todas las posibilidades.

### 10.5. Meta-learning

La red puede operar bajo condiciones diferentes: más demanda, mayor viscosidad o equipos más deteriorados.

El **meta-learning** busca aprender algo que facilite **adaptarse rápidamente a tareas nuevas**. No basta con tomar una política y ajustarla: debemos demostrar, frente a alternativas justas, que la inicialización o estrategia aprendida mejora la adaptación con pocos datos.

Separaremos tareas de entrenamiento y prueba, y mediremos desempeño **antes y después** de recibir nuevas experiencias.

### 10.6. RL + investigación de operaciones

La investigación de operaciones puede encontrar rutas factibles para el robot y resolver restricciones combinatorias. El aprendizaje por refuerzo puede aprender decisiones secuenciales sobre operación o coordinación bajo incertidumbre.

El objetivo de esta última sesión es comprender **qué parte conviene aprender y qué parte conviene optimizar explícitamente**.

## 11. Un ejemplo completo, sin algoritmos todavía

Supongamos que a las 08:00 del episodio:

- El tanque de origen tiene 750 $\mathrm{m^3}$.
- El tanque receptor tiene 500 $\mathrm{m^3}$.
- La demanda solicitada es $0.12\ \mathrm{m^3/s}$.
- El suministro externo al origen es $0.11\ \mathrm{m^3/s}$.
- Las bombas operan a consignas nominales.
- Una medición sugiere que PN podría estar deteriorada.

El controlador considera dos opciones: aumentar el bombeo o mantenerlo. Para evaluarlas, el simulador debe resolver **simultáneamente** el flujo de ambas ramas y comprobar presiones, velocidad, potencia y disponibilidad.

**Como ilustración aritmética, no como resultado validado del solucionador**, supongamos que una opción factible produjera $Q=0.10\ \mathrm{m^3/s}$ durante 15 minutos y que la demanda completa pudiera atenderse. Entonces:

$$
V_{0,t+1}=750+900(0.11-0.10)=759\ \mathrm{m^3},
$$

$$
V_{4,t+1}=500+900(0.10-0.12)=482\ \mathrm{m^3}.
$$

La demanda se atendió, pero el tanque receptor perdió 18 $\mathrm{m^3}$. Si se repitiera muchas veces esa decisión sin compensarla, terminaríamos cerca del límite inferior. El problema es **temporal**.

Ahora imagina que el robot confirma que PN está sana. Esa información podría cambiar la distribución de flujo entre ramas y, con ello, las consignas futuras. Pero solo sería conveniente inspeccionar si el beneficio esperado supera el costo.

Este pequeño ejemplo reúne las ideas centrales: física, incertidumbre, decisiones secuenciales, información, optimización y restricciones.

## 12. ¿Qué resultados veremos y cómo interpretarlos?

Los resultados científicos del laboratorio no serán únicamente un número de recompensa. Observaremos:

| Indicador | Interpretación |
|---|---|
| Demanda servida (%) | Qué proporción de la demanda solicitada fue atendida |
| Costo total (UM) | Cuánto costó operar bajo las convenciones del experimento |
| Energía (kWh) | Cuánta electricidad consumieron las bombas |
| Energía específica (kWh/m³) | Cuánta energía se necesitó por volumen entregado |
| Intervenciones de seguridad | Cuántas acciones propuestas fueron corregidas o rechazadas |
| Fallos o terminaciones | Cuándo una operación no pudo continuar de forma factible |
| Costo y utilidad de inspección | Si obtener información adicional produjo valor neto |
| Desempeño ante escenarios nuevos | Si la política generaliza o se deteriora fuera de entrenamiento |
| Velocidad de adaptación | Cuántas experiencias necesita un método para ajustarse |

**Comparación justa:** dos algoritmos deben evaluarse bajo las mismas condiciones iniciales, perturbaciones comparables y criterios de seguridad. Reportaremos también escenarios donde un método **no** mejora al otro. En ciencia, un resultado negativo puede ser muy informativo.

## 13. Glosario para consultar durante el curso

| Término | Explicación sencilla |
|---|---|
| Hidráulica | Estudio del comportamiento y movimiento de líquidos |
| Oleoducto | Sistema de tuberías para transportar petróleo; aquí usamos una versión sintética |
| Nodo | Punto de conexión o almacenamiento de la red |
| Arista | Tramo de tubería entre nodos |
| Caudal | Volumen que circula por unidad de tiempo |
| Presión manométrica | Presión medida respecto a la atmosférica |
| Altura hidráulica | Forma de expresar energía mecánica por unidad de peso en metros |
| Pérdida de carga | Energía que se disipa durante el transporte |
| Bomba | Equipo que añade energía al líquido |
| Eficiencia | Proporción de energía de entrada convertida en energía hidráulica útil |
| Viscosidad | Medida de resistencia interna del fluido al movimiento |
| Inventario | Volumen almacenado en un tanque |
| Consigna | Valor que el controlador solicita a un actuador |
| Estado | Variables que describen la situación del sistema |
| Observación | Información disponible para decidir, potencialmente incompleta o ruidosa |
| Política | Regla o función que selecciona acciones |
| Recompensa | Señal numérica utilizada para aprender decisiones |
| Episodio | Secuencia completa de pasos simulados |
| Restricción dura | Condición que no debe violarse |
| Línea base | Método de referencia contra el que comparamos uno nuevo |
| PPO | Algoritmo de aprendizaje por refuerzo con actualizaciones controladas de política |
| Optimización bayesiana | Búsqueda que usa un modelo probabilístico de resultados e incertidumbre |
| Dominancia de Pareto | Comparación de alternativas con varios objetivos |
| Meta-learning | Aprender mecanismos o inicializaciones que faciliten adaptarse a nuevas tareas |
| Investigación de operaciones | Métodos matemáticos para asignar recursos, planear rutas y optimizar decisiones |
| DGP | Proceso generador de datos sintéticos del experimento |
| Semilla aleatoria | Valor que permite reproducir una secuencia pseudoaleatoria |
| Escenario fuera de distribución | Condición distinta de las usadas habitualmente durante entrenamiento |

## 14. Cinco preguntas para llegar preparado

1. Si la demanda aumenta durante una hora, ¿es siempre conveniente aumentar inmediatamente la velocidad de las bombas? ¿Qué información adicional necesitarías?
2. ¿Por qué la conservación de masa impide que el flujo que sale de una bifurcación sea mayor que el que entra, salvo que exista otra fuente?
3. ¿Por qué puede ser más barato transportar cierta cantidad durante un periodo de tarifa baja y utilizar luego el inventario del tanque receptor?
4. Si un sensor reporta una presión anormal, ¿cómo distinguirías un cambio físico de un error de medición?
5. ¿En qué situación sería mejor inspeccionar una bomba y en cuál sería mejor no hacerlo?

No se espera una respuesta matemática perfecta. El objetivo es empezar a **pensar como diseñador de decisiones**.

## 15. Qué conviene recordar

**La física determina qué puede ocurrir. Las restricciones determinan qué está permitido. Los datos muestran una parte imperfecta de lo que ocurre. Los algoritmos ayudan a elegir qué hacer. Y la evaluación científica nos permite saber si realmente aprendimos algo útil.**

Nuestro laboratorio no intenta demostrar que el aprendizaje por refuerzo sea siempre superior a las reglas, que la optimización bayesiana siempre venza a la búsqueda aleatoria o que inspeccionar siempre genere valor. Intenta enseñar **cuándo, por qué y bajo qué evidencia** una técnica es adecuada.

---

## Nota de alcance y fuentes

Esta guía es una **explicación pedagógica derivada de la especificación matemática y computacional G2.4** y del syllabus G2.3 aprobados para el curso. Las definiciones introductorias de presión, caudal, balances y energía corresponden a principios físicos generales; los valores, topología, curvas de bomba, dependencia de viscosidad, tarifas, salud e inspección son **decisiones sintéticas específicas del laboratorio**, no parámetros operacionales de Ecopetrol.

**Documentos relacionados:** `Red_Hidrocarburos_Especificacion_Matematica_Computacional_G2.4.md`; `Laboratorio_Red_Inteligente_Hidrocarburos_Diseno_Cientifico_G2.3.md`; `Syllabus_IA_Avanzada_Ecopetrol_Uniandes_G2.3.md`.

**Lecturas opcionales:** Sutton y Barto, *Reinforcement Learning: An Introduction* (2018); White, *Fluid Mechanics* (principios de hidráulica); Rasmussen y Williams, *Gaussian Processes for Machine Learning* (2006). Ninguna es prerrequisito para comprender esta guía.

*Guía de estudiantes · G2.4 · Bogotá, octubre de 2026.*
