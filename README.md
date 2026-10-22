# Hydro-Lab G2.4 / S2.10

**Laboratorio educativo de simulación y control de una red sintética de transporte de hidrocarburos.** Aplicación local en Python 3.12 y Streamlit. Incluye control manual y automático, robot de inspección, comparación de políticas y experimentos reproducibles. **No** utiliza datos industriales reales ni está calibrado para una instalación de Ecopetrol. **No** implementa entrenamiento PPO.

## Obtener el código

Desde la página del repositorio de GitHub de **Aprendizaje Profundo**, utiliza **Code → Download ZIP** o descarga la versión etiquetada `v2.10.0` una vez publicada. Los usuarios avanzados pueden copiar la URL HTTPS desde **Code → HTTPS** y ejecutar:

```bash
git clone URL_HTTPS_DEL_REPOSITORIO
cd hydro-lab
```

> La URL definitiva se incorporará al crear el repositorio de la organización. No se ha publicado todavía ninguna etiqueta ni Release.

## Requisitos

Python **3.12**. Windows, macOS o Linux; se requiere verificar las tres plataformas en GitHub Actions antes de anunciar compatibilidad probada. Navegador moderno. No se requiere GPU ni Docker.

## Instalación con Conda

```bash
conda create -n hydro-lab python=3.12 -y
conda activate hydro-lab
python -m pip install -e ".[dev,ui]"
python -m pytest
python -m streamlit run dashboard/app.py
```

## Instalación con Python `venv` + `pip`

**macOS / Linux**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev,ui]"
python -m pytest
python -m streamlit run dashboard/app.py
```

**Windows PowerShell** (sin necesidad de cambiar la política de ejecución):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,ui]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m streamlit run dashboard/app.py
```

La aplicación se abre normalmente en `http://localhost:8501`. Para detenerla, usa **Ctrl+C** en la terminal.

## Documentación

Consulta el [índice de documentación](docs/README.md), el [manual de uso](docs/03_laboratorio/manuales/Manual_Hydro_Lab_S2.10_V2-0.md), el [syllabus](docs/01_curso/syllabus/Syllabus_IA_Avanzada_Ecopetrol_Uniandes_G2.3.md) y la [especificación técnica](docs/03_laboratorio/arquitectura/Red_Hidrocarburos_Especificacion_Matematica_Computacional_G2.4.md).

## Alcance y validación

La suite de pruebas está en `tests/` y el flujo de GitHub Actions ejecuta la matriz de Python 3.12 para Windows, macOS y Linux. Que el flujo exista **no** significa que haya terminado correctamente en los tres sistemas. Los resultados de experimentos son sintéticos y descriptivos.

## Licencia y publicación

**Pendiente de decisión del titular.** No se incluye una licencia de código abierto sin autorización explícita. Antes de hacer público el repositorio, revisar también atribuciones y uso de nombres institucionales.
