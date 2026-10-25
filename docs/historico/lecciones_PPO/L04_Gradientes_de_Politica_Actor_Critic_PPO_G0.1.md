# Lección L04 — De los gradientes de política a PPO

**Generación:** G0.1 · **Sesión:** 2 · **Temas del syllabus:** T3 Policy Gradients, conexión con T2 Deep RL  
**Estado:** primera redacción científica; por revisar y ampliar antes de clase.

## Pregunta rectora

**¿Cómo puede aprender un agente a tomar mejores decisiones directamente, sin que alguien le indique la acción correcta en cada situación?**

En Hydro-Lab, la decisión consiste en elegir velocidades de tres bombas mientras cambian la demanda, la tarifa y la condición de la red. No existe una respuesta óptima escrita de antemano para cada instante. El agente debe descubrir una estrategia a partir de las consecuencias acumuladas de sus decisiones.

## 1. De una regla a una política que aprende

Una regla fija prescribe qué hacer bajo determinadas condiciones. Una **política** es una regla de decisión más general: asocia lo que el agente observa con una acción o con una distribución de posibles acciones. Una política neuronal contiene parámetros ajustables; aprender consiste en modificarlos para favorecer decisiones que, en promedio, producen mejores resultados a lo largo de un episodio.

En el laboratorio, dos decisiones que parecen equivalentes ahora pueden tener consecuencias diferentes más tarde: aumentar la velocidad puede mejorar el suministro inmediato, pero elevar el gasto eléctrico o el desgaste. Por eso no basta con calificar una acción aislada: debemos evaluar trayectorias.

## 2. Qué significa optimizar una política

**Idea esencial.** Imaginemos que repetimos numerosos episodios con una política. Algunas acciones conducen a trayectorias mejores que otras. El aprendizaje refuerza las decisiones asociadas con resultados favorables y debilita las asociadas con resultados desfavorables. Como los resultados dependen también del azar y del contexto, la comparación debe hacerse estadísticamente.

**Formalización opcional.** Para una política estocástica parametrizada por $\theta$ y un retorno descontado $G_t$, definimos

$$
J(\theta)=\mathbb{E}_{\tau\sim\pi_\theta}\left[\sum_{t=0}^{T-1}\gamma^t r_t\right],\qquad 0\leq\gamma\leq1.
$$

La expectativa recorre las trayectorias $\tau$ inducidas por la política y el entorno. El gradiente de política admite, bajo condiciones de regularidad, una expresión del tipo

$$
\nabla_\theta J(\theta)=\mathbb{E}\left[\sum_t \nabla_\theta\log\pi_\theta(a_t\mid o_t)\,\widehat G_t\right],
$$

con las convenciones adecuadas de ponderación temporal. La observación $o_t$ reemplaza al estado verdadero cuando este no es accesible. La fórmula expresa una idea sencilla: modificar la probabilidad de acciones según la calidad de sus consecuencias. No es necesario desarrollar la derivación para comprender el algoritmo.

## 3. Por qué necesitamos un crítico

Si una decisión produce un resultado favorable, ¿fue realmente una buena decisión o simplemente ocurrió en una situación fácil? Necesitamos un punto de comparación. El **crítico** estima cuánto retorno podemos esperar desde la información disponible. El **actor** propone las acciones.

La **ventaja** mide si una acción resultó mejor o peor que ese punto de referencia. Su interpretación es más importante que su expresión algebraica: una recompensa positiva no implica necesariamente una ventaja positiva, porque quizá se esperaba una recompensa aún mayor.

**Formalización opcional.**

$$
A^\pi(s,a)=Q^\pi(s,a)-V^\pi(s).
$$

En un problema parcialmente observable se emplean aproximaciones basadas en observaciones o historias, y no se debe asumir que la observación es el estado físico completo.

## 4. El problema de las actualizaciones demasiado grandes

Supongamos que una política aprendió a operar razonablemente bien. Una actualización agresiva de sus parámetros puede cambiar simultáneamente muchas decisiones y deteriorar el comportamiento. **PPO —Proximal Policy Optimization—** busca mejorar la política evitando incentivar cambios excesivos en una sola actualización.

PPO no garantiza por sí solo que todas las actualizaciones sean pequeñas ni que las decisiones sean seguras. Es una estrategia de optimización práctica, no un certificado de seguridad.

**Formalización opcional.**

$$
L^{\mathrm{CLIP}}(\theta)=\mathbb E_t\left[\min\left(r_t(\theta)\widehat A_t,\operatorname{clip}(r_t(\theta),1-\epsilon,1+\epsilon)\widehat A_t\right)\right],
$$

$$
r_t(\theta)=\frac{\pi_\theta(a_t\mid o_t)}{\pi_{\theta_{\mathrm{old}}}(a_t\mid o_t)}.
$$

La razón $r_t$ compara cuánto favorece la política nueva una acción frente a la política que generó los datos. El recorte limita el incentivo de optimización fuera de un intervalo cercano a uno.

## 5. Qué aportan GAE y la evaluación independiente

**GAE (Generalized Advantage Estimation)** combina información de varios horizontes para estimar ventajas, regulando el compromiso entre sesgo y variabilidad. En lenguaje no matemático: permite usar señales de aprendizaje menos erráticas, sin pretender conocer perfectamente el valor futuro de cada decisión.

Un agente puede mejorar la recompensa definida para entrenarlo y, aun así, empeorar una métrica importante. Por eso evaluaremos por separado servicio, energía, maniobras, intervenciones de seguridad y comportamiento ante escenarios nuevos. No confundiremos entrenamiento exitoso con operación industrial segura.

## 6. Nuestro ejemplo continuo: Hydro-Lab

El entorno S2.10 ofrece tres acciones continuas normalizadas, observaciones ruidosas y una recompensa derivada de costos. Una protección puede modificar la acción solicitada si no es factible. Esto plantea una pregunta científicamente interesante: **¿qué aprendió la política y qué parte del buen comportamiento fue producida por el mecanismo de seguridad?** El experimento EXP02 debe distinguir ambas contribuciones.

## 7. Preguntas para discusión

1. ¿Por qué maximizar la recompensa de un paso puede perjudicar el resultado de un día?
2. ¿Qué diferencia hay entre una política, un actor y un crítico?
3. ¿Por qué una ventaja positiva no significa simplemente una recompensa positiva?
4. ¿Por qué PPO necesita observar muchas trayectorias?
5. ¿Puede una política obtener buena recompensa y ser inaceptable por seguridad?

## 8. Lecturas fundamentales

- Sutton, R. S. y Barto, A. G. (2018). *Reinforcement Learning: An Introduction*, 2.ª ed., capítulos sobre métodos de gradiente de política.
- Schulman, J. et al. (2015). *High-Dimensional Continuous Control Using Generalized Advantage Estimation*.
- Schulman, J. et al. (2017). *Proximal Policy Optimization Algorithms*.

**Nota editorial:** esta lección es conceptual primero; las ecuaciones son una segunda lectura opcional. No incluye instrucciones de uso de la aplicación, que pertenecen al experimento y al manual.
