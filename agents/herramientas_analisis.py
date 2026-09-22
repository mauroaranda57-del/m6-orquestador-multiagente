"""Herramientas del agente analista: calculo seguro e indicadores de mantenimiento."""

import ast
import operator as op

from langchain_core.tools import tool

_OPERADORES = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}


def _evaluar_nodo(nodo: ast.AST) -> float:
    """Evalua recursivamente un nodo del arbol sintactico, solo aritmetica."""
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, (int, float)):
        return nodo.value
    if isinstance(nodo, ast.BinOp) and type(nodo.op) in _OPERADORES:
        return _OPERADORES[type(nodo.op)](
            _evaluar_nodo(nodo.left), _evaluar_nodo(nodo.right)
        )
    if isinstance(nodo, ast.UnaryOp) and type(nodo.op) in _OPERADORES:
        return _OPERADORES[type(nodo.op)](_evaluar_nodo(nodo.operand))
    raise ValueError("Expresion no permitida")


@tool
def calculadora(expresion: str) -> str:
    """Evalua una expresion matematica con +, -, *, /, ** y parentesis.

    Usar para cualquier calculo numerico. Ejemplo de entrada: '7200 / 6'.
    No acepta variables, funciones ni nombres: solo numeros y operadores.
    """
    try:
        resultado = _evaluar_nodo(ast.parse(expresion, mode="eval").body)
        return f"Resultado: {round(resultado, 4)}"
    except ZeroDivisionError:
        return f"Error al calcular '{expresion}': division por cero"
    except Exception as error:
        return f"Error al calcular '{expresion}': {error}"


@tool
def calcular_indicadores_mantenimiento(
    horas_operacion: float,
    cantidad_fallas: int,
    horas_parada_total: float,
    costo_hora_parada_usd: float,
) -> str:
    """Calcula los indicadores de mantenimiento de un equipo y clasifica su criticidad.

    Usar cuando ya se cuente con el historico de un equipo y haya que evaluarlo.
    Calcula MTBF (tiempo medio entre fallas), MTTR (tiempo medio de reparacion),
    disponibilidad porcentual y costo total de indisponibilidad, y devuelve una
    clasificacion de criticidad segun la disponibilidad obtenida.
    """
    if cantidad_fallas <= 0:
        return "No se puede calcular el MTBF: la cantidad de fallas debe ser mayor a cero."
    if horas_operacion <= 0:
        return "No se puede calcular: las horas de operacion deben ser mayores a cero."

    mtbf = horas_operacion / cantidad_fallas
    mttr = horas_parada_total / cantidad_fallas
    disponibilidad = horas_operacion / (horas_operacion + horas_parada_total) * 100
    costo_total = horas_parada_total * costo_hora_parada_usd

    if disponibilidad >= 99:
        criticidad = "baja"
    elif disponibilidad >= 97:
        criticidad = "media"
    else:
        criticidad = "alta"

    return (
        f"MTBF: {mtbf:.1f} h entre fallas | "
        f"MTTR: {mttr:.1f} h por reparacion | "
        f"Disponibilidad: {disponibilidad:.2f} % | "
        f"Costo de indisponibilidad: USD {costo_total:,.0f} | "
        f"Criticidad: {criticidad}"
    )


HERRAMIENTAS_ANALISIS = [calculadora, calcular_indicadores_mantenimiento]