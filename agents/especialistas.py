"""Definicion de los dos agentes especialistas del orquestador."""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

import config
from agents.herramientas_analisis import HERRAMIENTAS_ANALISIS
from agents.herramientas_investigacion import HERRAMIENTAS_INVESTIGACION

PROMPT_INVESTIGADOR = (
    "Sos el agente investigador de un equipo de ingenieria de mantenimiento. "
    "Tu unica funcion es obtener datos concretos del historico de los equipos de "
    "planta usando tus herramientas. NO hagas calculos ni interpretes indicadores: "
    "de eso se encarga el analista. Respondes en espanol, en una sola linea, "
    "listando los datos crudos que encontraste."
)

PROMPT_ANALISTA = (
    "Sos el agente analista de un equipo de ingenieria de mantenimiento. "
    "Tu unica funcion es calcular indicadores a partir de datos que ya te dieron: "
    "MTBF, MTTR, disponibilidad, costo de indisponibilidad y criticidad. "
    "NO busques informacion nueva: si te falta un dato, decilo explicitamente. "
    "Respondes en espanol, en una sola linea, con los valores obtenidos."
)


def construir_llm() -> ChatGoogleGenerativeAI:
    """Instancia el modelo de Gemini usado por todos los nodos del grafo."""
    return ChatGoogleGenerativeAI(
        model=config.MODEL_NAME,
        google_api_key=config.GEMINI_API_KEY,
    )


def construir_agente_investigador():
    """Agente ReAct acotado a las herramientas de consulta de historico."""
    return create_react_agent(
        model=construir_llm(),
        tools=HERRAMIENTAS_INVESTIGACION,
        prompt=PROMPT_INVESTIGADOR,
    )


def construir_agente_analista():
    """Agente ReAct acotado a las herramientas de calculo."""
    return create_react_agent(
        model=construir_llm(),
        tools=HERRAMIENTAS_ANALISIS,
        prompt=PROMPT_ANALISTA,
    )