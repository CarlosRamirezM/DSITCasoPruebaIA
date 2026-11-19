import pytest


def pytest_collection_modifyitems(config, items):
    """Salta las pruebas marcadas `ollama` si el servidor o el índice no están disponibles."""
    if not any("ollama" in i.keywords for i in items):
        return
    reason = None
    try:
        import httpx

        from rag import config as cfg

        httpx.get(f"{cfg.OLLAMA_URL}/api/tags", timeout=3).raise_for_status()
        if not cfg.CHROMA_DIR.exists():
            reason = "índice no construido (python ingest/build_index.py)"
    except Exception as exc:  # noqa: BLE001
        reason = f"Ollama no disponible: {exc.__class__.__name__}"
    if reason:
        skip = pytest.mark.skip(reason=reason)
        for item in items:
            if "ollama" in item.keywords:
                item.add_marker(skip)
