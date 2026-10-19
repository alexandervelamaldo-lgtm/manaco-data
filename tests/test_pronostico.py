"""Pruebas del servicio de pronóstico de demanda (historial simulado + ajuste informal)."""

from __future__ import annotations

import pytest

from src.services import pronostico as pr


@pytest.mark.parametrize("linea", pr.LINEAS)
def test_generar_historial_forma_y_rangos(linea):
    historial = pr.generar_historial(linea, meses=24)
    assert len(historial) == 24
    assert list(historial.columns) == ["Fecha", "Presion_informal", "Pares_vendidos"]
    assert historial["Presion_informal"].between(0, 1).all()
    assert (historial["Pares_vendidos"] > 0).all()
    assert historial["Fecha"].is_monotonic_increasing


def test_generar_historial_es_reproducible():
    a = pr.generar_historial("Deportivo", meses=12)
    b = pr.generar_historial("Deportivo", meses=12)
    assert (a["Pares_vendidos"] == b["Pares_vendidos"]).all()


def test_generar_historial_linea_desconocida():
    with pytest.raises(ValueError):
        pr.generar_historial("Sandalia")


@pytest.mark.parametrize("linea", pr.LINEAS)
def test_pronosticar_devuelve_meses_futuros_consecutivos(linea):
    historial = pr.generar_historial(linea, meses=24)
    futuro = pr.pronosticar(historial, linea, meses_adelante=6)
    assert len(futuro) == 6
    assert futuro["Fecha"].iloc[0] > historial["Fecha"].iloc[-1]
    assert (futuro["Pronostico_base"] > 0).all()
    assert (futuro["Pronostico_ajustado"] > 0).all()


def test_pronosticar_respeta_escenario_de_presion_fija():
    historial = pr.generar_historial("Deportivo", meses=24)
    bajo = pr.pronosticar(historial, "Deportivo", meses_adelante=3, presion_informal=0.1)
    alto = pr.pronosticar(historial, "Deportivo", meses_adelante=3, presion_informal=0.8)
    # Más presión informal → menor demanda ajustada esperada para Manaco.
    assert alto["Pronostico_ajustado"].sum() < bajo["Pronostico_ajustado"].sum()
    # El pronóstico base no depende del escenario de presión informal.
    assert (alto["Pronostico_base"] == bajo["Pronostico_base"]).all()


@pytest.mark.parametrize("linea", pr.LINEAS)
def test_backtest_el_ajuste_informal_no_empeora_el_error(linea):
    historial = pr.generar_historial(linea, meses=24)
    resultado = pr.backtest(historial, linea, meses_prueba=6)
    assert resultado.mape_base >= 0
    assert resultado.mape_ajustado >= 0
    # La presión informal tiene una tendencia sostenida al alza en el historial simulado;
    # el modelo que la reconstruye y reaplica no debería ser peor que el que la ignora.
    assert resultado.mape_ajustado <= resultado.mape_base
