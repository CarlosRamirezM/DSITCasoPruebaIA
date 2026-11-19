"""Casos por tema. Los marcados `ollama` usan el modelo real; el resto usa dobles de prueba."""
import pytest

from rag import guardrails
from rag.chain import answer
from rag.retriever import Fragment

REAL = Fragment(
    "Restablecer mi acceso: ir a `https://cuenta.uniandes.edu.co` → \"Restablecer mi acceso\".",
    "Flujo_2.md", False, 0.30,
)
PLACE = Fragment("[PLACEHOLDER] sin contenido", "Flujo_3.md", True, 0.30)


def boom(*_):
    raise AssertionError("el mensaje no debía llegar al LLM")


# ------------------------------------------------------------ sin Ollama (dobles)

def test_mensaje_con_contrasena_se_bloquea_antes_del_llm():
    r = answer("mi contraseña es Secreta123", retrieve_fn=boom, llm_fn=boom)
    assert r.route == "bloqueado" and "Secreta123" not in r.text


def test_mensaje_con_codigo_se_bloquea_antes_del_llm():
    assert answer("me llegó el 123456", retrieve_fn=boom, llm_fn=boom).route == "bloqueado"


@pytest.mark.parametrize(
    "pregunta",
    ["¿cómo configuro Microsoft Authenticator?", "quiero cambiar mi correo alterno", "configurar mis métodos de inicio de sesión"],
)
def test_temas_placeholder_derivan_sin_llamar_al_llm(pregunta):
    r = answer(pregunta, retrieve_fn=boom, llm_fn=boom)
    assert r.route == "placeholder"
    assert "servicioalclientedsit@uniandes.edu.co" in r.text


def test_fuera_de_alcance_se_rechaza():
    far = Fragment("x", "Flujo_2.md", False, 0.9)
    r = answer("horario de la biblioteca", retrieve_fn=lambda q: [far], llm_fn=boom)
    assert r.route == "fuera_de_alcance"


def test_enlace_alucinado_por_el_modelo_se_elimina():
    fake = lambda *_: "Entra a https://cuenta.uniandes.edu.co o a https://inventado.test/reset ahora mismo."
    r = answer("olvidé mi contraseña", retrieve_fn=lambda q: [REAL], llm_fn=fake)
    assert "inventado.test" not in r.text and "cuenta.uniandes.edu.co" in r.text
    assert r.corrections


def test_respuesta_solo_alucinada_se_sustituye():
    r = answer("olvidé mi contraseña", retrieve_fn=lambda q: [REAL], llm_fn=lambda *_: "https://inventado.test/x")
    assert r.route == "derivado" and "inventado" not in r.text


def test_tras_dos_aclaraciones_deriva_en_vez_de_preguntar_otra_vez():
    hist = [
        {"role": "user", "content": "ayuda"}, {"role": "assistant", "content": "¿Sobre qué tema?"},
        {"role": "user", "content": "no sé"}, {"role": "assistant", "content": "¿Puedes iniciar sesión?"},
    ]
    r = answer("no sé", hist, retrieve_fn=lambda q: [REAL], llm_fn=lambda *_: "¿Y qué intentaste?")
    assert r.route == "derivado" and not r.text.endswith("?")


# ------------------------------------------------------------ con Ollama (modelo real)

@pytest.mark.ollama
def test_contrasena_olvidada_con_modelo_real():
    r = answer("Olvidé mi contraseña y no puedo entrar, ¿qué hago?")
    assert r.route in {"llm", "derivado"}
    guardrails.check_length(r.text)
    # Todo enlace en la respuesta debe estar en los fragmentos recuperados.
    ctx = " ".join(f.text for f in r.fragments)
    for url in guardrails._URL.findall(r.text):
        assert guardrails._strip(url) in ctx


@pytest.mark.ollama
def test_fuera_de_alcance_con_modelo_real():
    r = answer("¿A qué hora abre la biblioteca?")
    assert r.route == "fuera_de_alcance" or "biblioteca" not in r.text.lower() or "canales" in r.text.lower()


@pytest.mark.ollama
def test_longitud_de_respuestas_reales():
    for q in ["¿Cada cuánto debo cambiar mi contraseña?", "¿Cuál es la política de contraseña?"]:
        r = answer(q)
        assert len(r.text.split()) <= int(guardrails.config.MAX_WORDS * 1.5), r.text
