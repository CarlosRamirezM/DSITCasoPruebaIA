"""Configuración del prototipo. Los modelos y la URL de Ollama vienen de variables de entorno."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / "kb"
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", ROOT / ".chroma"))
COLLECTION = "kb_cuenta"

LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

TOP_K = int(os.getenv("TOP_K", "4"))
# Distancia coseno máxima del mejor fragmento para considerar la consulta dentro del alcance.
MAX_DISTANCE = float(os.getenv("MAX_DISTANCE", "0.39"))
MAX_WORDS = int(os.getenv("MAX_WORDS", "90"))
# Aclaraciones consecutivas permitidas antes de derivar a canales oficiales.
MAX_CLARIFICATIONS = 2

PLACEHOLDER_MARK = "[PLACEHOLDER"
