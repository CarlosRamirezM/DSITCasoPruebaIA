"""Carga kb/*.md, trocea y reconstruye el índice vectorial Chroma desde cero."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag import config
from rag.retriever import get_embeddings


def load_documents() -> list[Document]:
    docs = []
    for path in sorted(config.KB_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        docs.append(
            Document(
                page_content=text,
                metadata={"source": path.name, "is_placeholder": config.PLACEHOLDER_MARK in text},
            )
        )
    return docs


def main() -> None:
    docs = load_documents()
    if not docs:
        sys.exit(f"No hay documentos .md en {config.KB_DIR}")

    # Separa primero por viñetas para no partir enlaces ni pasos a la mitad.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700, chunk_overlap=0, separators=["\n- ", "\n\n", "\n", " "]
    )
    chunks = splitter.split_documents(docs)

    # Reconstruir desde cero sin borrar la carpeta: en Windows/OneDrive otro proceso (la app
    # de Gradio, el sincronizador) puede tener archivos abiertos y rmtree falla con "Acceso denegado".
    if config.CHROMA_DIR.exists():
        Chroma(
            collection_name=config.COLLECTION,
            embedding_function=get_embeddings(),
            persist_directory=str(config.CHROMA_DIR),
        ).delete_collection()

    Chroma.from_documents(
        chunks,
        get_embeddings(),
        collection_name=config.COLLECTION,
        persist_directory=str(config.CHROMA_DIR),
        collection_metadata={"hnsw:space": "cosine"},
    )
    placeholders = sum(d.metadata["is_placeholder"] for d in docs)
    print(f"Índice construido: {len(docs)} documentos ({placeholders} placeholder), {len(chunks)} fragmentos.")


if __name__ == "__main__":
    main()
