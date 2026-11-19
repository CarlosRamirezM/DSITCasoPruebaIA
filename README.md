# DSITCasoPruebaIA

Prototipo local del **Agente de IA Cuenta** de la DSIT (Universidad de los Andes). Responde en lenguaje natural sobre contraseña, A2P, correo Uniandes, correo alterno y seguridad de la cuenta, usando RAG sobre una base de conocimiento (`kb/`) con LangChain, Ollama (`llama3.2`) y una interfaz Gradio.

> **Estado:** prototipo funcional. Solo el Flujo 2 (contraseña) tiene contenido real; los Flujos 1, 3 y 4 son placeholders y el agente deriva a canales oficiales en esos temas. Ver [CLAUDE.md](CLAUDE.md) para el diseño completo.

## Requisitos

- Python 3.11 – 3.13 (se recomienda 3.12). Con Python 3.15 varias dependencias no tienen wheels y la instalación falla.
- [Ollama](https://ollama.com) en ejecución en `http://localhost:11434`, con los modelos `llama3.2` y `nomic-embed-text`.

## Instalación (PowerShell)

El repo está en una ruta con espacios: usa comillas.

```powershell
cd "<ruta al repo>\DSITCasoPruebaIA"

# Crear y activar un entorno virtual (puede estar fuera del repo)
py -3.12 -m venv "<ruta del venv>"
& "<ruta del venv>\Scripts\Activate.ps1"

python -m pip install -r requirements.txt

# Modelos de Ollama (si aún no los tienes)
ollama pull llama3.2
ollama pull nomic-embed-text
```

Para comprobar que Ollama responde y tiene los modelos:

```powershell
Invoke-RestMethod http://localhost:11434/api/tags | Select-Object -ExpandProperty models | Select-Object name
```

## Ejecución

```powershell
python ingest/build_index.py   # construye el índice vectorial desde kb/ (repetir si cambia la KB)
python app/gradio_app.py       # abre la demo en http://127.0.0.1:7860
```

## Pruebas

```powershell
pytest                                          # todas (las marcadas "ollama" requieren Ollama activo)
pytest -m "not ollama"                          # solo las que no necesitan Ollama
pytest tests/test_guardrails.py::test_nombre    # una sola prueba
```

## Configuración

Se leen de variables de entorno (ver `rag/config.py`): `LLM_MODEL`, `EMBED_MODEL`, `OLLAMA_URL`, `TOP_K`, `MAX_DISTANCE`, `MAX_WORDS`.

## Base de conocimiento

Los documentos viven en `kb/`. Tras reemplazar un placeholder por el contenido oficial, vuelve a ejecutar `python ingest/build_index.py`.
