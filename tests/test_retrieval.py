import pytest

from rag.retriever import official_channels, retrieve

pytestmark = pytest.mark.ollama


def test_consulta_de_contrasena_recupera_flujo_2():
    frags = retrieve("olvidé mi contraseña")
    assert frags[0].source.startswith("Flujo_2")
    assert not frags[0].is_placeholder


def test_politica_de_contrasena():
    frags = retrieve("cada cuánto debo cambiar la clave")
    assert any("180 días" in f.text for f in frags)


def test_placeholders_marcados_en_metadatos():
    frags = retrieve("autenticación en dos pasos", k=7)
    assert any(f.is_placeholder for f in frags)


def test_canales_oficiales_vienen_de_la_kb():
    assert "servicioalclientedsit@uniandes.edu.co" in official_channels()
