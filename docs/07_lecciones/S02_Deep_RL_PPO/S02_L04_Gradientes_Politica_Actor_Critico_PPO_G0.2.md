# S02 · L04 — Aprender a decidir: de los gradientes de política a PPO

**Curso:** Inteligencia artificial avanzada — decisiones secuenciales  
**Generación:** G0.2 — nueva redacción integral, para revisión académica  
**Sesión:** S02 · **Lección:** L04  
**Campo de aplicación permanente:** Hydro-Lab G2.4 / S2.10–S2.11  
**Modalidad:** exposición conceptual principal y profundización matemática opcional  

> **Pregunta de la lección.** ¿Cómo puede una máquina aprender una estrategia de operación que no consista en memorizar órdenes, sino en tomar buenas decisiones frente a estados cambiantes, consecuencias futuras e incertidumbre?

## Guía de lectura

El texto tiene dos recorridos. El **recorrido esencial** es la exposición conceptual, los ejemplos y las preguntas de interpretación: puede seguirse de principio a fin sin trabajar las ecuaciones. Los recuadros titulados **Profundización matemática (opcional)** aportan definiciones, demostraciones y formulaciones completas; su lectura no es requisito para entender la narración. En cada apartado, Hydro-Lab representa el mismo problema operativo, no un sustituto de la teoría.

**Al terminar**, el estudiante podrá distinguir agente, entorno, política y entrenamiento; explicar por qué el retorno importa más que una recompensa aislada; comparar métodos basados en valores y en políticas; comprender REINFORCE, línea base, ventaja, actor–crítico y PPO; e interpretar un experimento de entrenamiento sin confundir rendimiento, estabilidad y seguridad.

## 1. Una decisión aparentemente sencilla

Son las seis de la mañana. Una red transporta hidrocarburos mediante tres bombas. La demanda del norte crece; la del sur todavía es moderada. La electricidad no cuesta lo mismo a todas las horas y las bombas acumulan desgaste. El operador debe elegir sus velocidades.

Una decisión inmediata podría ser aumentar las tres velocidades para reducir el riesgo de déficit. Pero esto eleva el consumo y puede resultar innecesario. Otra posibilidad es ahorrar energía bajando las velocidades: la factura mejora ahora, aunque un déficit futuro puede salir mucho más caro. Si una bomba se encuentra degradada, además, una maniobra razonable en condiciones normales podría dejar de serlo.

No estamos buscando **la velocidad correcta para una fotografía fija**. Buscamos una **estrategia** que indique qué hacer ante muchos estados posibles y que tenga en cuenta lo que sucederá después.

Esta diferencia separa una orden de una política de control.

**Pregunta para discutir.** Dos controladores terminan el día con el mismo costo total. Uno mantuvo un suministro estable; el otro produjo déficits graves durante una hora y compensó después. ¿Son equivalentes? ¿Qué información adicional necesitamos para responder?

## 2. Anatomía de un agente

Un **agente** es un sistema que selecciona acciones a partir de la información disponible sobre su entorno. El **entorno** es aquello que cambia como consecuencia de las acciones y de factores externos. La **observación** es la información que recibe el agente; no necesariamente coincide con el estado físico completo. Una **política** es la regla —fija o aprendida— que transforma observaciones o estados en decisiones.

En Hydro-Lab, el entorno es la red hidráulica simulada; el agente es el controlador; la acción es un vector con las velocidades solicitadas de las tres bombas; la observación resume información operativa. Una regla fija también constituye una política. Un agente **no necesita aprender** para ser agente: aprende solamente si existe un procedimiento que modifica su política a partir de la experiencia.

La interacción se repite: el agente observa, decide, el entorno evoluciona y devuelve una nueva observación y una recompensa. Una sucesión de estas interacciones forma una **trayectoria**; un **episodio** es una trayectoria con inicio y criterio de finalización definidos.

Es útil distinguir tres actividades. **Actuar** significa aplicar una política. **Evaluar** significa medir sus consecuencias. **Entrenar** significa cambiar la política usando datos de experiencia. En una aplicación industrial, la política entrenada puede ejecutarse sin continuar actualizando sus parámetros.

Esta progresión recupera deliberadamente la enseñanza del cuaderno `ar_Agente_simple.ipynb`, donde se separan `Environment`, `Agent` y ejecución de un episodio. Aquí el ejemplo de interacción ya no es un entorno abstracto que entrega recompensas aleatorias, sino una red con dinámica física y costos interpretables.

### Profundización matemática (opcional): el proceso de decisión

Un proceso de decisión de Markov (MDP) se representa mediante $(\mathcal S,\mathcal A,P,R,\gamma)$, donde $\mathcal S$ es el espacio de estados, $\mathcal A$ el de acciones, $P(s'\mid s,a)$ la dinámica de transición, $R$ la recompensa y $\gamma$ el factor de descuento. La propiedad de Markov exige que, dado el estado presente y la acción, la distribución del estado siguiente no dependa de la historia previa:

$$
P(S_{t+1}\mid S_0,A_0,\ldots,S_t,A_t)=P(S_{t+1}\mid S_t,A_t).
$$

Cuando el agente solo recibe $O_t$, una política $\pi(a\mid o)$ puede operar bajo **observabilidad parcial**. No debe afirmarse que la observación sea markoviana sin verificarlo. Una política con memoria o un estado de creencias puede aprovechar historia adicional.

## 3. ¿Qué significa que una decisión sea buena?

Una recompensa inmediata mide la conveniencia de una transición según un criterio definido. Pero el problema real es **secuencial**: una decisión cambia las posibilidades futuras. En Hydro-Lab, ahorrar electricidad durante quince minutos no necesariamente mejora la operación del día. La calidad de una política se mide por el resultado acumulado de las decisiones que induce.

Llamamos **retorno** a la suma de recompensas futuras, posiblemente descontadas. El factor de descuento permite dar un peso diferente a resultados próximos y lejanos. No es una tarifa monetaria ni una probabilidad de fallo: es un parámetro de la formulación del problema.

### Profundización matemática (opcional): retorno y valores

Con la convención de recompensa $R_{t+1}$ obtenida después de actuar en $t$:

$$
G_t=\sum_{k=0}^{T-t-1}\gamma^kR_{t+k+1},\qquad 0\leq\gamma\leq 1.
$$

Para una política $\pi$:

$$
V^\pi(s)=\mathbb E_\pi[G_t\mid S_t=s],\qquad
Q^\pi(s,a)=\mathbb E_\pi[G_t\mid S_t=s,A_t=a].
$$

La **ventaja** compara una acción con el comportamiento promedio de la política en ese estado:

$$
A^\pi(s,a)=Q^\pi(s,a)-V^\pi(s).
$$

Las ecuaciones de Bellman expresan la relación entre valor presente y futuro:

$$
V^\pi(s)=\mathbb E_\pi[R_{t+1}+\gamma V^\pi(S_{t+1})\mid S_t=s],
$$

$$
Q^\pi(s,a)=\mathbb E[R_{t+1}+\gamma\mathbb E_{a'\sim\pi(\cdot\mid S_{t+1})}Q^\pi(S_{t+1},a')\mid S_t=s,A_t=a].
$$

Estas expresiones requieren las condiciones habituales de integrabilidad y una convención coherente de terminación. En episodios finitos, el valor terminal se fija de acuerdo con el modelo.

## 4. Una recompensa común para cosas diferentes

Aquí aparece una pregunta decisiva: ¿cómo sumar energía, déficit de suministro y maniobras sin sumar magnitudes incompatibles? **No se suman las magnitudes físicas; se suman sus costos convertidos a una unidad común.**

En S2.10, la recompensa hidráulica es el negativo de un costo expresado en **unidades monetarias sintéticas (UM)**. La energía consumida se multiplica por una tarifa en UM/kWh; el volumen no suministrado, por una penalización en UM/m³; los cambios de velocidad normalizada, por su coeficiente de maniobra. Existe además una penalización para una terminación excepcional. Los costos operativos del robot, cuando participan en el circuito de decisión, requieren tratamiento y registro diferenciados.

**Ejemplo didáctico, no salida del simulador.** Si un intervalo consume 10 kWh con tarifa de 0,18 UM/kWh, su costo energético es 1,8 UM. Si faltó suministrar 1 m³ con penalización de 4 UM/m³, el déficit cuesta 4 UM. Su suma es 5,8 UM antes de considerar maniobras y otros componentes. Las UM **no representan automáticamente pesos ni dólares**.

Esto resuelve la consistencia dimensional, pero no demuestra que los coeficientes sean económicamente correctos. Cambiar las ponderaciones cambia el problema que aprende el agente. En nuestro primer experimento PPO **conservaremos la recompensa S2.10** para no modificar al mismo tiempo el algoritmo y el criterio de evaluación. Más adelante podremos estudiar su sensibilidad.

**Pregunta para discutir.** Si aumentamos diez veces la penalización por déficit, ¿el agente se volvió más inteligente o simplemente cambiamos nuestras preferencias?

## 5. Dos familias de métodos: estimar valores o aprender políticas

En los métodos **basados en valores**, el algoritmo aprende a evaluar estados o pares estado–acción y deriva de allí una decisión. Q-learning y DQN son ejemplos familiares. En los métodos **basados en políticas**, se ajusta directamente una función que asigna acciones o probabilidades a las acciones. Ambos enfoques buscan mejorar decisiones, pero utilizan representaciones y mecanismos de aprendizaje diferentes.

La distinción es especialmente relevante cuando las acciones son **continuas**. En Hydro-Lab no elegimos simplemente entre «encender» y «apagar»: podemos solicitar velocidades normalizadas para tres bombas. Discretizar cada velocidad en muchas opciones produce rápidamente un número grande de combinaciones. Una política parametrizada puede producir directamente una distribución sobre acciones continuas.

Los cuadernos `ar_Gradientes_Politica.ipynb` y `ar_Actor_Critico.ipynb` establecen esta transición desde DQN hacia métodos de política; la conservamos porque es una progresión conceptual útil. No afirmamos que los métodos de política sean siempre mejores: su eficiencia muestral y estabilidad dependen del problema y del algoritmo.

### Profundización matemática (opcional): política estocástica

Una política parametrizada se escribe $\pi_\theta(a\mid s)$, donde $\theta$ son los parámetros de una red neuronal u otro modelo. Para acciones continuas puede utilizarse, por ejemplo, una distribución normal multivariada:

$$
U_t\sim\mathcal N(\mu_\theta(O_t),\Sigma_\theta(O_t)),\qquad A_t=f(U_t),
$$

con una transformación $f$ apropiada para respetar los límites del espacio de acción. La densidad de $A_t$ debe incorporar el cambio de variables cuando corresponda. En la implementación se deberá distinguir la **acción solicitada** de la **acción ejecutada** tras las protecciones del simulador; no son necesariamente idénticas.

## 6. La primera idea: reforzar las acciones que dieron buen resultado

Supongamos que un operador novel prueba varias estrategias. Después de cada jornada examina cuáles decisiones condujeron a mejores resultados y aumenta su disposición a repetirlas. La intuición de **REINFORCE** es semejante: aumentar la probabilidad de las acciones asociadas con retornos altos y disminuir la de las asociadas con retornos bajos.

Hay dos dificultades. Primero, una buena decisión puede ir seguida de un resultado malo por azar o por causas externas. Segundo, el resultado total de una jornada puede fluctuar mucho. Si aprendemos directamente de ese resultado, las actualizaciones serán ruidosas.

La ventaja de REINFORCE es que permite aprender sin conocer las ecuaciones internas del entorno. Su limitación es que suele necesitar numerosas trayectorias y puede presentar alta varianza. No debemos prometer que cada actualización mejorará el resultado.

### Profundización matemática (opcional): de la probabilidad al gradiente

Sea $\tau=(s_0,a_0,r_1,\ldots)$ una trayectoria y $p_\theta(\tau)$ su probabilidad bajo la política. Definimos:

$$
J(\theta)=\mathbb E_{\tau\sim p_\theta}[G_0].
$$

Mediante la identidad del logaritmo de una densidad, y suponiendo que la dinámica del entorno no depende de $\theta$:

$$
\nabla_\theta J(\theta)
=\mathbb E_{\tau\sim p_\theta}\left[G_0\nabla_\theta\log p_\theta(\tau)\right]
=\mathbb E\left[G_0\sum_t\nabla_\theta\log\pi_\theta(A_t\mid S_t)\right].
$$

Bajo las condiciones habituales, puede utilizarse el retorno desde cada instante $G_t$ en lugar del retorno completo, eliminando recompensas anteriores que no dependen de la acción actual:

$$
\nabla_\theta J(\theta)
=\mathbb E\left[\sum_t G_t\nabla_\theta\log\pi_\theta(A_t\mid S_t)\right].
$$

En práctica se aproxima la esperanza con trayectorias y se maximiza una función proporcional a $\sum_t G_t\log\pi_\theta(a_t\mid s_t)$. La expresión exacta del gradiente depende de cómo se defina el objetivo descontado y de la distribución de estados utilizada.

## 7. La línea base: aprender de lo inesperadamente bueno

Considera dos jornadas. En una, la demanda era tan baja que casi cualquier controlador habría funcionado. En otra, la demanda era exigente y una decisión concreta evitó un déficit importante. Un retorno alto no significa lo mismo en ambas situaciones.

Una **línea base** permite comparar lo obtenido con lo que razonablemente se esperaba. En lugar de preguntar «¿cuánta recompensa recibí?», preguntamos «¿cuánto mejor o peor resultó esta decisión que la referencia?». La comparación reduce parte de la variabilidad de la señal de aprendizaje.

Una referencia especialmente útil es el **valor del estado**: el retorno esperado cuando se continúa con la política actual. La diferencia entre el valor de una acción y el valor del estado es su **ventaja**. Una ventaja positiva favorece aumentar la probabilidad de la acción; una negativa, reducirla, en términos del estimador del gradiente.

### Profundización matemática (opcional): por qué una línea base no cambia el gradiente esperado

Si $b(s)$ no depende de la acción seleccionada y se cumplen condiciones de regularidad:

$$
\mathbb E_{a\sim\pi_\theta(\cdot\mid s)}[b(s)\nabla_\theta\log\pi_\theta(a\mid s)]
=b(s)\nabla_\theta\int\pi_\theta(a\mid s)\,da
=b(s)\nabla_\theta 1=0.
$$

Por ello, en el estimador de política podemos sustituir $G_t$ por $G_t-b(S_t)$ sin alterar su esperanza ideal, aunque una línea base estimada y compartida con el actor requiere cuidado en la implementación. Si $b(S_t)\approx V^\pi(S_t)$, el término se aproxima a la ventaja.

## 8. Actor–Crítico: decidir y evaluar son tareas diferentes

El **actor** propone la acción. El **crítico** estima el valor de la situación o de la decisión. Son funciones distintas, aunque pueden compartir parte de una red neuronal.

En Hydro-Lab, el actor puede sugerir aumentar P0 y reducir PN; el crítico estima el retorno esperado de continuar operando desde el estado actual. Tras observar el siguiente estado y la recompensa, el sistema dispone de una señal para revisar su evaluación y ajustar la política.

No debemos imaginar al crítico como un supervisor infalible que conoce la mejor acción. Es un **estimador aprendido** y puede equivocarse. Su utilidad reside en producir una referencia más informativa y, en muchos casos, de menor varianza que el retorno bruto.

El cuaderno `ar_Actor_Critico.ipynb` presenta esta idea mediante A2C, una red con componentes de política y valor y una actualización apoyada en ventajas. Conservamos esa secuencia conceptual, pero trasladamos el ejemplo desde Pong hacia el control continuo de Hydro-Lab.

### Profundización matemática (opcional): error de diferencia temporal

Una señal de aprendizaje de un paso es:

$$
\delta_t=R_{t+1}+\gamma V_\phi(S_{t+1})-V_\phi(S_t).
$$

Aquí $\phi$ parametriza el crítico. Si la transición es verdaderamente terminal, se toma $V_\phi(S_{t+1})=0$; si el episodio fue cortado por un límite administrativo de tiempo y no por un estado terminal, puede ser apropiado conservar el *bootstrap*. Confundir **terminación** con **truncamiento** introduce sesgo.

El actor utiliza una estimación de ventaja $\widehat A_t$ y el crítico ajusta sus predicciones hacia objetivos de retorno. En una arquitectura con parámetros compartidos, las pérdidas deben combinarse cuidadosamente.

## 9. De la ventaja inmediata a GAE

Una estimación basada solo en el siguiente paso responde rápidamente, pero puede arrastrar errores del crítico. Una estimación basada en el resultado de toda la jornada incorpora más información, pero suele variar mucho entre jornadas. **Generalized Advantage Estimation (GAE)** construye un compromiso: combina errores de predicción a diferentes horizontes.

El parámetro $\lambda$ regula cuánto peso damos a consecuencias más lejanas en esta combinación. No es un interruptor universal entre «bien» y «mal»: su elección depende de la calidad del crítico, la duración del episodio y la dinámica del problema.

### Profundización matemática (opcional): GAE

$$
\widehat A_t^{\mathrm{GAE}(\gamma,\lambda)}
=\sum_{l=0}^{T-t-1}(\gamma\lambda)^l\delta_{t+l},
\qquad 0\leq\lambda\leq 1.
$$

Con la convención de bootstrap adecuada, $\lambda=0$ utiliza esencialmente el error TD de un paso; $\lambda=1$ se acerca a una estimación de retorno de horizonte completo menos el valor estimado. Para entrenar el crítico suele construirse un objetivo $\widehat R_t=\widehat A_t+V_\phi(S_t)$, separando correctamente el cálculo del objetivo del gradiente que actualiza el crítico.

## 10. El problema que conduce a PPO

Ya tenemos una política que puede aprender y un crítico que ayuda a evaluar. Falta resolver una dificultad: **¿qué pasa si una actualización cambia demasiado la política?**

Una política que atendía razonablemente bien la demanda puede volverse inestable después de un cambio grande en sus parámetros. Es particularmente peligroso aprender a partir de un lote limitado de trayectorias y luego alterar de manera drástica las probabilidades de las acciones que las generaron.

**Proximal Policy Optimization (PPO)** propone una respuesta práctica: actualizar la política buscando mejoras, pero **reducir el incentivo para cambios excesivos** respecto de la política que produjo los datos. En su variante más conocida, utiliza un objetivo recortado (*clipped objective*).

PPO no garantiza seguridad física, no impone por sí solo un límite estricto de distancia entre políticas y no garantiza mejora monótona. Es una técnica de optimización de políticas; las restricciones operativas deben tratarse además mediante el diseño del entorno, acciones admisibles, evaluación y mecanismos de seguridad.

## 11. Entender el recorte antes de ver la fórmula

Supongamos que, en una situación de demanda elevada, la política anterior asignaba una probabilidad de 20 % a cierta acción. Después de un ajuste, la nueva política le asigna 26 %. La acción se volvió **1,3 veces** tan probable como antes.

Si esa acción tuvo una ventaja positiva, el aprendizaje intenta aumentar su probabilidad. Pero si seguimos premiando indefinidamente aumentos grandes, una sola tanda de datos puede empujar demasiado la política. Con un margen ilustrativo $\epsilon=0,2$, PPO deja de incrementar el incentivo de ese ejemplo cuando la razón supera 1,2. Para ventajas negativas, el recorte actúa sobre el otro extremo: desincentiva reducciones excesivas de probabilidad según el objetivo.

La palabra clave es **incentivo**. El objetivo recortado no impide matemáticamente que otros términos de la pérdida o la actualización global muevan más la política. Por eso, en una implementación seria también se vigilan indicadores como la divergencia KL aproximada y la fracción de muestras recortadas.

### Profundización matemática (opcional): función objetivo de PPO-Clip

Sea $\theta_{\mathrm{old}}$ el parámetro de la política que recolectó las trayectorias y $\theta$ el parámetro candidato:

$$
r_t(\theta)=\frac{\pi_\theta(A_t\mid O_t)}{\pi_{\theta_{\mathrm{old}}}(A_t\mid O_t)}.
$$

El objetivo principal de PPO-Clip es:

$$
L^{\mathrm{CLIP}}(\theta)=
\mathbb E_t\left[
\min\left(
 r_t(\theta)\widehat A_t,
 \operatorname{clip}(r_t(\theta),1-\epsilon,1+\epsilon)\widehat A_t
\right)
\right].
$$

El mínimo establece una cota pesimista del beneficio estimado cuando la razón se aleja demasiado en la dirección que aumentaría el objetivo. Para $\widehat A_t>0$ se limita el incentivo de razones mayores que $1+\epsilon$; para $\widehat A_t<0$, el de razones menores que $1-\epsilon$. No se recortan las probabilidades de la política: se recorta la **razón de densidades en el objetivo**.

Una función de entrenamiento típica combina maximización del objetivo de política, minimización del error del valor y una bonificación de entropía:

$$
L_{\mathrm{total}}(\theta,\phi)=
-L^{\mathrm{CLIP}}(\theta)
+c_v\,\mathbb E_t[(V_\phi(O_t)-\widehat R_t)^2]
-c_H\,\mathbb E_t[\mathcal H(\pi_\theta(\cdot\mid O_t))].
$$

Los coeficientes, normalizaciones y variantes de recorte de valor son decisiones de implementación; no deben confundirse con la definición universal del algoritmo.

## 12. Cómo aprende PPO: una jornada de entrenamiento

El ciclo tiene seis momentos. **Primero**, se ejecuta la política actual durante varios pasos o episodios y se guardan observaciones, acciones, recompensas, terminaciones y probabilidades de las acciones. **Segundo**, el crítico estima valores. **Tercero**, se calculan ventajas y objetivos de valor. **Cuarto**, el algoritmo actualiza la política en pequeños lotes, posiblemente durante varias épocas, usando el objetivo recortado. **Quinto**, se actualiza el crítico y se registran diagnósticos. **Sexto**, se descartan los datos de política antigua para la siguiente recolección *on-policy* y se repite el proceso.

**Entrenar no equivale a evaluar.** Para evaluar congelamos los parámetros y ejecutamos episodios independientes, con escenarios y semillas definidos antes de comparar. Tampoco basta con una curva ascendente de recompensa de entrenamiento: puede reflejar sobreajuste, variabilidad del entorno o un criterio de recompensa mal especificado.

### Profundización matemática (opcional): pseudocódigo conceptual

```text
Inicializar actor πθ y crítico Vφ
Repetir por iteraciones de entrenamiento:
    Recolectar trayectorias con la política πθ_old
    Registrar observaciones, acciones, log-probabilidades, recompensas,
        terminated, truncated y valores estimados
    Calcular ventajas GAE y objetivos del crítico
    Durante K épocas sobre minibatches del lote recolectado:
        Calcular nuevas log-probabilidades y razones de densidad
        Optimizar objetivo PPO-Clip + pérdida de valor + entropía
        Registrar KL aproximada, clip fraction y pérdidas
        Aplicar criterio de parada temprana si se ha definido
    Actualizar θ_old para la siguiente recolección
Congelar la política final y evaluar en episodios separados
```

**Advertencia técnica:** si el simulador proyecta una acción solicitada hacia otra acción segura, el entrenamiento debe registrar consistentemente qué distribución generó la acción solicitada y cuál fue ejecutada. No se debe calcular ingenuamente la densidad de la acción proyectada como si hubiese sido muestreada directamente de la política original.

## 13. PPO en Hydro-Lab: una hipótesis que podemos contrastar

Nuestro experimento central no es «hacer funcionar PPO», sino investigar una hipótesis:

> Una política PPO entrenada con la recompensa S2.10 puede aprender decisiones de bombeo que mejoren el desempeño agregado frente a controladores de referencia en determinados escenarios, sin degradar indebidamente indicadores operativos críticos.

La hipótesis **no es un resultado**. Puede ser rechazada. Un controlador basado en reglas bien diseñado podría superar a PPO en algunos escenarios, especialmente si el entrenamiento es insuficiente o las condiciones cambian.

Para estudiar el problema utilizaremos el mismo simulador, horizontes comparables, conjuntos de semillas separados para entrenamiento y evaluación, y un protocolo que no seleccione únicamente las corridas favorables. Compararemos **retorno**, **costo energético**, **volumen no suministrado**, **maniobras**, **terminaciones**, **acciones corregidas por seguridad** y, cuando corresponda, **desempeño ante escenarios no vistos**. No sustituiremos todas estas variables por un solo promedio.

La aplicación deberá permitir observar, al menos, una curva de entrenamiento, evaluaciones periódicas independientes y una comparación final por escenario. Los resultados todavía no están disponibles: **S2.11 es una herramienta en desarrollo**, no un PPO ya validado.

### Un experimento mental previo a abrir la aplicación

Considera dos políticas: A tiene menor costo medio, pero una pequeña fracción de episodios termina en contingencia; B es ligeramente más costosa, pero nunca incurre en esa contingencia dentro de la muestra observada. ¿Cuál preferirías para operar una red? ¿Cómo cambiaría tu respuesta si la contingencia implica una parada segura y no un daño físico? La discusión revela que **optimizar una recompensa no elimina la necesidad de evaluar riesgos por separado**.

## 14. Qué puede salir mal, incluso cuando el algoritmo converge

**La recompensa puede estar mal alineada.** El agente optimiza lo que hemos codificado, no necesariamente lo que queríamos expresar. Una recompensa en UM coherente dimensionalmente puede contener ponderaciones discutibles.

**La exploración puede ser costosa.** En simulación podemos probar políticas riesgosas bajo protecciones; en un sistema físico no sería aceptable trasladar sin más ese procedimiento.

**La política puede explotar peculiaridades del simulador.** Si una regla artificial permite obtener buena recompensa mediante un comportamiento extraño, PPO podría aprenderlo. Eso es un problema de validez del modelo, no una prueba de inteligencia superior.

**El resultado puede depender de la semilla.** Las redes neuronales, la exploración y los escenarios introducen variación. Una sola corrida no demuestra superioridad.

**La observación puede ser insuficiente.** Si dos estados físicamente diferentes producen observaciones parecidas, la misma acción puede ser correcta en uno e incorrecta en otro. Un MDP bien formulado no garantiza que una política basada solo en observaciones instantáneas tenga toda la información necesaria.

**Las restricciones de seguridad son distintas de la recompensa.** Penalizar una situación peligrosa no garantiza que jamás ocurra. Hydro-Lab mantiene sus mecanismos de protección y debemos registrar cuándo intervienen.

## 15. Comparación conceptual de métodos

| Método | ¿Qué aprende principalmente? | Señal para mejorar | Limitación importante |
|---|---|---|---|
| Reglas fijas | No aprende durante ejecución | Diseño humano | Adaptación limitada |
| Q-learning / DQN | Valores de acciones | Error de Bellman | Acciones continuas requieren tratamientos adicionales |
| REINFORCE | Política | Retornos de trayectorias | Alta varianza |
| Actor–Crítico | Política y valor | Ventaja estimada por crítico | Sesgo o error del crítico |
| PPO-Clip | Política y valor | Ventaja con objetivo recortado | No garantiza seguridad ni mejora monótona; es *on-policy* |

La tabla compara ideas, no establece una clasificación universal de rendimiento. Una evaluación justa requiere tareas, presupuestos computacionales y protocolos comparables.

## 16. Preguntas para comprobar comprensión

1. ¿Por qué una regla fija de operación puede ser un agente aunque no aprenda?
2. ¿Por qué no basta con maximizar la recompensa de los próximos quince minutos?
3. ¿Cuál es la diferencia entre estimar el valor de una acción y aprender directamente una política?
4. ¿Qué problema intenta resolver una línea base en REINFORCE?
5. ¿Qué hace el actor y qué estima el crítico? ¿Por qué el crítico también puede equivocarse?
6. ¿Qué compromiso introduce GAE?
7. En PPO, ¿qué se recorta exactamente? ¿Por qué ese recorte no constituye una garantía formal de seguridad?
8. ¿Por qué la recompensa en UM puede ser dimensionalmente correcta y, sin embargo, requerir calibración?
9. ¿Qué evidencia necesitaríamos antes de afirmar que PPO supera al controlador consciente de la salud?
10. ¿Por qué un agente entrenado puede ejecutarse sin seguir aprendiendo?

## 17. Síntesis

Comenzamos con una decisión operativa: elegir velocidades de bombas. Esa decisión se convirtió en una **política** porque debía funcionar bajo estados cambiantes. El retorno incorporó las consecuencias futuras. Los gradientes de política ofrecieron una manera de aprender directamente esa estrategia. La línea base y el crítico aportaron una referencia para distinguir decisiones mejores o peores que lo esperado. GAE combinó señales a diferentes horizontes. Finalmente, PPO introdujo un mecanismo práctico para reducir el incentivo de actualizaciones excesivas.

La lección no concluye que PPO sea el mejor controlador. Concluye algo más valioso: **ahora sabemos formular una comparación que podría demostrarlo o refutarlo**. Hydro-Lab será el lugar donde sometamos esa afirmación a prueba.

## 18. Referencias y procedencia del material

### Cuadernos docentes proporcionados para esta generación

- Montenegro Díaz, Á. M., y colaboradores. `ar_Aprendizaje_Reforzado_Intro.ipynb`: agente y entorno; episodios; procesos de Markov; recompensa, retorno, valores y políticas.
- Montenegro Díaz, Á. M., y colaboradores. `ar_Agente_simple.ipynb`: separación explícita de clases `Environment` y `Agent` y ejecución de episodios.
- Montenegro Díaz, Á. M., y colaboradores. `ar_Gradientes_Politica.ipynb`: REINFORCE; gradiente logarítmico; comparación con DQN; línea base y variabilidad.
- Montenegro Díaz, Á. M., y colaboradores. `ar_Actor_Critico.ipynb`: ventaja; valor del estado; arquitectura actor–crítico; A2C y entropía.

Los cuadernos anteriores sustentan la **secuencia pedagógica** y varios conceptos de esta lección. Sus ejemplos de ratón, oficinista, CartPole y Pong no se trasladan como prácticas: se reemplazan por el caso continuo de Hydro-Lab. Se han reformulado expresiones matemáticas donde era necesario precisar notación, supuestos o interpretación.

Puede consultar 

### Ampliación científica incorporada en esta generación

- Schulman, J., Levine, S., Moritz, P., Jordan, M., y Abbeel, P. (2015). *Trust Region Policy Optimization*. ICML. https://arxiv.org/abs/1502.05477
- Schulman, J., Moritz, P., Levine, S., Jordan, M., y Abbeel, P. (2016). *High-Dimensional Continuous Control Using Generalized Advantage Estimation*. ICLR. https://arxiv.org/abs/1506.02438
- Schulman, J., Wolski, F., Dhariwal, P., Radford, A., y Klimov, O. (2017). *Proximal Policy Optimization Algorithms*. https://arxiv.org/abs/1707.06347
- Sutton, R. S., y Barto, A. G. (2018). *Reinforcement Learning: An Introduction*, 2.ª ed. MIT Press. http://incompleteideas.net/book/the-book-2nd.html
- Williams, R. J. (1992). *Simple Statistical Gradient-Following Algorithms for Connectionist Reinforcement Learning*. Machine Learning, 8, 229–256.


## Material complementario de consulta

**Aprendizaje Profundo — Diplomado Avanzado en Inteligencia Artificial**

Como material de profundización, los estudiantes pueden consultar los cuadernos de aprendizaje por refuerzo desarrollados por Aprendizaje Profundo. Estos materiales incluyen ejemplos de agentes, políticas, gradientes de política y métodos Actor–Critic, entre otros temas.

**[Consultar los cuadernos de Aprendizaje Reforzado en GitHub](https://github.com/AprendizajeProfundo/Diplomado-Avanzado/tree/main/Aprendizaje%20Reforzado)**

Este material es complementario: permite ampliar los fundamentos y explorar implementaciones, pero no es requisito para comprender la exposición conceptual de esta lección.

### Estado y límites de la generación

Este archivo es **material docente de teoría**, no un manual de interfaz ni un informe de resultados. Las cifras del ejemplo monetario son ilustrativas; la descripción de la recompensa remite a la documentación técnica S2.10 y deberá cotejarse con la versión de código usada en clase. No se han ejecutado entrenamientos PPO ni generado curvas experimentales para este documento. La implementación S2.11 y la práctica EXP02 se documentan por separado.
