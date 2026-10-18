"""Pruebas de la carga y limpieza del Excel de comercio exterior."""

from __future__ import annotations

import pandas as pd
import pytest

from src.config import EXCEL_PATH
from src.services import etl


@pytest.fixture(scope="module")
def resultado() -> etl.ResultadoETL:
    return etl.limpiar(etl.leer_excel(EXCEL_PATH))


def test_filas_validas_y_descartadas(resultado):
    assert resultado.filas_originales == 240
    assert resultado.filas_validas == 230
    assert resultado.filas_descartadas == 10


def test_sin_faltantes_ni_mundo(resultado):
    reglas = {r.regla: r for r in resultado.bitacora}
    assert reglas["Validación de tipos y faltantes"].filas_afectadas == 0
    assert reglas["Separación de socio 'Mundo'"].filas_afectadas == 0
    assert reglas["Claves repetidas"].filas_afectadas == 10


def test_totales_por_flujo(resultado):
    totales = resultado.validos.groupby("Flujo_comercial")["Valor_USD"].sum() / 1e6
    assert round(totales["Importación"], 1) == 17055.8
    assert round(totales["Exportación"], 1) == 10605.5


def test_claves_unicas_en_validos(resultado):
    assert not resultado.validos.duplicated(subset=["Flujo_comercial", "Año", "Código_SA6", "Socio_comercial"]).any()


def test_regla_mundo_y_repetidos_en_datos_sinteticos():
    base = {
        "País_reportante": "España", "Flujo_comercial": "Importación", "Año": 2024,
        "Código_SA6": 640411, "Categoría_calzado": "Deportivo", "Socio_comercial": "China",
        "Valor_miles_USD": 1.0, "Cantidad_pares": 100, "Valor_USD": 1000.0, "Valor_USD_por_par": 10.0,
    }
    df = pd.DataFrame([base, base, {**base, "Socio_comercial": "Mundo"}])
    res = etl.limpiar(df)
    assert res.filas_validas == 1
    assert res.datos["registro_valido"].tolist() == [True, False, False]


def test_guardar_y_leer_db(sesion, resultado):
    etl.guardar_en_db(sesion, resultado)
    validos = etl.leer_comercio_db(sesion)
    assert len(validos) == 230
    assert len(etl.leer_comercio_db(sesion, solo_validos=False)) == 240
    assert not etl.leer_bitacora_db(sesion).empty
