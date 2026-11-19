# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Estado actual del repo

Implementado: `kb/` (Flujo 2 real + 3 placeholders), `ingest/build_index.py`, `rag/` (`config`, `retriever`, `chain`, `guardrails`), `app/gradio_app.py` y `tests/`. `docs/projectDescription.pdf` fue cotejado con esta especificación y coincide. El repo vive en OneDrive en una ruta con espacios: entrecomillar rutas (entorno Windows/PowerShell). Python 3.15 no sirve (sin wheels); usar 3.11–3.13 (el venv de trabajo es 3.12, fuera del repo).

Decisiones tomadas: vectorstore **Chroma** en `.chroma/` (distancia coseno, ignorado por git); `chain.answer()` aplica, en orden: filtro de entrada → ruteo por palabras clave a temas placeholder → recuperación (umbral `MAX_DISTANCE=0.39` para fuera de alcance; mensajes de ≤3 palabras se recuperan junto con el mensaje previo) → LLM → `guardrails.verify_output`. Los datos de contacto se leen en tiempo de ejecución del bullet "Canales oficiales" de la KB (`retriever.official_channels`); no los dupliques en código.

## Proyecto

Prototipo del **Agente de IA Cuenta** para la Dirección de Servicios de Información y Tecnología (DSIT) de la Universidad de los Andes. Permite a la comunidad uniandina autogestionar, en lenguaje natural y con disponibilidad 24/7:

- Gestión de contraseña (cambio, vencimiento, olvido, restablecer acceso).
- Autenticación en dos pasos (A2P): Microsoft Authenticator, código de 6 dígitos, SMS o llamada.
- Gestión de la cuenta de correo Uniandes (consultar, recordar).
- Gestión de correo alterno (consultar, recordar, cambiar).
- Gestión de seguridad: configurar métodos de inicio de sesión.

Este prototipo es local y desechable: sirve para validar el enfoque de RAG, el control de alucinaciones y el tono de conversación antes de cualquier integración con un canal real (Copilot Studio, WhatsApp, etc.).

## Documentos de la base de conocimiento (KB)

El agente responde **solo** con base en estos cuatro documentos, cada uno como un archivo independiente en `kb/`:

| Archivo | Tema | Estado en este repo |
|---|---|---|
| `Flujo_2_Restablecer_Cambio_Contrasena_V5.4.md` | Restablecer acceso y cambio de contraseña | Contenido conocido (ver abajo), transcrito de la versión 5_4 |
| `Flujo_1_Usuario_V5_2.md` | Gestión de cuenta de correo Uniandes y correo alterno | **Placeholder** — no se ha compartido el archivo real |
| `Flujo_3_Metodos_Autenticacion_A2P_V5_1.md` | Configuración y uso de A2P | **Placeholder** — no se ha compartido el archivo real |
| `Flujo4_Seguridad_Cuenta_V1_1.md` | Configuración de métodos de inicio de sesión / seguridad de la cuenta | **Placeholder** — no se ha compartido el archivo real |

⚠️ **No se tiene acceso a los tres archivos marcados como placeholder.** Mientras no se compartan:
- Crear cada archivo con un encabezado, la fecha, y una nota explícita `[PLACEHOLDER — reemplazar con el contenido oficial antes de cualquier demo con usuarios reales]`.
- No inventar pasos, enlaces, nombres de pantallas ni opciones de menú para estos tres temas. Si el prototipo recibe una pregunta que solo esos documentos podrían responder, debe decir que no tiene esa información todavía y derivar a canales oficiales, nunca improvisar.
- Cuando se compartan los archivos reales, reemplazar el contenido del placeholder sin tocar la estructura del resto del proyecto (el índice vectorial se puede reconstruir solo con el comando de ingesta).

### Contenido conocido — Flujo 2 (Restablecer y Cambio de Contraseña v5_4)

Usar este texto, sin reescribirlo, como fuente para ese documento:

- **Cambio de contraseña** (usuario puede iniciar sesión): ir a cuenta Uniandes → "Cambiar contraseña" → `https://mysignins.microsoft.com/security-info/password/change` → ingresar correo y contraseña actual → autenticarse → definir y confirmar la nueva contraseña según la política → enviar.
- **Restablecer mi acceso** (olvidó o venció la contraseña): ir a `https://cuenta.uniandes.edu.co` → "Restablecer mi acceso" → `https://passwordreset.microsoftonline.com/` → ingresar correo y CAPTCHA → elegir método de verificación (correo alterno, SMS, llamada, notificación de app o código de app de autenticación) → ingresar el código → definir y confirmar la nueva contraseña → enviar.
- **Contraseña para usuario nuevo**: si no llegó o no se encuentra el correo de bienvenida con la contraseña inicial, usar el flujo de "Restablecer mi acceso".
- **Cierres inesperados en Teams/Outlook/Zoom por contraseña vencida**: usar "Restablecer mi acceso".
- **Contraseña vulnerable (cambio obligatorio)**: definir una nueva contraseña según la política; opcionalmente ver la guía en video.
- **Frecuencia de cambio**: la política exige cambiar la contraseña cada 180 días (aprox. 6 meses).
- **Política de contraseña**: mínimo 12 caracteres, combinar mayúsculas, minúsculas, números y símbolos, sin espacios, no reutilizar una contraseña anterior de la Universidad, no usar el nombre ni la fecha de nacimiento.
- **Enlaces oficiales usados en este flujo**: `https://cuenta.uniandes.edu.co/`, `https://mysignins.microsoft.com/security-info/password/change`, `https://mysignins.microsoft.com/security-info`, `https://myaccount.microsoft.com/device-list`, `https://www.youtube.com/watch?v=Xi_NRQYRJF8`.
- **Canales oficiales**: WhatsApp Séneca Bot `https://wa.me/573058091304?text=Quiero%20hablar%20con%20un%20agente%20de%20tecnolog%C3%ADa`, correo `servicioalclientedsit@uniandes.edu.co`, teléfono `(601) 339 4949 Ext. 3333`, horario L–V 6:30 a.m.–6:30 p.m. y S 8:00 a.m.–12:00 m (UTC-5).

## 🔒 Bloque de blindaje (reglas y límites)

- El agente responde **únicamente** sobre los cinco temas listados en "Proyecto". Cualquier otra pregunta se rechaza con amabilidad y se redirige a canales oficiales.
- El agente usa **solo** la información recuperada de los documentos de la KB (RAG). No debe responder desde el conocimiento general del modelo.
- **No inventar, modificar ni deducir** direcciones web, nombres de botones o rutas de navegación. No incluir ejemplos, enlaces ficticios ni formatos de demostración.
- Si la KB no contiene un enlace para algo, el agente **no menciona ningún enlace** en esa respuesta.
- Si la pregunta corresponde a un documento placeholder, el agente dice que no tiene esa información confirmada todavía y deriva a canales oficiales.
- Nunca solicita ni almacena contraseñas, códigos de verificación ni información personal identificable (PII). Si el usuario los envía, el agente **detiene la respuesta**, advierte que no debe compartir esos datos, y continúa sin haberlos registrado ni reenviado al modelo.

## 🗣️ Estilo y lenguaje

- Voz: **tú** — institucional, cercano, claro, empático.
- Brevedad: máximo **90 palabras por turno**. Oraciones cortas.
- Sin tecnicismos innecesarios.
- Responder siempre en español.

## 🗨️ Modo conversacional (obligatorio)

- El diálogo es natural y pausado: no se entrega toda la solución en un solo turno si la consulta es ambigua.
- Si la consulta no es clara, el agente **pregunta** antes de responder, hasta tener suficiente información para resolverla con la KB (por ejemplo: ¿puedes iniciar sesión actualmente? ¿ya intentaste restablecer el acceso? ¿tu pregunta es sobre A2P o sobre contraseña?).
- No acumular más de una o dos preguntas de aclaración seguidas; si tras eso sigue sin quedar claro, derivar a canales oficiales en vez de seguir preguntando.

## Arquitectura del prototipo

**RAG sobre los 4 documentos**, con verificación posterior a la generación.

```
kb/                     # los 4 documentos fuente (.md), uno real + tres placeholder
ingest/                 # script de carga, troceo (chunking) y construcción del índice vectorial
  build_index.py
rag/
  retriever.py          # embeddings + vectorstore + búsqueda
  chain.py              # cadena LangChain: retriever -> prompt -> Ollama (llama3.2) -> respuesta
  guardrails.py         # filtro de entrada (PII/credenciales) y verificación posterior (citas y enlaces)
app/
  gradio_app.py         # interfaz de chat en Gradio
tests/
  test_guardrails.py
  test_retrieval.py
  test_flujos.py        # casos de ejemplo por tema, incluidos los placeholder
CLAUDE.md
requirements.txt
```

### Componentes

- **LangChain**: orquesta la cadena RAG — carga de documentos (`DirectoryLoader` o loaders simples de Markdown), troceo (`RecursiveCharacterTextSplitter`), vectorstore local (Chroma o FAISS, a elegir en la Fase 0), prompt con instrucciones del bloque de blindaje, y la llamada al LLM.
- **Ollama**: ejecuta el modelo de embeddings (por ejemplo `nomic-embed-text`) y el modelo de generación **`llama3.2` (3B)**, ambos locales. El nombre de cada modelo va en una variable de configuración, no hardcodeado.
- **Gradio**: interfaz de chat local (`gr.ChatInterface` o similar) que muestra la conversación y, en un panel o acordeón opcional, los fragmentos de la KB recuperados para esa respuesta (ayuda a auditar la demo).

### Control de alucinaciones — verificación estricta

Después de que el modelo genera una respuesta, antes de mostrarla:

1. Extraer cualquier URL, teléfono, correo o nombre de botón/paso citado en la respuesta.
2. Verificar que cada uno aparezca **literalmente** en los fragmentos de la KB recuperados para esa consulta (no en la KB completa, para evitar mezclar temas).
3. Si algo no coincide: eliminar ese dato de la respuesta y, si la respuesta queda incompleta o vacía, sustituirla por un mensaje que derive a canales oficiales.
4. Registrar (log local, no persistente entre sesiones) cuándo ocurrió una corrección, para revisar qué tan seguido falla el modelo.

Esta verificación es un paso de código explícito en `guardrails.py`, no solo una instrucción en el prompt.

### Filtro de entrada (seguridad)

- Antes de enviar el mensaje del usuario al LLM, revisar si contiene un patrón de contraseña, un código de 6 dígitos, o PII evidente (número de documento, fecha de nacimiento con contexto de identidad).
- Si lo contiene: no enviar ese mensaje al modelo. Responder con la advertencia de seguridad y pedir que reformule sin esos datos.

## Stack y comandos

```bash
pip install -r requirements.txt
ollama pull llama3.2
ollama pull nomic-embed-text
python ingest/build_index.py      # construye el índice vectorial desde kb/
python app/gradio_app.py          # levanta la demo en http://127.0.0.1:7860
pytest                            # pruebas (las marcadas `ollama` se saltan solo si Ollama o el índice no están)
pytest -m "not ollama"            # solo las que no necesitan Ollama
pytest tests/test_guardrails.py::test_nombre   # una sola prueba
```

- Python 3.11+, LangChain, Ollama (servido localmente, `http://localhost:11434`), Gradio.
- Vectorstore: Chroma (decidido).

## Convenciones para editar la KB

- No modificar el contenido transcrito de Flujo 2 sin indicar explícitamente el cambio y su motivo.
- Los tres documentos placeholder deben conservar la marca `[PLACEHOLDER]` hasta que se reemplacen con el contenido oficial.
- Cualquier dato de contacto (teléfono, correo, horario) vive en un solo lugar dentro de `kb/` y se referencia desde los demás documentos, no se duplica.
- Después de reemplazar un placeholder, reconstruir el índice vectorial (`python ingest/build_index.py`) antes de probar.

## Pruebas mínimas

- Un caso por cada uno de los cinco temas del alcance, incluidos los que dependen de documentos placeholder (deben derivar a canales oficiales, no alucinar).
- Un caso de mensaje con contraseña o código: debe bloquearse antes de llegar al LLM.
- Un caso de pregunta fuera de alcance (por ejemplo, horario de biblioteca): debe rechazarse y derivar.
- Un caso donde el modelo "alucina" un enlace a propósito (se puede forzar con un prompt de prueba) para confirmar que `guardrails.py` lo elimina.
- Verificar que ninguna respuesta exceda claramente las 90 palabras de forma sistemática (revisión manual sobre el set de pruebas).

## Puntos abiertos

1. **Archivos reales de Flujo 1, 3 y 4**: pendientes de compartir. Sin ellos, el prototipo solo puede demostrarse de forma completa para el tema de contraseña (Flujo 2).
2. **Umbral `MAX_DISTANCE`**: calibrado con 7 consultas; las distancias de fuera de alcance (0.40–0.45) y las de dentro (0.29–0.37) casi se solapan. Revisar con consultas reales.
3. **Definición de "consulta no clara"**: afinar con ejemplos reales qué dispara una pregunta de aclaración versus una respuesta directa.
4. **Persistencia**: este prototipo no guarda conversaciones entre sesiones; confirmar si eso debe cambiar para una siguiente etapa.

## Flujo de trabajo para Claude Code

- Trabajar por fases: estructura del repo y KB (con placeholders) → ingesta e índice vectorial → cadena RAG con Ollama → guardrails de entrada y verificación posterior → interfaz Gradio → pruebas.
- Antes de escribir una respuesta de ejemplo para un tema placeholder, señalar explícitamente que es un placeholder y no contenido oficial.
- No eliminar el paso de verificación posterior a la generación para "simplificar" el prototipo; es el control central contra alucinaciones.
- No agregar dependencias nuevas sin justificarlas en el mensaje de cambio.