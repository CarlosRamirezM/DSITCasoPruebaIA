"""Cadena RAG: ruteo determinista -> retriever -> prompt -> Ollama -> verificación posterior."""
import re
from dataclasses import dataclass, field
from typing import Callable

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama

from rag import config, guardrails
from rag.retriever import Fragment, official_channels, retrieve

SYSTEM_PROMPT = """Eres el Agente de IA Cuenta de la DSIT de la Universidad de los Andes.

ALCANCE: solo respondes sobre: contraseña (cambio, vencimiento, olvido, restablecer acceso), \
autenticación en dos pasos (A2P), cuenta de correo Uniandes, correo alterno y seguridad de la \
cuenta (métodos de inicio de sesión). Cualquier otra pregunta se rechaza con amabilidad y se \
redirige a los canales oficiales.

REGLAS:
- Usa ÚNICAMENTE la información del CONTEXTO. No uses conocimiento general.
- No inventes, modifiques ni deduzcas direcciones web, nombres de botones o rutas. Copia los \
enlaces y nombres tal como aparecen en el CONTEXTO.
- Si el CONTEXTO no trae un enlace para algo, no menciones ningún enlace.
- Si el CONTEXTO no responde la pregunta, di que no tienes esa información y deriva a canales oficiales.
- Nunca pidas contraseñas, códigos de verificación ni datos personales.

ESTILO: responde siempre en español, tratando de "tú", con tono institucional, cercano y empático. \
Máximo 90 palabras. Oraciones cortas, sin tecnicismos.

MODO CONVERSACIONAL: si la consulta es ambigua, haz UNA pregunta corta de aclaración en lugar de \
dar toda la solución (por ejemplo: ¿puedes iniciar sesión actualmente?). No repitas preguntas que \nel usuario ya respondió. {clarification_rule}

CONTEXTO:
{context}"""

NO_MORE_QUESTIONS = (
    "Ya hiciste varias aclaraciones: NO hagas más preguntas. Si no puedes resolver con el "
    "CONTEXTO, deriva a los canales oficiales."
)
ALLOW_QUESTION = "Puedes hacer una pregunta de aclaración si hace falta."

# Temas cuyo documento aún es placeholder. Se detectan por palabras clave en código para no
# depender del modelo (la similitud de embeddings no los separa bien del Flujo 2).
_PLACEHOLDER_TOPICS = re.compile(
    r"a2p|autenticaci[oó]n|authenticator|dos pasos|verificaci[oó]n en dos|"
    r"correo alterno|correo alternativo|correo secundario|cuenta de correo|mi correo|"
    r"m[eé]todos? de (inicio de )?sesi[oó]n|seguridad de (la|mi) cuenta|"
    r"configurar (la )?seguridad",
    re.I,
)
_PASSWORD_TOPIC = re.compile(r"contrase[ñn]a|clave|restablec|olvid|venci|cambiar mi acceso", re.I)


@dataclass
class Result:
    text: str
    fragments: list[Fragment] = field(default_factory=list)
    route: str = "llm"  # llm | bloqueado | placeholder | fuera_de_alcance | derivado
    corrections: list[str] = field(default_factory=list)


def _referral() -> str:
    return f"Puedes contactar los canales oficiales: {official_channels()}"


def _placeholder_reply() -> str:
    return "Aún no tengo esa información confirmada. " + _referral()


def _out_of_scope_reply() -> str:
    return "Solo puedo ayudarte con tu cuenta Uniandes: contraseña, A2P, correo y seguridad. " + _referral()


def _text(content) -> str:
    if isinstance(content, list):
        return " ".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return str(content or "")


def _trailing_clarifications(history: list[dict]) -> int:
    n = 0
    for msg in reversed([m for m in history if m.get("role") == "assistant"]):
        if _text(msg["content"]).strip().endswith("?"):
            n += 1
        else:
            break
    return n


def _default_llm(system: str, history: list[dict], question: str) -> str:
    prompt = ChatPromptTemplate.from_messages(
        [("system", "{system}"), MessagesPlaceholder("history"), ("human", "{question}")]
    )
    llm = ChatOllama(model=config.LLM_MODEL, base_url=config.OLLAMA_URL, temperature=0.1)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"system": system, "history": history, "question": question})


def answer(
    message: str,
    history: list[dict] | None = None,
    *,
    retrieve_fn: Callable[[str], list[Fragment]] = retrieve,
    llm_fn: Callable[[str, list[dict], str], str] = _default_llm,
) -> Result:
    """`history`: lista de {"role": "user"|"assistant", "content": str}, sin el mensaje actual."""
    history = [{"role": m["role"], "content": _text(m["content"])} for m in (history or [])]

    # 1) Filtro de entrada: el mensaje no llega al retriever ni al modelo.
    kind = guardrails.check_input(message)
    if kind:
        return Result(guardrails.WARNING_INPUT, route="bloqueado")

    # 2) Ruteo determinista por tema placeholder.
    if _PLACEHOLDER_TOPICS.search(message) and not _PASSWORD_TOPIC.search(message):
        return Result(_placeholder_reply(), route="placeholder")

    # 3) Recuperación. Los mensajes muy cortos ("sí", "no puedo") son seguimientos: se
    #    recupera con el último mensaje previo del usuario; los demás se buscan solos para
    #    que un tema anterior no contamine una pregunta nueva (p. ej. fuera de alcance).
    prev_user = [m["content"] for m in history if m["role"] == "user"][-1:]
    short = len(message.split()) <= 3
    fragments = retrieve_fn(" ".join(prev_user + [message]) if short else message)
    if not fragments or fragments[0].distance > config.MAX_DISTANCE:
        return Result(_out_of_scope_reply(), fragments, route="fuera_de_alcance")
    if fragments[0].is_placeholder:
        return Result(_placeholder_reply(), fragments, route="placeholder")

    # 4) Generación con el contexto recuperado (sin fragmentos placeholder).
    usable = [f for f in fragments if not f.is_placeholder]
    context = "\n\n".join(f.text for f in usable)
    capped = _trailing_clarifications(history) >= config.MAX_CLARIFICATIONS
    system = SYSTEM_PROMPT.format(
        context=context, clarification_rule=NO_MORE_QUESTIONS if capped else ALLOW_QUESTION
    )
    raw = llm_fn(system, history, message).strip()

    # 5) Verificación posterior (control central contra alucinaciones).
    verified = guardrails.verify_output(raw, context, fallback=_referral())
    text = verified.text
    route = "derivado" if verified.replaced else "llm"
    if capped and text.endswith("?"):
        text, route = _referral(), "derivado"
    guardrails.check_length(text)
    return Result(text, fragments, route, verified.removed)
