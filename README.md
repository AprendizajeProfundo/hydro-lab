# Hydro-Lab G2.4 / S2.11

**Laboratorio educativo de inteligencia artificial avanzada para una red sintética de transporte de hidrocarburos.** Aplicación local en Python 3.12 y Streamlit. Incluye operación manual y automática, comparación de estrategias de control, robot de inspección, análisis de episodios y **entrenamiento, evaluación y comparación de políticas de aprendizaje por refuerzo mediante PPO**.

El laboratorio **no utiliza datos industriales reales**, no está calibrado para una instalación de Ecopetrol y no debe emplearse para operar infraestructura real.

## Obtener el código

Una vez autorizada y habilitada la distribución del repositorio, utiliza **Code → Download ZIP** desde su página de GitHub o copia la URL HTTPS para clonarlo:

```bash
git clone URL_HTTPS_DEL_REPOSITORIO
cd hydro-lab
```

> La URL definitiva, la etiqueta de versión y cualquier Release se anunciarán únicamente después de su creación. No se presupone que exista una versión pública `v2.11.0`.

## Requisitos

- **Python 3.12**.
- Navegador moderno para acceder a Streamlit.
- macOS, Linux o Windows: las instrucciones se proporcionan para estas plataformas, pero la compatibilidad multiplataforma debe confirmarse mediante pruebas de integración.
- No se requiere Docker. El entrenamiento PPO utiliza PyTorch y puede ejecutarse en CPU; su rendimiento dependerá del equipo.

## Instalación con Conda

```bash
conda create -n hydro-lab python=3.12 -y
conda activate hydro-lab
python -m pip install -e ".[dev,ui,ppo]"
python -m pytest -q
python -m streamlit run dashboard/app.py
```

## Instalación con Python `venv` + `pip`

**macOS / Linux**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,ui,ppo]"
python -m pytest -q
python -m streamlit run dashboard/app.py
```

**Windows PowerShell**, sin cambiar la política de ejecución:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,ui,ppo]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
```

La aplicación se abre normalmente en <http://localhost:8501>. Para detenerla, utiliza **Ctrl+C** en la terminal.

Las dependencias opcionales del proyecto están definidas en `pyproject.toml`: `dev` para pruebas, `ui` para la interfaz y `ppo` para Stable-Baselines3 y PyTorch. Para utilizar todas las funciones de S2.11, instala las tres.

## Funcionalidades de S2.11

La interfaz integra la operación de la red, la evolución de episodios, la comparación de estrategias de control, el robot de inspección y una sección de **aprendizaje por refuerzo · PPO**. Esta última permite ejecutar entrenamientos, consultar sus diagnósticos, evaluar políticas y revisar resultados guardados. Los experimentos se realizan sobre el entorno sintético del laboratorio.

## Documentación

- [Índice de documentación](docs/README.md)
- [Syllabus del curso G2.4](docs/01_curso/syllabus/Syllabus_IA_Avanzada_Ecopetrol_Uniandes_G2.4.md)
- [Ocho cuadernos Jupyter del curso](docs/01_curso/lecciones/Cuadernos/)
- [Manual de Hydro-Lab S2.11 G3.1](docs/03_laboratorio/manuales/Manual_Hydro_Lab_S2.11_G3.1.md)
- [Guía de estudiantes S2.11 G3.4](docs/03_laboratorio/manuales/Guia_Estudiantes_Hydro_Lab_S2.11_G3.4.md)
- [Especificación matemática y computacional G2.4](docs/03_laboratorio/arquitectura/Red_Hidrocarburos_Especificacion_Matematica_Computacional_G2.4.md)
- [Documentación técnica del desarrollo PPO](docs/06_desarrollo/S2.11_PPO/)

## Validación y reproducibilidad

La suite de pruebas se encuentra en `tests/`. En la revisión local de S2.11 se ejecutó `python -m pytest -q` con **125 pruebas aprobadas**. Este resultado no constituye por sí solo una validación de Windows, Linux y macOS. Los resultados de entrenamiento y otros artefactos generados se almacenan localmente; la carpeta `/resultados/` está excluida del control de versiones.

## Licencia y publicación

**Pendiente de decisión y autorización del titular de los derechos.** La ausencia de una licencia abierta no concede permiso general de reutilización o redistribución. Antes de hacer público el repositorio se deben revisar las atribuciones de materiales de terceros, los derechos de los cuadernos y las autorizaciones para el uso de nombres institucionales.
