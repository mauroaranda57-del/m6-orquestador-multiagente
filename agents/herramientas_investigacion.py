"""Herramientas del agente investigador: consulta al RAG de planta y al historico."""

from langchain_core.tools import tool

HISTORICO_FALLAS: dict[str, dict[str, object]] = {
    "C-02": {
        "equipo": "Compresor de tornillo C-02",
        "periodo": "ultimos 12 meses",
        "horas_operacion": 7200,
        "cantidad_fallas": 6,
        "horas_parada_total": 48,
        "costo_hora_parada_usd": 850,
    },
    "B-07": {
        "equipo": "Bomba centrifuga B-07",
        "periodo": "ultimos 12 meses",
        "horas_operacion": 8000,
        "cantidad_fallas": 2,
        "horas_parada_total": 9,
        "costo_hora_parada_usd": 320,
    },
}


@tool
def consultar_historico_fallas(equipo_id: str) -> str:
    """Devuelve el historico de fallas y paradas de un equipo de planta.

    Usar cuando haga falta conocer cuantas fallas tuvo un equipo, cuantas horas
    estuvo parado, cuantas horas opero o cuanto cuesta su hora de indisponibilidad.
    El parametro equipo_id es el codigo del equipo en planta, por ejemplo 'C-02'
    o 'B-07'. Devuelve horas de operacion, cantidad de fallas, horas de parada
    acumuladas y costo por hora de parada en dolares.
    """
    clave = equipo_id.strip().upper()
    datos = HISTORICO_FALLAS.get(clave)
    if datos is None:
        disponibles = ", ".join(HISTORICO_FALLAS.keys())
        return (
            f"No hay historico cargado para el equipo '{equipo_id}'. "
            f"Los equipos con historico disponible son: {disponibles}."
        )
    return (
        f"Equipo {clave} ({datos['equipo']}) | Periodo: {datos['periodo']} | "
        f"Horas de operacion: {datos['horas_operacion']} | "
        f"Cantidad de fallas: {datos['cantidad_fallas']} | "
        f"Horas de parada acumuladas: {datos['horas_parada_total']} | "
        f"Costo por hora de parada: USD {datos['costo_hora_parada_usd']}"
    )


HERRAMIENTAS_INVESTIGACION = [consultar_historico_fallas]