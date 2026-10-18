"""Pruebas de las reglas de negocio de inventario."""

from __future__ import annotations

from datetime import timedelta

import pytest

from src.services import inventario as inv
from src.services.inventario import ErrorNegocio


def test_ejemplo_obligatorio_50_12_38_36(sesion, hoy):
    """Apertura 50, ventas 12 → esperado 38; conteo 36 → diferencia −2, Faltante."""
    inv.registrar_apertura(sesion, hoy, 1, 1, 50, usuario_id=2)
    inv.registrar_venta(sesion, hoy, 1, 1, 5, usuario_id=2)
    inv.registrar_venta(sesion, hoy, 1, 1, 7, usuario_id=2)
    resumen = inv.resumen_dia(sesion, hoy, 1, 1)
    assert resumen.saldo_inicial == 50
    assert resumen.total_vendido == 12
    assert resumen.saldo_esperado == 38

    cierre = inv.registrar_cierre(sesion, hoy, 1, 1, conteo_final=36, usuario_id=2)
    assert cierre.saldo_esperado == 38
    assert cierre.diferencia == -2
    assert cierre.estado == "Faltante"
    assert inv.mensaje_alerta_cierre(cierre) == (
        "Faltan 2 pares de MAN-DEP-001 en Tienda Prado (esperado 38, contado 36)"
    )
    assert len(inv.alertas_pendientes(sesion)) == 1


@pytest.mark.parametrize(("diferencia", "tolerancia", "estado"), [
    (0, 0, "Correcto"), (-1, 0, "Faltante"), (3, 0, "Sobrante"),
    (-1, 1, "Correcto"), (1, 1, "Correcto"), (-2, 1, "Faltante"),
])
def test_clasificar_diferencia(diferencia, tolerancia, estado):
    assert inv.clasificar_diferencia(diferencia, tolerancia) == estado


def test_mensaje_sobrante_singular():
    assert inv.mensaje_alerta("Sobrante", 1, "MAN-DEP-001", "Tienda Prado", 10, 11) == (
        "Sobra 1 par de MAN-DEP-001 en Tienda Prado (esperado 10, contado 11)"
    )


def test_apertura_no_admite_duplicados_ni_negativos(sesion, hoy):
    with pytest.raises(ErrorNegocio, match="negativo"):
        inv.registrar_apertura(sesion, hoy, 1, 1, -1)
    inv.registrar_apertura(sesion, hoy, 1, 1, 10)
    with pytest.raises(ErrorNegocio, match="Ya existe"):
        inv.registrar_apertura(sesion, hoy, 1, 1, 10)


def test_apertura_propone_cierre_de_ayer(sesion, hoy):
    ayer = hoy - timedelta(days=1)
    assert inv.proponer_saldo_inicial(sesion, hoy, 1, 1) is None
    inv.registrar_apertura(sesion, ayer, 1, 1, 20)
    inv.registrar_venta(sesion, ayer, 1, 1, 4)
    inv.registrar_cierre(sesion, ayer, 1, 1, conteo_final=15)
    assert inv.proponer_saldo_inicial(sesion, hoy, 1, 1) == 15


def test_abrir_tienda_completa(sesion, hoy):
    creadas, omitidas = inv.abrir_tienda_completa(sesion, hoy, 1, saldos={1: 30})
    assert (creadas, omitidas) == (1, 0)
    assert inv.obtener_apertura(sesion, hoy, 1, 1).saldo_inicial == 30
    assert inv.abrir_tienda_completa(sesion, hoy, 1) == (0, 1)


def test_venta_requiere_apertura(sesion, hoy):
    with pytest.raises(ErrorNegocio, match="apertura"):
        inv.registrar_venta(sesion, hoy, 1, 1, 1)


def test_venta_cantidad_positiva_y_stock(sesion, hoy):
    inv.registrar_apertura(sesion, hoy, 1, 1, 10)
    with pytest.raises(ErrorNegocio, match="mayor que 0"):
        inv.registrar_venta(sesion, hoy, 1, 1, 0)
    inv.registrar_venta(sesion, hoy, 1, 1, 8)
    with pytest.raises(ErrorNegocio, match="disponible 2"):
        inv.registrar_venta(sesion, hoy, 1, 1, 3)
    venta = inv.registrar_venta(sesion, hoy, 1, 1, 2)
    assert venta.precio_unitario_bs == 389.0
    df = inv.stock_disponible(sesion, hoy, 1)
    assert df.loc[0, "Disponible"] == 0


def test_cierre_requiere_apertura_y_es_unico(sesion, hoy):
    with pytest.raises(ErrorNegocio, match="no existe la apertura"):
        inv.registrar_cierre(sesion, hoy, 1, 1, 5)
    inv.registrar_apertura(sesion, hoy, 1, 1, 5)
    cierre = inv.registrar_cierre(sesion, hoy, 1, 1, 5, conteo_ia=4, confianza_ia=0.8)
    assert cierre.estado == "Correcto"
    assert cierre.conteo_ia == 4 and cierre.conteo_final == 5
    with pytest.raises(ErrorNegocio, match="ya fue guardado"):
        inv.registrar_cierre(sesion, hoy, 1, 1, 5)
    with pytest.raises(ErrorNegocio, match="ya está cerrado"):
        inv.registrar_venta(sesion, hoy, 1, 1, 1)


def test_solo_admin_anula_cierre_con_motivo(sesion, hoy):
    inv.registrar_apertura(sesion, hoy, 1, 1, 5)
    cierre = inv.registrar_cierre(sesion, hoy, 1, 1, 3)
    with pytest.raises(ErrorNegocio, match="Solo el administrador"):
        inv.anular_cierre(sesion, cierre.id, usuario_id=2, motivo="error")
    with pytest.raises(ErrorNegocio, match="motivo"):
        inv.anular_cierre(sesion, cierre.id, usuario_id=1, motivo="  ")
    inv.anular_cierre(sesion, cierre.id, usuario_id=1, motivo="Conteo mal digitado")
    assert inv.obtener_cierre(sesion, hoy, 1, 1) is None
    nuevo = inv.registrar_cierre(sesion, hoy, 1, 1, 5)
    assert nuevo.estado == "Correcto"


def test_tolerancia_configurable(sesion, hoy):
    inv.registrar_apertura(sesion, hoy, 1, 1, 10)
    cierre = inv.registrar_cierre(sesion, hoy, 1, 1, 9, tolerancia=1)
    assert cierre.diferencia == -1
    assert cierre.estado == "Correcto"
