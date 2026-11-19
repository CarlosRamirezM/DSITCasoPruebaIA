import pytest

from rag import guardrails as g

CONTEXT = (
    "Ir a `https://cuenta.uniandes.edu.co` → \"Restablecer mi acceso\". "
    "Correo servicioalclientedsit@uniandes.edu.co, teléfono (601) 339 4949 Ext. 3333."
)
FALLBACK = "Contacta los canales oficiales."


@pytest.mark.parametrize(
    "texto",
    [
        "mi contraseña es Abc123xyz!",
        "la clave actual: hola1234",
        "me llegó el código 482913",
        "mi cédula es 1020304050",
        "nací el 12/03/1998",
    ],
)
def test_input_bloquea_credenciales_y_pii(texto):
    assert g.check_input(texto) is not None


@pytest.mark.parametrize(
    "texto", ["olvidé mi contraseña", "¿cada cuánto debo cambiar la contraseña?", "no me llega el código por SMS"]
)
def test_input_permite_consultas_normales(texto):
    assert g.check_input(texto) is None


def test_input_no_devuelve_el_contenido():
    assert "482913" not in (g.check_input("código 482913") or "")


def test_enlace_alucinado_se_elimina():
    out = g.verify_output(
        "Entra a https://cuenta.uniandes.edu.co o a https://falso.example.com/reset para continuar.",
        CONTEXT,
        FALLBACK,
    )
    assert "falso.example.com" not in out.text
    assert "https://cuenta.uniandes.edu.co" in out.text
    assert out.removed


def test_enlace_legitimo_con_puntuacion_se_conserva():
    out = g.verify_output("Ingresa a https://cuenta.uniandes.edu.co.", CONTEXT, FALLBACK)
    assert not out.removed and "cuenta.uniandes.edu.co" in out.text


def test_correo_y_telefono_inventados_se_eliminan():
    out = g.verify_output(
        "Escribe a soporte@uniandes.edu.co o llama al (601) 111 2222 para ayuda con tu cuenta.", CONTEXT, FALLBACK
    )
    assert "soporte@" not in out.text and "111 2222" not in out.text


def test_telefono_real_se_conserva():
    out = g.verify_output("Llama al (601) 339 4949 Ext. 3333.", CONTEXT, FALLBACK)
    assert not out.removed


def test_boton_inventado_elimina_la_oracion():
    out = g.verify_output(
        'Pulsa "Recuperar clave ya". Luego sigue las instrucciones de pantalla en tu equipo.', CONTEXT, FALLBACK
    )
    assert "Recuperar clave" not in out.text
    assert "instrucciones" in out.text


def test_respuesta_vacia_se_sustituye_por_derivacion():
    out = g.verify_output("Entra a https://inventado.test/x", CONTEXT, FALLBACK)
    assert out.replaced and out.text == FALLBACK


def test_url_de_otro_tema_no_permitida():
    ctx_otro_tema = "Texto sin enlaces."
    out = g.verify_output("Ve a https://cuenta.uniandes.edu.co para cambiarla ahora.", ctx_otro_tema, FALLBACK)
    assert "https://" not in out.text


def test_correcciones_se_registran():
    g.CORRECTIONS_LOG.clear()
    g.verify_output("Ve a https://x.test/y y luego sigue los pasos indicados.", CONTEXT, FALLBACK)
    assert g.CORRECTIONS_LOG


def test_limite_de_palabras():
    assert g.check_length("palabra " * 10)
    assert not g.check_length("palabra " * 200)
