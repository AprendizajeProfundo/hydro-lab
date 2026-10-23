"""S2.11 interactive PPO lab. Additive UI; hydraulic simulator is unchanged."""
from __future__ import annotations
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT / 'resultados' / 's211_replicas_05'
DIAGNOSTICS = ROOT / 'resultados' / 's211_estudio_05' / 'diagnostico_multisemilla_correcto'
RUNS = ROOT / 'resultados' / 's211_dashboard'


def _csv(path):
    try:
        return pd.read_csv(path) if path.is_file() else None
    except (OSError, ValueError, pd.errors.EmptyDataError):
        return None


def _checkpoints():
    folders = [HISTORICAL / f'seed_{seed}' for seed in (41, 42, 43)]
    if RUNS.is_dir():
        folders += [p / 'checkpoint' for p in sorted(RUNS.glob('train_*'), reverse=True)]
    return {str(p.relative_to(ROOT)): p for p in folders if all(
        (p / f).is_file() for f in ('ppo_model.zip', 'normalization.pkl', 'metadata.json'))}


def _graph(df, title, x_candidates=('timesteps', 'total_timesteps', 'step', 'steps')):
    if df is None or df.empty:
        st.caption(f'{title}: todavía no hay datos disponibles.')
        return
    st.dataframe(df.tail(100), use_container_width=True, hide_index=True)
    numeric = df.select_dtypes(include='number').columns.tolist()
    x = next((c for c in x_candidates if c in numeric), None)
    if x is None:
        x = next((c for c in numeric if 'step' in c.lower()), None)
    y = [c for c in numeric if c != x and any(t in c.lower() for t in
         ('reward', 'return', 'loss', 'value', 'entropy', 'kl', 'explained', 'energy', 'unserved'))]
    if x and y:
        chosen = st.selectbox(f'Indicador · {title}', y, key=f'plot_selector_{title}_{st.session_state.get("s211_history_model", "current")}')
        st.plotly_chart(px.line(df, x=x, y=chosen, markers=True, title=f'{title}: {chosen}'), use_container_width=True, key=f'plot_line_{title}_{st.session_state.get("s211_history_model", "current")}')


def _run_folder():
    return st.session_state.get('s211_run_folder')


def _show_progress():
    path_text = _run_folder()
    if not path_text:
        st.caption('No hay un entrenamiento iniciado en esta sesión.')
        return
    folder = Path(path_text)
    st.code(str(folder.relative_to(ROOT)))
    status_file = folder / 'dashboard_status.json'
    if status_file.is_file():
        try:
            status = json.loads(status_file.read_text(encoding='utf-8'))
            state = status.get('state', 'unknown')
            if state == 'completed':
                st.success('Entrenamiento terminado. El modelo está disponible en Evaluar.')
            elif state == 'failed':
                st.error('Entrenamiento fallido: ' + str(status.get('detail', '')))
            else:
                st.info('Entrenamiento en ejecución. Los indicadores aparecen cuando el entrenador los publica.')
        except (OSError, ValueError):
            st.info('Leyendo estado del entrenamiento…')
    else:
        st.info('Inicializando entrenamiento…')
    log = folder / 'dashboard_training.log'
    if log.is_file():
        content = log.read_text(encoding='utf-8', errors='replace')
        with st.expander('Registro de ejecución', expanded=True):
            st.code(content[-7000:] if content else 'Esperando mensajes…')
    for filename, title in [('validation_during_training.csv', 'Validación periódica'),
                            ('ppo_diagnostics.csv', 'Diagnósticos PPO'),
                            ('episodes_training.csv', 'Episodios de entrenamiento')]:
        df = _csv(folder / 'checkpoint' / filename)
        if df is not None:
            with st.expander(title, expanded=filename.startswith('validation')):
                _graph(df, title)


def _training():
    st.markdown('#### 1. Configurar y entrenar un agente PPO')
    st.caption('Los parámetros crean un entrenamiento nuevo; nunca sobrescriben los checkpoints existentes.')
    a, b, c = st.columns(3)
    seed = int(a.number_input('Semilla de entrenamiento', 1, 999999, 44, step=1))
    timesteps = int(b.selectbox('Pasos totales', [1024, 2048, 4096, 8192], index=2))
    validation_count = int(c.slider('Escenarios de validación', 1, 8, 8))
    d, e, f = st.columns(3)
    n_steps = int(d.selectbox('n_steps · horizonte PPO', [128, 256, 512], index=1))
    batch_size = int(e.selectbox('batch_size', [32, 64, 128], index=1))
    eval_every = int(f.selectbox('Validar cada N pasos', [512, 1024, 2048], index=1))
    st.caption('El número real de pasos puede redondearse al final de un rollout. Las validaciones no actualizan la política.')
    confirm = st.checkbox('Confirmo que deseo iniciar un entrenamiento nuevo', key='s211_confirm_train')
    if st.button('▶ Iniciar entrenamiento PPO', type='primary', disabled=not confirm, key='s211_launch'):
        folder = RUNS / f'train_seed_{seed}_{datetime.now():%Y%m%d_%H%M%S_%f}'
        folder.mkdir(parents=True, exist_ok=False)
        log = folder / 'dashboard_training.log'
        cmd = [sys.executable, '-u', str(Path(__file__).with_name('ppo_worker.py')),
               '--output', str(folder), '--seed', str(seed), '--timesteps', str(timesteps),
               '--n-steps', str(n_steps), '--batch-size', str(batch_size),
               '--eval-every', str(eval_every), '--validation-count', str(validation_count)]
        env = dict(os.environ)
        env['PYTHONPATH'] = str(ROOT / 'src') + os.pathsep + env.get('PYTHONPATH', '')
        try:
            with log.open('w', encoding='utf-8') as handle:
                proc = subprocess.Popen(cmd, cwd=str(ROOT), env=env, stdout=handle,
                                        stderr=subprocess.STDOUT, start_new_session=True)
            st.session_state['s211_run_folder'] = str(folder)
            st.session_state['s211_run_pid'] = proc.pid
            st.success(f'Proceso iniciado (PID {proc.pid}). Puedes consultar el progreso abajo.')
        except OSError as exc:
            st.error(f'No se pudo iniciar el entrenamiento: {exc}')
    st.markdown('#### 2. Seguimiento del entrenamiento')
    if hasattr(st, 'fragment'):
        @st.fragment(run_every='3s')
        def live():
            _show_progress()
        live()
    else:
        if st.button('Actualizar progreso', key='s211_refresh'):
            pass
        _show_progress()
    st.caption('Las curvas se actualizan cuando el entrenador escribe los CSV; si los escribe al final, el registro muestra el estado mientras tanto.')


def _evaluation():
    st.markdown('#### Evaluar un modelo PPO entrenado')
    checkpoints = _checkpoints()
    if not checkpoints:
        st.warning('No hay modelos PPO completos disponibles.')
        return
    selected = st.selectbox('Checkpoint', list(checkpoints), key='s211_eval_checkpoint')
    folder = checkpoints[selected]
    try:
        with st.expander('Metadatos del modelo'):
            st.json(json.loads((folder / 'metadata.json').read_text(encoding='utf-8')))
    except (OSError, ValueError) as exc:
        st.warning(f'Metadatos no legibles: {exc}')
    count = st.slider('Escenarios de validación para evaluación', 1, 8, 8, key='s211_eval_count')
    st.caption('La evaluación utiliza semillas de validación separadas de las de entrenamiento.')
    if st.button('▶ Evaluar y comparar con políticas de referencia', key='s211_eval_start'):
        from hydro_lab.s211_study05 import diagnose
        output = RUNS / f'eval_{datetime.now():%Y%m%d_%H%M%S_%f}'
        try:
            with st.spinner('Ejecutando escenarios de validación…'):
                report = diagnose([folder], output=output, split='validation', scenario_count=count)
            st.session_state['s211_last_eval'] = str(output)
            st.success('Evaluación finalizada y guardada.')
            st.json(report)
        except Exception as exc:
            st.error(f'Error de evaluación: {exc}')
    result_dir = st.session_state.get('s211_last_eval')
    if result_dir:
        _comparison(Path(result_dir))


def _comparison(directory, context='evaluation'):
    summary = _csv(directory / 'summary_by_seed.csv')
    if summary is None:
        st.warning('No se encontró el resumen de evaluación.')
        return
    st.dataframe(summary, use_container_width=True, hide_index=True)
    if {'training_seed', 'policy', 'mean_return_um'}.issubset(summary.columns):
        for col, label in [('mean_return_um', 'Retorno medio (UM)'),
                           ('mean_unserved_m3', 'Volumen no atendido (m³)'),
                           ('mean_energy_kwh', 'Consumo energético (kWh)'),
                           ('early_terminations', 'Terminaciones anticipadas')]:
            if col in summary:
                st.plotly_chart(px.bar(summary, x='policy', y=col, color='policy',
                                       facet_col='training_seed' if summary.training_seed.nunique() > 1 else None,
                                       title=label), use_container_width=True, key=f'plot_bar_{context}_{directory.resolve()}_{col}')
    between = _csv(directory / 'between_seed_variability.csv')
    if between is not None:
        st.markdown('**Diferencias pareadas PPO − referencia, por semilla de entrenamiento**')
        st.dataframe(between, use_container_width=True, hide_index=True)
        st.caption('Intervalos descriptivos: no constituyen inferencia confirmatoria con pocas semillas.')
    episodes = _csv(directory / 'episodes.csv')
    if episodes is not None:
        with st.expander('Resultados por episodio y escenario'):
            st.dataframe(episodes, use_container_width=True, hide_index=True)
    for name in ('summary_by_seed.csv', 'episodes.csv', 'paired.csv'):
        p = directory / name
        if p.is_file():
            st.download_button(f'Descargar {name}', p.read_bytes(), file_name=name,
                               mime='text/csv', key=f'download_{context}_{directory.resolve()}_{name}')


def _history():
    st.markdown('#### Historial de modelos y experimentos')
    checkpoints = _checkpoints()
    if checkpoints:
        chosen = st.selectbox('Modelo para consultar curvas de entrenamiento', list(checkpoints), key='s211_history_model')
        folder = checkpoints[chosen]
        for filename, title in [('validation_during_training.csv', 'Validación durante entrenamiento'),
                                ('ppo_diagnostics.csv', 'Diagnósticos PPO'),
                                ('episodes_training.csv', 'Episodios de entrenamiento')]:
            with st.expander(title, expanded=filename.startswith('validation')):
                _graph(_csv(folder / filename), title)
    st.markdown('#### Diagnóstico multisemilla existente')
    _comparison(DIAGNOSTICS, context='historical_multiseed')
    if RUNS.is_dir():
        evals = [p for p in sorted(RUNS.glob('eval_*'), reverse=True) if (p / 'summary_by_seed.csv').is_file()]
        if evals:
            selected = st.selectbox('Evaluaciones anteriores', evals, format_func=lambda p: p.name)
            _comparison(selected, context='historical_evaluation')


def render():
    st.subheader('S2.11 · Laboratorio interactivo de aprendizaje por refuerzo')
    st.info('Simulación educativa. PPO no está validado para operación industrial; las comparaciones son exploratorias.')
    t1, t2, t3 = st.tabs(['Entrenar y observar', 'Evaluar y comparar', 'Consultar resultados'])
    with t1:
        _training()
    with t2:
        _evaluation()
    with t3:
        _history()
