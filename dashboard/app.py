"""S2.6 Hydro-Lab Control Center — launch with streamlit run dashboard/app.py."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from hydro_lab.control_center import EpisodeSession, run_comparison, safe_filename
from hydro_lab.benchmark import save_report
from hydro_lab.active_benchmark import active_paired_benchmark

st.set_page_config(page_title='Hydro-Lab Control Center',page_icon='🛢️',layout='wide')
st.title('Hydro-Lab · Control Center')
st.caption('G2.4 / S2.10 · Laboratorio sintético de transporte de hidrocarburos · 1 paso = 15 minutos')

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
tab1,tab2,tab3,tab4=st.tabs(['Operar la red','Evolución y episodios','Comparar controladores','Robot de inspección'])

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
        col1,col2=st.columns(2)
        with col1:
            st.plotly_chart(__import__('plotly.express',fromlist=['line']).line(df,x='hour',y=['observed_volume0_m3','observed_volume4_m3'],title='Inventarios observados (m³)'),use_container_width=True)
            st.plotly_chart(__import__('plotly.express',fromlist=['line']).line(df,x='hour',y=['observed_demand_m3_s'],title='Demanda observada (m³/s)'),use_container_width=True)
        with col2:
            st.plotly_chart(__import__('plotly.express',fromlist=['line']).line(df,x='hour',y=['cumulative_reward'],title='Recompensa acumulada (UM)'),use_container_width=True)
            st.plotly_chart(__import__('plotly.express',fromlist=['line']).line(df,x='hour',y=['energy_kwh','unserved_m3'],title='Energía (kWh) y déficit (m³) por paso; escalas distintas'),use_container_width=True)
        r=session.report()
        c=st.columns(4)
        c[0].metric('Energía total',f"{r['total_energy_kwh']:,.1f} kWh")
        c[1].metric('Demanda no atendida total',f"{r['total_unserved_m3']:,.1f} m³")
        c[2].metric('Intervenciones',r['interventions'])
        c[3].metric('Error máx. masa',f"{max(abs(x['mass_error_m3']) for x in r['records']):.2e} m³")
        st.download_button('Descargar episodio JSON',session.json_bytes(),file_name=safe_filename('hydro_s26_episode',session.seed),mime='application/json')
        if st.button('Guardar episodio en results/'):
            path=Path('results')/safe_filename('hydro_s26_episode',session.seed)
            try:
                save_report(r,path)
                st.success(f'Guardado: {path}')
            except OSError as exc:
                st.error(f'No se pudo guardar: {exc}')
        with st.expander('Tabla de trazas (datos de evaluación)'):
            st.dataframe(df,use_container_width=True)

with tab3:
    st.subheader('Experimento pareado: constante vs. realimentación')
    st.write('Cada política se evalúa con las mismas semillas. La comparación es descriptiva; no constituye evidencia concluyente con pocas réplicas.')
    n=st.slider('Número de semillas pareadas',2,100,5)
    first=st.number_input('Primera semilla',min_value=0,max_value=2147483500,value=1000,step=1)
    if st.button('Ejecutar benchmark',type='primary'):
        with st.spinner(f'Simulando {2*n} episodios…'):
            st.session_state.comparison=run_comparison(tuple(range(int(first),int(first)+n)))
    if 'comparison' in st.session_state:
        rep=st.session_state.comparison
        st.dataframe(pd.DataFrame(rep['summary']).T,use_container_width=True)
        st.metric('Diferencia media pareada de recompensa',f"{rep['comparison']['paired_mean_reward_difference']:,.2f} UM")
        st.caption('Realimentación menos constante. Recompensas menos negativas son mejores; las terminaciones anticipadas afectan las métricas acumuladas.')
        st.download_button('Descargar benchmark JSON',json.dumps(rep,ensure_ascii=False,indent=2).encode('utf-8'),file_name=safe_filename('hydro_s26_benchmark',int(first)),mime='application/json')

    st.divider()
    st.subheader('S2.8 · Experimento factorial de observación activa')
    st.caption('Cuatro brazos pareados: realimentación y control sensible a salud, cada uno con robot apagado o autónomo. La recompensa neta descuenta costos robóticos.')
    n_active=st.slider('Semillas S2.8',2,30,5,key='s28_n')
    first_active=st.number_input('Primera semilla S2.8',min_value=0,max_value=2147483500,value=2000,step=1,key='s28_seed')
    if st.button('Ejecutar comparación S2.8'):
        with st.spinner(f'Simulando {4*n_active} episodios…'):
            st.session_state.active_comparison=active_paired_benchmark(tuple(range(int(first_active),int(first_active)+n_active)))
    if 'active_comparison' in st.session_state:
        result=st.session_state.active_comparison
        st.dataframe(pd.DataFrame(result['summary']).T,use_container_width=True)
        st.metric('Valor neto pareado de inspección (política sensible a salud)',f"{result['paired_mean_net_reward_difference_um']:,.2f} UM")
        st.caption('Positivo favorece al robot; negativo indica que la inspección no compensó su costo en estas semillas. Resultados descriptivos, no prueba de superioridad.')
        st.download_button('Descargar experimento S2.8 JSON',json.dumps(result,ensure_ascii=False,indent=2).encode('utf-8'),file_name=safe_filename('hydro_s28_paired',int(first_active)),mime='application/json')

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
    if session.policy_name == 'health_aware':
        st.success('Control sensible a salud activo: las estimaciones de inspección afectan las consignas del siguiente paso.')
    else:
        st.caption('El controlador seleccionado no utiliza explícitamente las estimaciones de salud.')
    st.dataframe(pd.DataFrame({'bomba':['P0','PN','PS'],
        'estimación':session.env.belief.estimate,
        'incertidumbre':session.env.belief.uncertainty}),hide_index=True,use_container_width=True)
    if robot.events:
        st.dataframe(pd.DataFrame(robot.events),use_container_width=True)
        history = pd.DataFrame([{'paso':i+1,'batería':e['battery_after'],
            **{f'estimación_{k}':e['belief_estimates'][j] for j,k in enumerate(('P0','PN','PS'))},
            **{f'incertidumbre_{k}':e['belief_uncertainty'][j] for j,k in enumerate(('P0','PN','PS'))}}
            for i,e in enumerate(robot.events)])
        px = __import__('plotly.express',fromlist=['line'])
        st.plotly_chart(px.line(history,x='paso',y='batería',title='Evolución de batería'),use_container_width=True)
        st.plotly_chart(px.line(history,x='paso',y=['estimación_P0','estimación_PN','estimación_PS'],title='Estimación de salud por bomba'),use_container_width=True)
        st.plotly_chart(px.line(history,x='paso',y=['incertidumbre_P0','incertidumbre_PN','incertidumbre_PS'],title='Incertidumbre por bomba'),use_container_width=True)

st.divider()
st.caption('S2.8: integración experimental de estimaciones y control · S2.7: robot discreto, observación activa y costos de inspección · Motor hidráulico S2.1–S2.5 sin modificaciones · Datos sintéticos, no calibrados con operación industrial · Diagnósticos verdaderos solo para evaluación, no para políticas')
