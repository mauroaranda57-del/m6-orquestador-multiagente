"""Esquema de estado compartido entre el supervisor y los agentes especialistas."""

import operator
from typing import Annotated, Optional, TypedDict

from langgraph.graph import MessagesState


class Contribucion(TypedDict):
    """Un aporte individual de un agente especialista."""

    agente: str
    aporte: str


class EstadoOrquestador(MessagesState):
    """Estado compartido del sistema multi-agente.

    Hereda `messages` de MessagesState (con su reducer `add_messages`) y suma:

    - `next_agent`: a quien delega el supervisor en el proximo paso.
    - `contribuciones`: registro acumulado de que agente aporto que dato. Usa
      `operator.add` como reducer, de modo que cada nodo suma su aporte a la
      lista en lugar de pisarla. Esto es lo que evita la perdida de contexto
      entre agentes.
    - `pasos`: contador de delegaciones, para cortar bucles infinitos.
    - `task_completed`: bandera que el supervisor levanta al validar el cierre.
    """

    next_agent: Optional[str]
    contribuciones: Annotated[list[Contribucion], operator.add]
    pasos: int
    task_completed: bool