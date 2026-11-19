"""Embeddings (Ollama) + vectorstore (Chroma) + búsqueda."""
from dataclasses import dataclass

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from rag import config


@dataclass
class Fragment:
    text: str
    source: str
    is_placeholder: bool
    distance: float  # distancia coseno: menor = más parecido


def get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=config.EMBED_MODEL, base_url=config.OLLAMA_URL)


def get_store() -> Chroma:
    return Chroma(
        collection_name=config.COLLECTION,
        embedding_function=get_embeddings(),
        persist_directory=str(config.CHROMA_DIR),
        collection_metadata={"hnsw:space": "cosine"},
    )


def retrieve(query: str, k: int | None = None) -> list[Fragment]:
    results: list[tuple[Document, float]] = get_store().similarity_search_with_score(
        query, k=k or config.TOP_K
    )
    return [
        Fragment(
            text=doc.page_content,
            source=doc.metadata.get("source", "?"),
            is_placeholder=bool(doc.metadata.get("is_placeholder")),
            distance=float(score),
        )
        for doc, score in results
    ]


def official_channels() -> str:
    """Texto de 'Canales oficiales' leído de la KB (única fuente de datos de contacto)."""
    for path in sorted(config.KB_DIR.glob("*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if "**Canales oficiales**" in line:
                return line.split(":", 1)[1].strip().replace("`", "")
    return ""
