"""Filtro de entrada (credenciales/PII) y verificación posterior de la respuesta del modelo.

La verificación posterior es el control central contra alucinaciones: todo dato citado
(URL, correo, teléfono, nombre entre comillas) debe aparecer literalmente en los
fragmentos recuperados para esa consulta; si no, se elimina.
"""
import re
from dataclasses import dataclass, field

from rag import config

# --------------------------------------------------------------------------- entrada

_INPUT_PATTERNS = {
    "contraseña": re.compile(
        r"(contrase[ñn]a|clave|password|pass)\s*(actual|nueva|anterior)?\s*(es|:|=|era)\s*\S+", re.I
    ),
    "código": re.compile(r"(?<!\d)\d{6}(?!\d)"),
    "documento": re.compile(
        r"(c[eé]dula|documento|identificaci[oó]n|\bc\.?c\.?\b)\D{0,20}\d{6,12}", re.I
    ),
    "fecha de nacimiento": re.compile(
        r"(nac[ií]|nacimiento|cumplea[ñn]os)\D{0,25}\d{1,2}[/\-. ]\d{1,2}[/\-. ]\d{2,4}", re.I
    ),
}

WARNING_INPUT = (
    "Por tu seguridad, no compartas contraseñas, códigos de verificación ni datos personales "
    "(como documento o fecha de nacimiento) en este chat. No los he guardado. "
    "¿Puedes volver a escribir tu consulta sin esos datos?"
)
REDACTED_USER_MSG = "[Mensaje omitido: contenía datos sensibles]"


def check_input(text: str) -> str | None:
    """Devuelve la categoría detectada (sin el contenido) o None si el mensaje es seguro."""
    for name, pattern in _INPUT_PATTERNS.items():
        if pattern.search(text):
            return name
    return None


# --------------------------------------------------------------------------- salida

_URL = re.compile(r"https?://[^\s<>`\"']+")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PHONE = re.compile(r"\(\d{2,4}\)\s?\d{3}\s?\d{4}(?:\s?Ext\.?\s?\d+)?")
_QUOTED = re.compile(r"[\"“«]([^\"”»\n]{2,60})[\"”»]")
_TRAILING = ".,;:!?)»”\"'"

# Registro local en memoria (no persistente entre sesiones).
CORRECTIONS_LOG: list[dict] = []


@dataclass
class Verification:
    text: str
    removed: list[str] = field(default_factory=list)
    replaced: bool = False


def _strip(token: str) -> str:
    return token.rstrip(_TRAILING)


def _in_context(item: str, context: str, *, ci: bool = False) -> bool:
    if ci:
        return item.lower() in context.lower()
    return item in context


def verify_output(answer: str, context: str, fallback: str) -> Verification:
    """Elimina de `answer` todo dato que no aparezca literalmente en `context`."""
    removed: list[str] = []
    text = answer

    for kind, pattern in (("url", _URL), ("correo", _EMAIL), ("teléfono", _PHONE)):
        for match in list(pattern.finditer(text)):
            raw = match.group(0)
            item = _strip(raw)
            # Un correo dentro de una URL de la KB ya se cubre por la URL; no tratar de nuevo.
            if not _in_context(item, context):
                removed.append(f"{kind}: {item}")
                text = text.replace(raw, "")

    # Nombres de botón/paso entre comillas: se elimina toda la oración que los contiene.
    for match in list(_QUOTED.finditer(text)):
        name = match.group(1)
        if not _in_context(name, context, ci=True):
            removed.append(f"botón/paso: {name}")
            sentences = re.split(r"(?<=[.!?])\s+", text)
            text = " ".join(s for s in sentences if match.group(0) not in s)

    text = re.sub(r"[ \t]+([.,;:!?])", r"\1", text)
    text = re.sub(r"[ \t]{2,}", " ", text).strip()

    for item in removed:
        CORRECTIONS_LOG.append({"tipo": "dato_no_verificado", "detalle": item})

    replaced = False
    if removed and len(text.split()) < 4:
        text, replaced = fallback, True
        CORRECTIONS_LOG.append({"tipo": "respuesta_sustituida", "detalle": "quedó vacía/incompleta"})
    return Verification(text=text, removed=removed, replaced=replaced)


def word_count(text: str) -> int:
    return len(text.split())


def check_length(text: str) -> bool:
    """True si el texto respeta el límite de palabras. Registra la violación si no."""
    n = word_count(text)
    if n > config.MAX_WORDS:
        CORRECTIONS_LOG.append({"tipo": "excede_palabras", "detalle": f"{n} palabras"})
        return False
    return True
