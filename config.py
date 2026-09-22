"""Configuración central del orquestador: carga y valida variables de entorno."""

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY: str | None = os.getenv("PINECONE_API_KEY")

MODEL_NAME: str = "gemini-3.6-flash"
INDEX_NAME: str = "planta-docs"
NAMESPACE: str = "manuales"

MAX_PASOS: int = 6
RECURSION_LIMIT: int = 15


def validar_entorno() -> None:
    """Corta la ejecución al arranque si falta alguna variable obligatoria."""
    faltantes: list[str] = [
        nombre
        for nombre, valor in (
            ("GEMINI_API_KEY", GEMINI_API_KEY),
            ("PINECONE_API_KEY", PINECONE_API_KEY),
        )
        if not valor
    ]
    if faltantes:
        raise RuntimeError(
            f"Faltan variables de entorno en el archivo .env: {', '.join(faltantes)}"
        )


validar_entorno()