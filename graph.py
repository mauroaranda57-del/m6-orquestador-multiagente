"""Orquestador multi-agente con topologia jerarquica supervisor -> especialistas."""

from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

import config
from agents.especialistas import (
    construir_agente_analista,
    construir_agente_investigador,
    construir_llm,
)
from state import EstadoOrquestador

SUPERVISOR_PROMPT = """Sos el Supervisor de un equipo de ingenieria de mantenimiento
con dos especialistas a cargo:

- investigador: obtiene el historico de fallas y paradas de un equipo de planta.
- analista: calcula MTBF, MTTR, disponibilidad, costo de indisponibilidad y criticidad
  a partir de datos que ya fueron obtenidos.

Rubrica de validacion. Antes de responder FINISH, verifica que se cumplan TODAS estas
condiciones:
1. El investigador ya aporto el historico del equipo consultado (horas de operacion,
   cantidad de fallas, horas de parada y costo por hora).
2. El analista ya aporto los indicadores calculados, incluyendo disponibilidad y
   criticidad.
3. Ningun aporte contiene un mensaje de error o de dato faltante.

Reglas de delegacion:
- Si falta el historico del equipo, delega en 'investigador'.
- Si el historico ya esta pero faltan los indicadores, delega en 'analista'.
- Si un especialista devolvio un error o un dato incompleto, volve a delegarle la tarea
  una sola vez, indicando que dato falta.
- Si se cumplen las tres condiciones de la rubrica, respondes 'FINISH'.
- Nunca delegues dos veces seguidas en el mismo agente si ya cumplio su parte.

Contribuciones registradas hasta ahora:
{contribuciones}
"""


class DecisionSupervisor(BaseModel):
    """Salida estructurada del supervisor: a quien delega y por que."""

    next: Literal["investigador", "analista", "FINISH"] = Field(
        description="Proximo agente a invocar, o FINISH si la tarea esta completa"
    )
    razon: str = Field(description="Breve justificacion de la decision tomada")


def _formatear_contribuciones(state: EstadoOrquestador) -> str:
    """Arma el resumen de aportes que el supervisor usa para decidir."""
    contribuciones = state.get("contribuciones", [])
    if not contribuciones:
        return "(ninguna todavia)"
    return "\n".join(f"- {c['agente']}: {c['aporte']}" for c in contribuciones)


def nodo_supervisor(state: EstadoOrquestador) -> dict:
    """Router inteligente: valida la rubrica y decide el proximo paso."""
    if state.get("pasos", 0) >= config.MAX_PASOS:
        return {
            "next_agent": "FINISH",
            "task_completed": True,
            "messages": [
                AIMessage(
                    content=(
                        f"Se alcanzo el limite de {config.MAX_PASOS} delegaciones. "
                        "Se cierra con la informacion disponible."
                    ),
                    name="supervisor",
                )
            ],
        }

    llm_estructurado = construir_llm().with_structured_output(DecisionSupervisor)
    pregunta_original = state["messages"][0].content

    decision = llm_estructurado.invoke(
        [
            {
                "role": "system",
                "content": SUPERVISOR_PROMPT.format(
                    contribuciones=_formatear_contribuciones(state)
                ),
            },
            {"role": "user", "content": f"Consulta original: {pregunta_original}"},
        ]
    )

    return {
        "next_agent": decision.next,
        "task_completed": decision.next == "FINISH",
        "messages": [
            AIMessage(
                content=f"[Supervisor -> {decision.next}] {decision.razon}",
                name="supervisor",
            )
        ],
    }


def nodo_investigador(state: EstadoOrquestador) -> dict:
    """Ejecuta al investigador con contexto acotado a la consulta original."""
    agente = construir_agente_investigador()
    tarea = state["messages"][0].content
    resultado = agente.invoke({"messages": [HumanMessage(content=tarea)]})
    respuesta = resultado["messages"][-1].content

    return {
        "messages": [AIMessage(content=respuesta, name="investigador")],
        "contribuciones": [{"agente": "investigador", "aporte": respuesta}],
        "pasos": state.get("pasos", 0) + 1,
    }


def nodo_analista(state: EstadoOrquestador) -> dict:
    """Ejecuta al analista pasandole solo la consulta y los datos ya recolectados."""
    agente = construir_agente_analista()
    datos = _formatear_contribuciones(state)
    tarea = (
        f"Consulta original: {state['messages'][0].content}\n\n"
        f"Datos aportados por el equipo:\n{datos}\n\n"
        "Calcula los indicadores de mantenimiento con estos datos."
    )
    resultado = agente.invoke({"messages": [HumanMessage(content=tarea)]})
    respuesta = resultado["messages"][-1].content

    return {
        "messages": [AIMessage(content=respuesta, name="analista")],
        "contribuciones": [{"agente": "analista", "aporte": respuesta}],
        "pasos": state.get("pasos", 0) + 1,
    }


def nodo_sintesis(state: EstadoOrquestador) -> dict:
    """Fase final: combina los aportes en una recomendacion para el supervisor."""
    prompt = (
        f"Consulta original: {state['messages'][0].content}\n\n"
        f"Aportes del equipo:\n{_formatear_contribuciones(state)}\n\n"
        "Redacta la respuesta final para un supervisor de mantenimiento: breve, "
        "con los indicadores obtenidos y una recomendacion operativa concreta. "
        "Responde en espanol."
    )
    respuesta = construir_llm().invoke(prompt)
    return {"messages": [AIMessage(content=respuesta.content, name="sintesis")]}


def enrutar(
    state: EstadoOrquestador,
) -> Literal["investigador", "analista", "sintesis"]:
    """Arista condicional: traduce la decision del supervisor a un nodo del grafo."""
    if state.get("next_agent") == "FINISH":
        return "sintesis"
    return state["next_agent"]


def construir_grafo():
    """Arma y compila el grafo del orquestador."""
    grafo = StateGraph(EstadoOrquestador)
    grafo.add_node("supervisor", nodo_supervisor)
    grafo.add_node("investigador", nodo_investigador)
    grafo.add_node("analista", nodo_analista)
    grafo.add_node("sintesis", nodo_sintesis)

    grafo.add_edge(START, "supervisor")
    grafo.add_conditional_edges(
        "supervisor",
        enrutar,
        {
            "investigador": "investigador",
            "analista": "analista",
            "sintesis": "sintesis",
        },
    )
    grafo.add_edge("investigador", "supervisor")
    grafo.add_edge("analista", "supervisor")
    grafo.add_edge("sintesis", END)

    return grafo.compile()


def estado_inicial(consulta: str) -> dict:
    """Construye el estado de arranque para una consulta del usuario."""
    return {
        "messages": [HumanMessage(content=consulta)],
        "next_agent": None,
        "contribuciones": [],
        "pasos": 0,
        "task_completed": False,
    }