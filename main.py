"""Punto de entrada: ejecuta el orquestador y muestra el flujo de delegacion."""

import json
from datetime import datetime
from typing import Any

from langchain_core.messages import BaseMessage

import config
from graph import construir_grafo, estado_inicial

CONSULTA = (
    "Analiza la criticidad del compresor C-02 en base a su historico del ultimo "
    "anio. Necesito los indicadores de mantenimiento y una recomendacion."
)


def texto_plano(mensaje: BaseMessage) -> str:
    """Extrae solo el texto de un mensaje, descartando metadatos internos.

    Gemini devuelve el contenido como lista de bloques, incluyendo metadata
    interna del modelo que no forma parte de la respuesta al usuario.
    """
    contenido = mensaje.content
    if isinstance(contenido, str):
        return contenido
    partes: list[str] = []
    for bloque in contenido:
        if isinstance(bloque, dict) and bloque.get("type") == "text":
            partes.append(bloque["text"])
        elif isinstance(bloque, str):
            partes.append(bloque)
    return "\n".join(partes)


def main() -> None:
    """Corre el grafo en modo streaming e imprime cada delegacion."""
    app = construir_grafo()
    inicial = estado_inicial(CONSULTA)
    configuracion = {"recursion_limit": config.RECURSION_LIMIT}
    traza: list[dict[str, Any]] = []

    print("=" * 70)
    print("CONSULTA:", CONSULTA)
    print("=" * 70)

    for evento in app.stream(inicial, config=configuracion, stream_mode="updates"):
        for nodo, actualizacion in evento.items():
            print(f"\n--- nodo: {nodo} ---")
            for mensaje in actualizacion.get("messages", []):
                contenido = texto_plano(mensaje)
                print(contenido)
                traza.append(
                    {
                        "nodo": nodo,
                        "autor": getattr(mensaje, "name", "sistema"),
                        "contenido": contenido,
                    }
                )

    salida = {
        "generado": datetime.now().isoformat(timespec="seconds"),
        "modelo": config.MODEL_NAME,
        "max_pasos": config.MAX_PASOS,
        "recursion_limit": config.RECURSION_LIMIT,
        "consulta": CONSULTA,
        "flujo": traza,
    }
    with open("traza_delegacion.json", "w", encoding="utf-8") as archivo:
        json.dump(salida, archivo, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("Traza guardada en traza_delegacion.json")


if __name__ == "__main__":
    main()