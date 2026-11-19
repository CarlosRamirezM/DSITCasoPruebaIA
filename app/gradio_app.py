"""Interfaz de chat local en Gradio. Sin persistencia entre sesiones."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gradio as gr

from rag import guardrails
from rag.chain import _text, answer

AVISO = (
    "⚠️ **Prototipo.** Solo el tema de contraseña (Flujo 2) tiene contenido oficial. "
    "Correo Uniandes, correo alterno, A2P y seguridad usan documentos *placeholder*: "
    "el agente derivará a canales oficiales."
)


def _fragments_md(result) -> str:
    if not result.fragments:
        return "_Sin fragmentos para esta respuesta._"
    return "\n\n".join(
        f"**{f.source}** · distancia {f.distance:.2f}{' · PLACEHOLDER' if f.is_placeholder else ''}\n\n{f.text}"
        for f in result.fragments
    )


def _stats() -> str:
    return f"Correcciones del verificador en esta sesión: **{len(guardrails.CORRECTIONS_LOG)}**"


def respond(message: str, history: list[dict]):
    message = (message or "").strip()
    if not message:
        return "", history, gr.update(), _stats()
    history = history or []
    prior = [{"role": m["role"], "content": _text(m["content"])} for m in history]
    result = answer(message, prior)
    # Un mensaje bloqueado no se conserva en el historial.
    shown = guardrails.REDACTED_USER_MSG if result.route == "bloqueado" else message
    history = history + [
        {"role": "user", "content": shown},
        {"role": "assistant", "content": result.text},
    ]
    return "", history, _fragments_md(result), _stats()


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Agente de IA Cuenta — DSIT") as demo:
        gr.Markdown("# Agente de IA Cuenta — DSIT Uniandes")
        gr.Markdown(AVISO)
        chatbot = gr.Chatbot(height=420)
        box = gr.Textbox(placeholder="Escribe tu consulta…", show_label=False)
        stats = gr.Markdown(_stats())
        with gr.Accordion("Fragmentos de la KB recuperados (auditoría)", open=False):
            fragments = gr.Markdown()
        box.submit(respond, [box, chatbot], [box, chatbot, fragments, stats])
    return demo


if __name__ == "__main__":
    build_app().launch(server_name="127.0.0.1", server_port=7860)
