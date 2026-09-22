"""Pruebas del orquestador multi-agente."""

import pytest

from agents.herramientas_analisis import (
    calculadora,
    calcular_indicadores_mantenimiento,
)
from agents.herramientas_investigacion import consultar_historico_fallas
from graph import construir_grafo, enrutar, estado_inicial


def test_historico_devuelve_datos_de_equipo_conocido() -> None:
    """El investigador obtiene el historico de un equipo cargado."""
    resultado = consultar_historico_fallas.invoke({"equipo_id": "C-02"})
    assert "7200" in resultado
    assert "850" in resultado


def test_historico_informa_equipo_inexistente_sin_romper() -> None:
    """Ante un codigo invalido devuelve un mensaje util, no una excepcion."""
    resultado = consultar_historico_fallas.invoke({"equipo_id": "Z-99"})
    assert "No hay historico" in resultado
    assert "C-02" in resultado


def test_calculadora_resuelve_aritmetica() -> None:
    """La calculadora evalua expresiones matematicas validas."""
    assert "1200" in calculadora.invoke({"expresion": "7200 / 6"})


def test_calculadora_rechaza_codigo_arbitrario() -> None:
    """La calculadora no ejecuta nada que no sea aritmetica pura."""
    resultado = calculadora.invoke({"expresion": "__import__('os').system('dir')"})
    assert "Error" in resultado


def test_indicadores_calculan_mtbf_y_disponibilidad() -> None:
    """Los indicadores de mantenimiento se calculan correctamente."""
    resultado = calcular_indicadores_mantenimiento.invoke(
        {
            "horas_operacion": 7200,
            "cantidad_fallas": 6,
            "horas_parada_total": 48,
            "costo_hora_parada_usd": 850,
        }
    )
    assert "1200.0" in resultado
    assert "99.34" in resultado
    assert "baja" in resultado


def test_indicadores_evitan_division_por_cero() -> None:
    """Sin fallas registradas no se intenta dividir por cero."""
    resultado = calcular_indicadores_mantenimiento.invoke(
        {
            "horas_operacion": 7200,
            "cantidad_fallas": 0,
            "horas_parada_total": 0,
            "costo_hora_parada_usd": 850,
        }
    )
    assert "No se puede calcular" in resultado


@pytest.mark.parametrize(
    "decision, nodo_esperado",
    [
        ("investigador", "investigador"),
        ("analista", "analista"),
        ("FINISH", "sintesis"),
    ],
)
def test_enrutar_mapea_la_decision_al_nodo(decision: str, nodo_esperado: str) -> None:
    """El router traduce la decision del supervisor al nodo correspondiente."""
    assert enrutar({"next_agent": decision}) == nodo_esperado


def test_estado_inicial_arranca_vacio_y_en_cero() -> None:
    """El estado de arranque no trae contribuciones ni pasos previos."""
    estado = estado_inicial("consulta de prueba")
    assert estado["contribuciones"] == []
    assert estado["pasos"] == 0
    assert estado["task_completed"] is False


def test_grafo_tiene_los_cuatro_nodos() -> None:
    """El grafo compilado incluye supervisor, especialistas y sintesis."""
    nodos = construir_grafo().get_graph().nodes
    for nombre in ("supervisor", "investigador", "analista", "sintesis"):
        assert nombre in nodos