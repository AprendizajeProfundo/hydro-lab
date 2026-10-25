"""Hydro-Lab S2.11 Control Center — launch with streamlit run dashboard/app.py."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import json
import subprocess
import time
import zipfile
import io
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from hydro_lab.control_center import EpisodeSession, run_comparison, safe_filename
from hydro_lab.benchmark import save_report
from hydro_lab.active_benchmark import active_paired_benchmark
from hydro_lab.paired_statistics import (
    paired_inference, holm_adjust, interpretation,
    fixed_feedback_differences, inspection_differences, robust_differences,
)

st.set_page_config(page_title='Hydro-Lab Control Center',page_icon='🛢️',layout='wide')
st.title('Hydro-Lab · Control Center')
st.caption('Laboratorio sintético de transporte de hidrocarburos · 1 paso = 15 minutos')

with st.sidebar:
    st.header('Escenario')
    seed=st.number_input('Semilla reproducible',min_value=0,max_value=2147483647,value=20261019,step=1)
    policy=st.selectbox('Controlador',['demand_feedback','health_aware','health_robust','constant','manual'],format_func=lambda x:{'demand_feedback':'Realimentación de demanda','health_aware':'Control sensible a salud','health_robust':'Control robusto a ruido','constant':'Velocidad constante','manual':'Manual'}[x])
    robot_policy=st.selectbox('Robot de inspección', ['off','manual','uncertainty','value'],format_func=lambda x:{'off':'Sin inspección','manual':'Control manual','uncertainty':'Priorizar incertidumbre','value':'Inspección costo-consciente'}[x])
    nominal=st.checkbox('Escenario nominal',value=False,help='Exógenas nominales, sin eliminar el modelo de fallas')
    horizon=st.slider('Horizonte (pasos de 15 min)',1,96,96)
    st.caption('Cambiar parámetros no modifica el episodio en curso. Pulsa Crear episodio.')
    if st.button('Crear / reiniciar episodio',type='primary',use_container_width=True):
        if 'session' in st.session_state: st.session_state.session.close()
        st.session_state.session=EpisodeSession(int(seed),policy,nominal,horizon,robot_policy)
        st.session_state.config=(int(seed),policy,nominal,horizon,robot_policy)
    if 'session' not in st.session_state:
        st.session_state.session=EpisodeSession(int(seed),policy,nominal,horizon,robot_policy)
        st.session_state.config=(int(seed),policy,nominal,horizon,robot_policy)

session=st.session_state.session
cfg=st.session_state.config
tab1,tab2,tab3,tab4,tab5=st.tabs(['Operar la red','Evolución y episodios','Comparar estrategias de control','Robot de inspección','Aprendizaje por refuerzo · PPO'])

def network_figure(record):
    f=go.Figure()
    positions={0:(0,0),1:(1,0),2:(2,1),3:(2,-1),4:(3,0)}
    edges=[(0,1),(1,2),(2,4),(1,3),(3,4)]
    for i,(a,b) in enumerate(edges):
        x0,y0=positions[a];x1,y1=positions[b]
        f.add_trace(go.Scatter(x=[x0,x1],y=[y0,y1],mode='lines',line=dict(color='#1689a8',width=6),hoverinfo='text',text=f'Tubería {a}→{b}',showlegend=False))
    for i,(x,y) in positions.items():
        f.add_trace(go.Scatter(x=[x],y=[y],mode='markers+text',marker=dict(size=32,color=('#2e86ab' if i in (0,4) else '#ffb703'),line=dict(color='#263238',width=1)),text=[f'N{i}'],textposition='middle center',textfont=dict(color='black',size=11),hoverinfo='text',hovertext=f'Nodo {i}',showlegend=False))
    for x,y,name in ((.5,.12,'P0'),(1.4,.65,'PN'),(1.4,-.65,'PS')):
        f.add_annotation(x=x,y=y,text=name,showarrow=False,bgcolor='#f0e1a1',font=dict(color='#202020',size=12))
    f.update_layout(height=340,margin=dict(l=10,r=10,t=10,b=10),xaxis=dict(visible=False,range=[-.3,3.3]),yaxis=dict(visible=False,range=[-1.35,1.35],scaleanchor='x',scaleratio=1),showlegend=False)
    return f

with tab1:
    st.subheader('Red de cinco nodos · Tres bombas · Dos ramales')
    st.caption(f'Episodio activo: semilla {cfg[0]} · política {cfg[1]} · nominal={cfg[2]} · horizonte={cfg[3]}')
    left,right=st.columns([1.3,1])
    with left:
        st.plotly_chart(network_figure(session.records[-1] if session.records else None),use_container_width=True)
    with right:
        st.markdown('**Consignas de velocidad de las bombas**')
        disabled=session.policy_name!='manual' or session.finished
        u0=st.slider('P0 (principal)',.60,1.00,.80,.01,disabled=disabled)
        un=st.slider('PN (norte)',.60,1.00,.80,.01,disabled=disabled)
        us=st.slider('PS (sur)',.60,1.00,.80,.01,disabled=disabled)
        if session.policy_name!='manual':
            st.caption('Las consignas las determina la política elegida. Para manipularlas, selecciona Manual y crea un episodio.')
        robot_action = st.selectbox('Acción del robot para el próximo avance',
            ['wait','move_BASE','move_P0','move_PN','move_PS','inspect'],
            disabled=session.robot_policy!='manual' or session.finished,
            help='Una acción robótica por cada paso hidráulico; desplazamientos solo entre estaciones vecinas.')
        b1,b2,b3=st.columns(3)
        with b1: one=st.button('▶ Un paso',disabled=session.finished,use_container_width=True)
        with b2: four=st.button('▶ 1 hora',disabled=session.finished,use_container_width=True)
        with b3: allsteps=st.button('▶ Hasta el final',disabled=session.finished,use_container_width=True)
        if one or four or allsteps:
            session.advance(1 if one else 4 if four else 96,(u0,un,us),robot_action=robot_action)
            st.rerun()
        st.metric('Pasos ejecutados',f'{len(session.records)} / {session.max_steps}')
        st.metric('Recompensa acumulada',f'{session.reward_total:,.2f} UM')
        if session.finished:
            st.success('Episodio terminado por contingencia' if session.terminated else 'Horizonte completado (truncado)')
    if session.records:
        last=session.records[-1]
        st.markdown('**Último paso ejecutado**')
        m=st.columns(4)
        m[0].metric('Energía',f"{last['energy_kwh']:.2f} kWh")
        m[1].metric('Demanda no atendida',f"{last['unserved_m3']:.2f} m³")
        m[2].metric('Estado hidráulico',last['hydraulic_status'])
        m[3].metric('Seguridad',last['intervention_reason'] or 'Sin intervención')
        st.caption('Las magnitudes anteriores corresponden al último paso, no al episodio completo.')

with tab2:
    st.subheader('Evolución temporal')
    if not session.records:
        st.info('Ejecuta al menos un paso en la pestaña Operar la red.')
    else:
        df=pd.DataFrame(session.records)

        #sel=st.slider('Inspeccionar paso',1,len(df),len(df))
        
        if len(df) == 1:
            sel = 1
            st.info("Solo hay un paso registrado: paso 1.")
        else:
            sel = st.slider(
                "Inspeccionar paso",
                min_value=1,
                max_value=len(df),
                value=len(df)
            )
        selected=session.records[sel-1]
        st.caption(f"Paso {sel} · t={selected['hour']:.2f} h · acción ejecutada {tuple(round(x,3) for x in selected['action_executed'])}")
        def grafico_temporal(series, titulo, eje_y, clave):
            figura = go.Figure()

            for columna, etiqueta, color in series:
                figura.add_trace(go.Scatter(
                    x=df["hour"],
                    y=df[columna],
                    mode="lines",
                    name=etiqueta,
                    line=dict(color=color, width=2),
                    hovertemplate=(
                        "Tiempo: %{x:.2f} h"
                        "<br>Valor: %{y:.3f}"
                        "<extra>%{fullData.name}</extra>"
                    ),
                ))

            figura.update_layout(
                title=dict(text=titulo, font=dict(size=16)),
                xaxis_title="Tiempo simulado (horas)",
                yaxis_title=eje_y,
                legend_title_text="Series",
                hovermode="x unified",
                height=360,
                margin=dict(l=45, r=20, t=55, b=50),
            )

            st.plotly_chart(
                figura,
                use_container_width=True,
                key=clave,
            )

        col1, col2 = st.columns(2)

        with col1:
            grafico_temporal(
                [
                    ("observed_volume0_m3", "Tanque de origen", "#1769AA"),
                    ("observed_volume4_m3", "Tanque receptor", "#E69F00"),
                ],
                "Inventarios observados",
                "Volumen (m³)",
                "s211_evolucion_inventarios",
            )

            grafico_temporal(
                [
                    ("observed_demand_m3_s", "Demanda observada", "#1769AA"),
                ],
                "Evolución de la demanda",
                "Caudal demandado (m³/s)",
                "s211_evolucion_demanda",
            )

            grafico_temporal(
                [
                    ("unserved_m3", "Demanda no atendida", "#C44E52"),
                ],
                "Demanda no atendida por intervalo",
                "Volumen no atendido (m³)",
                "s211_evolucion_deficit",
            )

        with col2:
            grafico_temporal(
                [
                    ("cumulative_reward", "Recompensa acumulada", "#1769AA"),
                ],
                "Recompensa acumulada",
                "Recompensa (UM)",
                "s211_evolucion_recompensa",
            )

            grafico_temporal(
                [
                    ("energy_kwh", "Energía consumida", "#009E73"),
                ],
                "Consumo energético por intervalo",
                "Energía (kWh)",
                "s211_evolucion_energia",
            )

        r=session.report()
        c=st.columns(4)
        c[0].metric('Energía total',f"{r['total_energy_kwh']:,.1f} kWh")
        c[1].metric('Demanda no atendida total',f"{r['total_unserved_m3']:,.1f} m³")
        c[2].metric('Intervenciones',r['interventions'])
        c[3].metric('Error máx. masa',f"{max(abs(x['mass_error_m3']) for x in r['records']):.2e} m³")
        if session.finished:
            st.caption('Finalización: ' + ('contingencia · ' + str(r.get('termination_reason') or 'causa no especificada') if session.terminated else 'horizonte completado (truncado)'))
        st.download_button('Descargar episodio JSON',session.json_bytes(),file_name=safe_filename('hydro_s211_episode',session.seed),mime='application/json')
        if st.button('Guardar episodio en results/'):
            path=Path('results')/safe_filename('hydro_s211_episode',session.seed)
            try:
                save_report(r,path)
                st.success(f'Guardado: {path}')
            except OSError as exc:
                st.error(f'No se pudo guardar: {exc}')
        with st.expander('Tabla de trazas (datos de evaluación)'):
            columnas_redondeo = [
                "controller_health_observation",
                "action_requested",
                "action_executed",
                "mass_error_m3",
                "evaluation_true_volumes_m3",
                "evaluation_true_health",
            ]

            def redondear_visual(valor):
                if isinstance(valor, (list, tuple, np.ndarray)):
                    return type(valor)(
                        redondear_visual(x) for x in valor
                    ) if not isinstance(valor, np.ndarray) else np.array(
                        [redondear_visual(x) for x in valor]
                    )
                if isinstance(valor, (float, np.floating)):
                    return round(float(valor), 4)
                return valor

            df_visual = df.copy(deep=True)

            for columna in columnas_redondeo:
                if columna in df_visual.columns:
                    df_visual[columna] = df_visual[columna].map(
                        redondear_visual
                    )

            if "evaluation_true_volumes_m3" in df_visual.columns:
                def formato_volumen(valor):
                    if isinstance(valor, (list, tuple, np.ndarray)):
                        return "[" + ", ".join(
                            formato_volumen(x) for x in valor
                        ) + "]"
                    if isinstance(valor, dict):
                        return "{" + ", ".join(
                            f"{k}: {formato_volumen(v)}"
                            for k, v in valor.items()
                        ) + "}"
                    if isinstance(valor, (int, float, np.number)):
                        return f"{float(valor):.4f}"
                    return str(valor)

                df_visual["evaluation_true_volumes_m3"] = (
                    df_visual["evaluation_true_volumes_m3"].map(formato_volumen)
                )

            st.dataframe(df_visual, use_container_width=True)

def _fmt(value, decimals=2):
    return f"{float(value):,.{decimals}f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def _metric_delta(summary, arm_a, arm_b, key, unit, label):
    """Only descriptive mean differences; never imply a separate significance test."""
    try:
        delta = float(summary[arm_b][key]) - float(summary[arm_a][key])
    except (KeyError, TypeError, ValueError):
        return None
    direction = 'aumentó' if delta > 0 else 'disminuyó' if delta < 0 else 'no cambió'
    return f"{label} {direction} {_fmt(abs(delta))} {unit}"


def _technical_reading(result, *, adjusted_p=None, context=None):
    """Auditable, deterministic interpretation; no language model required."""
    context = context or {}
    n = result['n']
    mean = result['mean']
    name_a = context.get('a', 'A')
    name_b = context.get('b', 'B')
    if mean is None:
        return 'No hay datos suficientes para estimar la diferencia media.'
    direction = (f'favorece descriptivamente a {name_b}' if mean > 0 else
                 f'favorece descriptivamente a {name_a}' if mean < 0 else
                 'no muestra una diferencia media observada')
    parts = [f"En {n} parejas de escenarios, la diferencia media de recompensa "
             f"({name_b} menos {name_a}) fue {_fmt(mean)} UM; "
             f"el resultado {direction}."]
    if result['status'] == 'ok':
        low, high = result['ci_low'], result['ci_high']
        p = adjusted_p if adjusted_p is not None else result['p']
        kind = 'ajustado por Holm' if adjusted_p is not None else 'bilateral'
        parts.append(f"El intervalo de confianza del 95 % fue "
                     f"[{_fmt(low)}; {_fmt(high)}] UM y el valor p {kind} fue {p:.4g}.")
        if p < .05:
            sign = ('positiva' if low > 0 else 'negativa' if high < 0 else 'distinta de cero')
            parts.append(f"Bajo los supuestos de la prueba existe evidencia estadística "
                         f"de una diferencia media {sign} al nivel del 5 %" +
                         (' después del ajuste por comparaciones múltiples.' if adjusted_p is not None else '.'))
        else:
            parts.append('No hay evidencia estadística suficiente para rechazar una diferencia '
                         'media nula al nivel del 5 %. Esto no demuestra equivalencia ni ausencia de efecto.')
        if low <= 0 <= high:
            parts.append('El intervalo incluye cero: los datos son compatibles con efectos '
                         'de distinto signo dentro de los límites estimados.')
        if result['sd'] is not None and abs(mean) > 0 and result['sd'] < .02 * abs(mean):
            parts.append('Las diferencias entre semillas son extraordinariamente estables; '
                         'conviene comprobar si un costo casi fijo domina el contraste. '
                         'Un valor p muy pequeño no garantiza relevancia operacional.')
    else:
        parts.append('La inferencia t no es calculable con estas diferencias; '
                     'no corresponde emitir una conclusión de significación estadística.')
    summary = context.get('summary')
    if summary:
        a, b = context.get('arm_a'), context.get('arm_b')
        metrics = context.get('metrics', ())
        observed = [_metric_delta(summary, a, b, *metric) for metric in metrics]
        observed = [v for v in observed if v]
        if observed:
            parts.append('En términos operacionales, las medias descriptivas muestran que ' +
                         '; '.join(observed) + '. Estas diferencias operacionales no cuentan '
                         'aquí con pruebas inferenciales individuales.')
        if context.get('termination_key'):
            try:
                ta = float(summary[a][context['termination_key']])
                tb = float(summary[b][context['termination_key']])
                if abs(tb-ta) > 1e-9:
                    parts.append('Las tasas de terminación difieren entre estrategias '
                                 f'({_fmt(100*ta, 1)} % frente a {_fmt(100*tb, 1)} %): '
                                 'las métricas acumuladas pueden corresponder a duraciones distintas.')
            except (KeyError, TypeError, ValueError):
                pass
    if context.get('robot_cost_note'):
        parts.append('La recompensa neta incluye los costos de inspección. Una pérdida próxima '
                     'al costo robótico sugiere un beneficio hidráulico insuficiente para '
                     'compensarlo en estas simulaciones; no demuestra inutilidad general del robot.')
    if context.get('symmetry_note'):
        parts.append('Sin inspección, las tres estimaciones de salud comienzan iguales y la '
                     'predicción solo incrementa su incertidumbre. Por construcción, los '
                     'controladores sensible a salud y robusto aplican entonces las mismas '
                     'acciones de realimentación de demanda.')
    if n < 10:
        parts.append('Con menos de diez parejas, el resultado es especialmente sensible '
                     'a los supuestos de normalidad de las diferencias y a observaciones atípicas.')
    parts.append('Compartir semillas mejora la comparabilidad, pero no garantiza independencia '
                 'ni representatividad. Las conclusiones se limitan al simulador sintético; '
                 'no constituyen una garantía de desempeño o seguridad industrial.')
    return '\n\n'.join(parts)


def render_paired_statistics(differences, title, *, adjusted_p=None, key='paired', context=None):
    """Resultados, incertidumbre e interpretación del contraste B menos A."""
    result = paired_inference(differences, label=title)
    st.markdown(f"**Inferencia estadística · {title}**")
    a, b, c, d = st.columns(4)
    a.metric('Parejas (n)', result['n'])
    b.metric('Diferencia media (UM)', f"{result['mean']:,.2f}" if result['mean'] is not None else 'No estimable')
    c.metric('Desviación estándar (UM)', 'No estimable' if result['sd'] is None else f"{result['sd']:,.2f}")
    d.metric('Valor p bilateral', 'No calculable' if result['p'] is None else f"{result['p']:.4g}")
    if result['status'] == 'ok':
        st.write(f"**IC del 95 % para la diferencia media:** "
                 f"[{result['ci_low']:,.2f}, {result['ci_high']:,.2f}] UM "
                 f"· t = {result['t']:.3f} · gl = {result['df']} "
                 f"· error estándar = {result['se']:.3f} UM")
        if adjusted_p is not None:
            st.write(f"**Valor p ajustado por Holm (tres regímenes):** {adjusted_p:.4g}")
    chart = pd.DataFrame({'Semilla (índice de pareja)': range(1, result['n'] + 1),
                          'Diferencia B − A (UM)': result['differences']})
    st.bar_chart(chart.set_index('Semilla (índice de pareja)'))
    st.markdown('**Interpretación técnica: qué podemos afirmar y qué no**')
    reading = _technical_reading(result, adjusted_p=adjusted_p, context=context)
    st.info(reading)
    result['technical_interpretation'] = reading
    if result['status'] == 'ok':
        st.caption('El IC del 95 % cuantifica incertidumbre bajo el modelo de inferencia; '
                   'no significa que haya una probabilidad del 95 % de que el parámetro fijo esté en este intervalo.')
    with st.expander('¿Cómo se calcula esta prueba? Ecuaciones, hipótesis y supuestos'):
        st.write('Para cada semilla se calcula la diferencia entre la recompensa de B y la de A:')
        st.latex(r'D_i = R_i(B)-R_i(A),\qquad i=1,\ldots,n')
        st.latex(r'\bar D = \frac{1}{n}\sum_{i=1}^n D_i,\qquad s_D = \sqrt{\frac{1}{n-1}\sum_{i=1}^n(D_i-\bar D)^2}')
        st.latex(r'EE(\bar D)=\frac{s_D}{\sqrt n},\qquad T=\frac{\bar D}{s_D/\sqrt n}')
        st.latex(r'H_0:\mu_D=0,\qquad H_1:\mu_D\ne 0')
        st.latex(r'IC_{95\%}(\mu_D)=\bar D\pm t_{0.975,n-1}\frac{s_D}{\sqrt n}')
        st.write('Bajo la hipótesis nula y los supuestos de la prueba, T sigue una distribución '
                 't de Student con n − 1 grados de libertad. El valor p es bilateral.')
        st.markdown('**Supuestos y alcance.** Las parejas deben ser independientes entre sí; '
                    'con pocas parejas, la prueba es sensible a la normalidad de las diferencias. '
                    'Compartir semilla permite comparar condiciones reproducibles, pero no '
                    'garantiza independencia, normalidad ni trayectorias idénticas. '
                    'Las recompensas acumuladas pueden verse afectadas por terminaciones anticipadas. '
                    'Los resultados corresponden a escenarios sintéticos, no a validación industrial.')
        st.markdown('**Comparaciones múltiples.** En el experimento robusto se ajustan por Holm '
                    'los tres valores p correspondientes a los tres regímenes.')
    return result


def render_termination_diagnostics(diag, *, key):
    """Visual summary of existing termination JSON; no simulator changes."""
    if not diag or any(not isinstance(v, dict) for v in diag.values()):
        st.info('El reporte no incluye diagnósticos. Ejecuta de nuevo la comparación.')
        return
    rows = []
    cause_rows = []
    for arm, d in diag.items():
        total = int(d.get('n_episodes') or 0)
        nterm = int(d.get('n_terminated') or 0)
        rows.append({
            'Estrategia': arm,
            'Episodios': total,
            'Terminaciones anticipadas': nterm,
            'Tasa (%)': 100 * nterm / total if total else 0.0,
            'Pasos medios hasta terminación': d.get('mean_steps_to_termination'),
        })
        for reason, count in (d.get('termination_reason_counts') or {}).items():
            cause_rows.append({
                'Estrategia': arm,
                'Causa registrada': reason,
                'Casos': int(count),
                'Incidencia (%)': 100 * int(count) / total if total else 0.0,
                'Entre terminados (%)': 100 * int(count) / nterm if nterm else 0.0,
            })
    st.markdown('**Frecuencia de terminación anticipada**')
    summary = pd.DataFrame(rows)
    st.dataframe(summary, hide_index=True, use_container_width=True,
                 column_config={
                     'Tasa (%)': st.column_config.NumberColumn(format='%.1f %%'),
                     'Pasos medios hasta terminación': st.column_config.NumberColumn(format='%.1f'),
                 })
    st.bar_chart(summary.set_index('Estrategia')['Tasa (%)'],
                 x_label='Estrategia', y_label='Terminaciones anticipadas (%)')
    if cause_rows:
        st.markdown('**Causas observadas**')
        causes = pd.DataFrame(cause_rows)
        st.dataframe(causes, hide_index=True, use_container_width=True,
                     column_config={
                         'Incidencia (%)': st.column_config.NumberColumn(format='%.1f %%'),
                         'Entre terminados (%)': st.column_config.NumberColumn(format='%.1f %%'),
                     })
        chart = causes.pivot_table(index='Estrategia', columns='Causa registrada',
                                   values='Incidencia (%)', aggfunc='sum', fill_value=0)
        st.bar_chart(chart, x_label='Estrategia',
                     y_label='Incidencia por causa (% de episodios)')
    else:
        st.success('No se registraron terminaciones anticipadas en los episodios evaluados.')
    st.caption('Incidencia: porcentaje sobre todos los episodios de cada estrategia. '
               'Entre terminados: porcentaje sobre los episodios que finalizaron anticipadamente. '
               'El horizonte completado no se considera una contingencia. '
               'Los resultados describen únicamente los escenarios simulados.')
    with st.expander('Ver datos originales (JSON)'):
        st.json(diag)


with tab3:
    st.subheader('Control fijo frente a realimentación de demanda')
    st.write('Cada política se evalúa con las mismas semillas. Se presenta inferencia pareada, sujeta a los supuestos estadísticos y al alcance del simulador.')
    n=st.slider('Número de semillas pareadas',2,100,5)
    st.caption(f'Cada semilla define un escenario reproducible evaluado con ambas estrategias: {n} parejas = {2*n} episodios.')
    first=st.number_input('Primera semilla',min_value=0,max_value=2147483500,value=1000,step=1)
    if st.button('Ejecutar comparación',type='primary'):
        with st.spinner(f'Simulando {2*n} episodios…'):
            st.session_state.comparison=run_comparison(tuple(range(int(first),int(first)+n)))
    if 'comparison' in st.session_state:
        rep=st.session_state.comparison
        st.dataframe(pd.DataFrame(rep['summary']).T,use_container_width=True)
        with st.expander('Diagnóstico de terminaciones por controlador'):
            diag = {k: v.get('termination_diagnostics') for k, v in rep['summary'].items()}
            if all(value is not None for value in diag.values()):
                render_termination_diagnostics(diag, key='fixed_term')
            else:
                st.info('Resultado anterior al diagnóstico. Vuelve a ejecutar la comparación con el parche instalado.')
        st.metric('Diferencia media pareada de recompensa',f"{rep['comparison']['paired_mean_reward_difference']:,.2f} UM")
        st.caption('Realimentación menos constante. Recompensas menos negativas son mejores; las terminaciones anticipadas afectan las métricas acumuladas.')
        stat_fixed = render_paired_statistics(
            fixed_feedback_differences(rep), 'Realimentación menos control constante', key='fixed',
            context={'a':'control constante','b':'realimentación de demanda',
                     'summary':rep['summary'], 'arm_a':'constant', 'arm_b':'demand_feedback',
                     'termination_key':'terminal_rate',
                     'metrics':(('mean_energy_kwh','kWh','la energía media'),
                                ('mean_unserved_m3','m³','la demanda no atendida media'),
                                ('mean_interventions','','las intervenciones medias'))})
        st.download_button('Descargar inferencia pareada (JSON)',
            json.dumps(stat_fixed, ensure_ascii=False, indent=2).encode('utf-8'),
            file_name='inferencia_control_fijo.json', mime='application/json', key='fixed_stats_download')
        st.download_button('Descargar comparación JSON',json.dumps(rep,ensure_ascii=False,indent=2).encode('utf-8'),file_name=safe_filename('hydro_s211_benchmark',int(first)),mime='application/json')

    st.divider()
    st.subheader('Valor de la inspección robótica')
    st.caption('Cuatro brazos pareados: realimentación y control sensible a salud, cada uno con robot apagado o autónomo. La recompensa neta descuenta costos robóticos.')
    n_active=st.slider('Semillas para inspección robótica',2,30,5,key='s28_n')
    st.caption(f'{n_active} semillas comunes para cuatro estrategias: {4*n_active} episodios, con comparaciones pareadas por semilla.')
    first_active=st.number_input('Primera semilla de inspección',min_value=0,max_value=2147483500,value=2000,step=1,key='s28_seed')
    if st.button('Ejecutar comparación de inspección'):
        with st.spinner(f'Simulando {4*n_active} episodios…'):
            st.session_state.active_comparison=active_paired_benchmark(tuple(range(int(first_active),int(first_active)+n_active)))
    if 'active_comparison' in st.session_state:
        result=st.session_state.active_comparison
        st.dataframe(pd.DataFrame(result['summary']).T,use_container_width=True)
        with st.expander('Diagnóstico de terminaciones por estrategia'):
            diag = {k: v.get('termination_diagnostics') for k, v in result['summary'].items()}
            if all(value is not None for value in diag.values()):
                render_termination_diagnostics(diag, key='active_term')
            else:
                st.info('Resultado anterior al diagnóstico. Vuelve a ejecutar la comparación con el parche instalado.')
        st.metric('Valor neto pareado de inspección (política sensible a salud)',f"{result['paired_mean_net_reward_difference_um']:,.2f} UM")
        st.caption('Positivo favorece al robot; negativo indica que la inspección no compensó su costo en estas semillas.')
        stat_inspection = render_paired_statistics(
            inspection_differences(result), 'Inspección por incertidumbre menos robot apagado', key='inspection',
            context={'a':'control sensible a salud sin robot', 'b':'control sensible a salud con inspección',
                     'summary':result['summary'], 'arm_a':'health_aware/off',
                     'arm_b':'health_aware/uncertainty', 'robot_cost_note':True,
                     'metrics':(('net_reward_um','UM','la recompensa neta media'),
                                ('robot_cost_um','UM','el costo robótico medio'),
                                ('energy_kwh','kWh','la energía media'),
                                ('unserved_m3','m³','la demanda no atendida media'))})
        st.download_button('Descargar inferencia de inspección (JSON)',
            json.dumps(stat_inspection, ensure_ascii=False, indent=2).encode('utf-8'),
            file_name='inferencia_inspeccion.json', mime='application/json', key='inspection_stats_download')
        st.download_button('Descargar comparación de inspección JSON',json.dumps(result,ensure_ascii=False,indent=2).encode('utf-8'),file_name=safe_filename('hydro_s211_paired',int(first_active)),mime='application/json')


    st.divider()
    st.subheader("Control robusto e inspección inteligente")
    st.caption(
        "Comparación pareada de cuatro estrategias bajo operación de referencia, "
        "degradación y desgaste acelerado. Se incluye inferencia pareada y ajuste de Holm."
    )

    n_robust = st.number_input(
        "Número de semillas para control robusto",
        min_value=1,
        max_value=100,
        value=5,
        step=1,
        key="robust_comparison_n",
    )

    st.caption(f'{int(n_robust)} semillas por régimen y cuatro estrategias: {12*int(n_robust)} episodios en tres regímenes.')

    output_root = Path("results") / "comparaciones_control_robusto"
    output_root.mkdir(parents=True, exist_ok=True)

    if st.button("Ejecutar comparación de control robusto", key="run_robust_comparison"):
        stamp = time.strftime("%Y%m%d_%H%M%S")
        output_dir = output_root / f"comparacion_{stamp}_{time.time_ns() % 1000000:06d}"
        command = [
            sys.executable,
            "examples/compare_s210.py",
            "--seeds", str(int(n_robust)),
            "--output", str(output_dir),
        ]
        log_file = output_root / f"{output_dir.name}.log"

        with log_file.open("w", encoding="utf-8") as log:
            process = subprocess.Popen(
                command,
                cwd=str(Path(__file__).resolve().parents[1]),
                stdout=log,
                stderr=subprocess.STDOUT,
            )

        st.session_state["robust_comparison_job"] = {
            "pid": process.pid,
            "output": str(output_dir),
            "log": str(log_file),
        }
        st.success("Comparación iniciada. Puedes consultar su resultado aquí.")

    job = st.session_state.get("robust_comparison_job")
    if job:
        output_dir = Path(job["output"])
        report_path = output_dir / "comparison_s210.json"
        log_path = Path(job["log"])

        if report_path.exists():
            report = json.loads(report_path.read_text(encoding="utf-8"))
            st.success("Comparación finalizada.")

            regime_labels = {
                "baseline": "Operación de referencia",
                "degraded": "Operación degradada",
                "accelerated_wear": "Desgaste acelerado",
            }
            arm_labels = {
                "health_aware/off": "Control sensible a salud · Sin robot",
                "health_aware/uncertainty": "Control sensible a salud · Inspección por incertidumbre",
                "health_robust/off": "Control robusto · Sin robot",
                "health_robust/value": "Control robusto · Inspección costo-consciente",
            }

            regimes = list(report['summary'])
            regime_stats = {
                regime: paired_inference(robust_differences(report, regime))
                for regime in regimes
            }
            adjusted = holm_adjust([regime_stats[regime]['p'] for regime in regimes])
            inference_export = {}
            for regime, groups in report["summary"].items():
                st.markdown(f"**{regime_labels.get(regime, regime)}**")
                rows = []
                for arm, values in groups.items():
                    if arm.startswith("paired_"):
                        continue
                    rows.append({
                        "Estrategia": arm_labels.get(arm, arm),
                        "Recompensa media (UM)": values["reward_um"],
                        "Energía media (kWh)": values["energy_kwh"],
                        "Costo robótico medio (UM)": values["robot_cost_um"],
                        "Inspecciones medias": values["inspections"],
                        "Demanda no atendida media (m³)": values["unserved_m3"],
                    })
                st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
                with st.expander('Diagnóstico de terminaciones por estrategia · ' + regime_labels.get(regime, regime)):
                    diag = {arm_labels.get(k, k): v.get('termination_diagnostics') for k, v in groups.items() if not k.startswith('paired_')}
                    if diag and all(value is not None for value in diag.values()):
                        render_termination_diagnostics(diag, key=f'robust_term_{regime}')
                    else:
                        st.info('El reporte no incluye aún diagnósticos de terminación. Ejecuta nuevamente con el parche instalado.')

                effect = groups["paired_robust_value_minus_robust_off"]["mean_um"]
                st.metric(
                    "Efecto pareado: control robusto con inspección frente a sin inspección",
                    f"{effect:,.2f} UM",
                )
                regime_index = regimes.index(regime)
                stat = render_paired_statistics(
                    robust_differences(report, regime),
                    'Control robusto con inspección menos control robusto sin inspección',
                    adjusted_p=adjusted[regime_index], key=f'robust_{regime}',
                     context={'a':'control robusto sin robot', 'b':'control robusto con inspección',
                              'summary':groups, 'arm_a':'health_robust/off',
                              'arm_b':'health_robust/value', 'robot_cost_note':True,
                              'symmetry_note':True,
                              'metrics':(('energy_kwh','kWh','la energía media'),
                                         ('unserved_m3','m³','la demanda no atendida media'),
                                         ('robot_cost_um','UM','el costo robótico medio'),
                                         ('inspections','','las inspecciones medias'))})
                inference_export[regime] = {**stat, 'holm_adjusted_p': adjusted[regime_index]}

            st.caption(
                "La inferencia se realiza por régimen. Holm ajusta los tres contrastes, "
                "pero no demuestra seguridad ni superioridad universal."
            )

            st.download_button(
                'Descargar inferencia robusta (JSON)',
                json.dumps(inference_export, ensure_ascii=False, indent=2).encode('utf-8'),
                file_name='inferencia_control_robusto.json', mime='application/json',
                key='robust_stats_download',
            )

            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
                for filename in (
                    "comparison_s210.json",
                    "episodes_s210.csv",
                    "summary_s210.md",
                ):
                    file_path = output_dir / filename
                    if file_path.exists():
                        archive.write(file_path, arcname=filename)

            st.download_button(
                "Descargar resultados completos (ZIP)",
                data=buffer.getvalue(),
                file_name="comparacion_control_robusto.zip",
                mime="application/zip",
                key="download_robust_comparison",
            )

        else:
            st.info("La comparación está en ejecución o pendiente de finalizar.")
            if log_path.exists():
                log_text = log_path.read_text(encoding="utf-8")
                if log_text.strip():
                    with st.expander("Registro de ejecución"):
                        st.code(log_text[-4000:])
            if st.button("Actualizar estado", key="refresh_robust_comparison"):
                st.rerun()


with tab4:
    st.subheader('Robot de inspección · Observación activa')
    st.caption('Grafo de caminos independiente de las tuberías: BASE ↔ P0 ↔ PN y P0 ↔ PS. Una arista por paso de 15 minutos. Inspeccionar no repara.')
    robot=session.robot
    c=st.columns(4)
    c[0].metric('Posición',robot.position)
    c[1].metric('Batería',f'{robot.battery:.1f} / 100')
    c[2].metric('Inspecciones',robot.inspections)
    c[3].metric('Costo robótico',f'{robot.cost_um:.2f} UM')
    st.write('Política robótica activa:',session.robot_policy)
    if session.robot_policy=='off':
        st.info('Selecciona Manual, Priorizar incertidumbre o Inspección costo-consciente en la barra lateral y crea un nuevo episodio.')
    elif session.robot_policy=='manual':
        st.info('Selecciona una acción robótica en «Operar la red» y avanza un paso. Las rutas no adyacentes son rechazadas sin consumir batería.')
    else:
        st.info('Heurística demostrativa: visita la bomba con mayor incertidumbre estimada. No maximiza explícitamente el valor económico de la información.')
    st.write('Estimación de salud accesible al controlador y su incertidumbre:')
    if session.policy_name in ('health_aware', 'health_robust'):
        st.success('Control sensible a salud o robusto activo: las estimaciones de inspección pueden modificar las consignas a partir del siguiente paso.')
    else:
        st.caption('El controlador seleccionado no utiliza explícitamente las estimaciones de salud.')
    st.dataframe(pd.DataFrame({'bomba':['P0','PN','PS'],
        'estimación':session.env.belief.estimate,
        'incertidumbre':session.env.belief.uncertainty}),hide_index=True,use_container_width=True)
    if robot.events:
        events_df = pd.DataFrame(robot.events)
        for column in ("belief_estimates", "belief_uncertainty"):
            if column in events_df.columns:
                events_df[column] = events_df[column].map(
                    lambda values: (
                        "[" + ", ".join(f"{float(v):.4f}" for v in values) + "]"
                        if isinstance(values, (list, tuple, np.ndarray))
                        else values
                    )
                )
        st.dataframe(events_df, use_container_width=True)
        history = pd.DataFrame([{'paso':i+1,'batería':e['battery_after'],
            **{f'estimación_{k}':e['belief_estimates'][j] for j,k in enumerate(('P0','PN','PS'))},
            **{f'incertidumbre_{k}':e['belief_uncertainty'][j] for j,k in enumerate(('P0','PN','PS'))}}
            for i,e in enumerate(robot.events)])
        px = __import__('plotly.express',fromlist=['line'])
        st.plotly_chart(px.line(history,x='paso',y='batería',title='Evolución de batería'),use_container_width=True)
        st.plotly_chart(px.line(history,x='paso',y=['estimación_P0','estimación_PN','estimación_PS'],title='Estimación de salud por bomba'),use_container_width=True)
        st.plotly_chart(px.line(history,x='paso',y=['incertidumbre_P0','incertidumbre_PN','incertidumbre_PS'],title='Incertidumbre por bomba'),use_container_width=True)

st.divider()
st.caption('Hydro-Lab S2.11 · Red hidráulica y robot de inspección sintéticos · Datos no calibrados para operación industrial · Diagnósticos verdaderos solo para evaluación, no para políticas')


with tab5:
    import ppo_tab as s211_ppo_tab
    s211_ppo_tab.render()
