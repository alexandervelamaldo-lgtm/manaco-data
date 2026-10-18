"""Reglas de negocio de apertura, ventas y cierre de inventario.

Este módulo no depende de Streamlit: recibe una sesión SQLAlchemy y lanza
``ErrorNegocio`` con mensajes claros en español cuando una regla no se cumple.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.config import (
    ESTADO_CORRECTO, ESTADO_FALTANTE, ESTADO_SOBRANTE, ROL_ADMIN, TOLERANCIA_DIFERENCIA,
)
from src.models import AnulacionCierre, Apertura, Cierre, Producto, Tienda, Usuario, Venta


class ErrorNegocio(Exception):
    """Una regla de negocio impide la operación. El mensaje es apto para el usuario."""


@dataclass(frozen=True)
class ResumenDia:
    """Situación de un producto en una tienda para una fecha."""

    saldo_inicial: int | None
    total_vendido: int
    saldo_esperado: int | None
    tiene_apertura: bool
    tiene_cierre: bool


# --- Cálculos puros ----------------------------------------------------------

def calcular_saldo_esperado(saldo_inicial: int, total_vendido: int) -> int:
    """Saldo esperado = saldo inicial − total vendido."""
    return saldo_inicial - total_vendido


def calcular_diferencia(conteo_final: int, saldo_esperado: int) -> int:
    """Diferencia = conteo final − saldo esperado."""
    return conteo_final - saldo_esperado


def clasificar_diferencia(diferencia: int, tolerancia: int = TOLERANCIA_DIFERENCIA) -> str:
    """Devuelve ``Correcto``, ``Faltante`` o ``Sobrante`` según la diferencia."""
    if abs(diferencia) <= tolerancia:
        return ESTADO_CORRECTO
    return ESTADO_FALTANTE if diferencia < 0 else ESTADO_SOBRANTE


def mensaje_alerta(
    estado: str, diferencia: int, codigo_modelo: str, tienda: str,
    saldo_esperado: int, conteo_final: int,
) -> str:
    """Construye el texto de la alerta, p. ej. 'Faltan 2 pares de MAN-DEP-001 en ...'."""
    n = abs(diferencia)
    pares = "par" if n == 1 else "pares"
    detalle = f"(esperado {saldo_esperado}, contado {conteo_final})"
    if estado == ESTADO_FALTANTE:
        verbo = "Falta" if n == 1 else "Faltan"
    elif estado == ESTADO_SOBRANTE:
        verbo = "Sobra" if n == 1 else "Sobran"
    else:
        return f"Inventario correcto de {codigo_modelo} en {tienda} {detalle}"
    return f"{verbo} {n} {pares} de {codigo_modelo} en {tienda} {detalle}"


def mensaje_alerta_cierre(cierre: Cierre) -> str:
    """Mensaje de alerta a partir de un cierre guardado."""
    return mensaje_alerta(
        cierre.estado, cierre.diferencia, cierre.producto.codigo_modelo,
        cierre.tienda.nombre, cierre.saldo_esperado, cierre.conteo_final,
    )


# --- Consultas ---------------------------------------------------------------

def obtener_apertura(sesion: Session, fecha: date, tienda_id: int, producto_id: int) -> Apertura | None:
    """Apertura de un producto en una tienda y fecha, si existe."""
    return sesion.scalar(select(Apertura).where(
        Apertura.fecha == fecha, Apertura.tienda_id == tienda_id, Apertura.producto_id == producto_id,
    ))


def obtener_cierre(sesion: Session, fecha: date, tienda_id: int, producto_id: int) -> Cierre | None:
    """Cierre de un producto en una tienda y fecha, si existe."""
    return sesion.scalar(select(Cierre).where(
        Cierre.fecha == fecha, Cierre.tienda_id == tienda_id, Cierre.producto_id == producto_id,
    ))


def total_vendido(sesion: Session, fecha: date, tienda_id: int, producto_id: int) -> int:
    """Suma de pares vendidos del día."""
    total = sesion.scalar(select(func.coalesce(func.sum(Venta.cantidad), 0)).where(
        Venta.fecha == fecha, Venta.tienda_id == tienda_id, Venta.producto_id == producto_id,
    ))
    return int(total or 0)


def productos_cerrados(sesion: Session, fecha: date, tienda_id: int) -> set[int]:
    """Ids de los productos que ya tienen cierre en la fecha y tienda."""
    return set(sesion.scalars(select(Cierre.producto_id).where(
        Cierre.fecha == fecha, Cierre.tienda_id == tienda_id)).all())


def proponer_saldo_inicial(sesion: Session, fecha: date, tienda_id: int, producto_id: int) -> int | None:
    """Propone el ``conteo_final`` del cierre del día anterior, si existe."""
    cierre = obtener_cierre(sesion, fecha - timedelta(days=1), tienda_id, producto_id)
    return cierre.conteo_final if cierre else None


def resumen_dia(sesion: Session, fecha: date, tienda_id: int, producto_id: int) -> ResumenDia:
    """Saldo inicial, vendido y esperado de un producto en el día."""
    apertura = obtener_apertura(sesion, fecha, tienda_id, producto_id)
    vendido = total_vendido(sesion, fecha, tienda_id, producto_id)
    cierre = obtener_cierre(sesion, fecha, tienda_id, producto_id)
    if apertura is None:
        return ResumenDia(None, vendido, None, False, cierre is not None)
    return ResumenDia(
        apertura.saldo_inicial, vendido,
        calcular_saldo_esperado(apertura.saldo_inicial, vendido), True, cierre is not None,
    )


# --- Operaciones -------------------------------------------------------------

def registrar_apertura(
    sesion: Session, fecha: date, tienda_id: int, producto_id: int,
    saldo_inicial: int, usuario_id: int | None = None,
) -> Apertura:
    """Registra el saldo inicial del día. No admite duplicados ni negativos."""
    if saldo_inicial is None or int(saldo_inicial) < 0:
        raise ErrorNegocio("El saldo inicial no puede ser negativo.")
    if obtener_apertura(sesion, fecha, tienda_id, producto_id) is not None:
        producto = sesion.get(Producto, producto_id)
        codigo = producto.codigo_modelo if producto else "el producto"
        raise ErrorNegocio(f"Ya existe una apertura de {codigo} para el {fecha:%d/%m/%Y} en esta tienda.")
    apertura = Apertura(
        fecha=fecha, tienda_id=tienda_id, producto_id=producto_id,
        saldo_inicial=int(saldo_inicial), usuario_id=usuario_id,
    )
    sesion.add(apertura)
    sesion.flush()
    return apertura


def abrir_tienda_completa(
    sesion: Session, fecha: date, tienda_id: int, usuario_id: int | None = None,
    saldos: dict[int, int] | None = None,
) -> tuple[int, int]:
    """Abre todos los productos activos de una tienda.

    Usa ``saldos[producto_id]`` si se indica; si no, el cierre de ayer (o 0).
    Devuelve ``(aperturas_creadas, ya_existentes)``.
    """
    creadas = omitidas = 0
    productos = sesion.scalars(select(Producto).where(Producto.activo.is_(True))).all()
    for producto in productos:
        if obtener_apertura(sesion, fecha, tienda_id, producto.id) is not None:
            omitidas += 1
            continue
        if saldos and producto.id in saldos:
            saldo = saldos[producto.id]
        else:
            saldo = proponer_saldo_inicial(sesion, fecha, tienda_id, producto.id) or 0
        registrar_apertura(sesion, fecha, tienda_id, producto.id, saldo, usuario_id)
        creadas += 1
    return creadas, omitidas


def registrar_venta(
    sesion: Session, fecha: date, tienda_id: int, producto_id: int, cantidad: int,
    precio_unitario_bs: float | None = None, usuario_id: int | None = None,
    hora: time | None = None,
) -> Venta:
    """Registra una venta validando apertura, cantidad y stock disponible."""
    if cantidad is None or int(cantidad) <= 0:
        raise ErrorNegocio("La cantidad vendida debe ser mayor que 0.")
    apertura = obtener_apertura(sesion, fecha, tienda_id, producto_id)
    producto = sesion.get(Producto, producto_id)
    codigo = producto.codigo_modelo if producto else "el producto"
    if apertura is None:
        raise ErrorNegocio(f"No hay apertura de {codigo} el {fecha:%d/%m/%Y}. Registre primero la apertura.")
    if obtener_cierre(sesion, fecha, tienda_id, producto_id) is not None:
        raise ErrorNegocio(f"El día {fecha:%d/%m/%Y} ya está cerrado para {codigo}; no se pueden registrar ventas.")
    vendido = total_vendido(sesion, fecha, tienda_id, producto_id)
    disponible = apertura.saldo_inicial - vendido
    if int(cantidad) > disponible:
        raise ErrorNegocio(
            f"No hay stock suficiente de {codigo}: disponible {disponible}, "
            f"se intentó vender {int(cantidad)}."
        )
    if precio_unitario_bs is None:
        precio_unitario_bs = producto.precio_venta_bs if producto else 0.0
    if precio_unitario_bs < 0:
        raise ErrorNegocio("El precio unitario no puede ser negativo.")
    venta = Venta(
        fecha=fecha, hora=hora or datetime.now().time().replace(microsecond=0),
        tienda_id=tienda_id, producto_id=producto_id, cantidad=int(cantidad),
        precio_unitario_bs=float(precio_unitario_bs), usuario_id=usuario_id,
    )
    sesion.add(venta)
    sesion.flush()
    return venta


def registrar_cierre(
    sesion: Session, fecha: date, tienda_id: int, producto_id: int, conteo_final: int,
    usuario_id: int | None = None, conteo_ia: int | None = None,
    confianza_ia: float | None = None, foto_ruta: str | None = None,
    observacion: str = "", tolerancia: int = TOLERANCIA_DIFERENCIA,
) -> Cierre:
    """Calcula la diferencia contra el saldo esperado y guarda el cierre del día."""
    if conteo_final is None or int(conteo_final) < 0:
        raise ErrorNegocio("El conteo final no puede ser negativo.")
    apertura = obtener_apertura(sesion, fecha, tienda_id, producto_id)
    producto = sesion.get(Producto, producto_id)
    codigo = producto.codigo_modelo if producto else "el producto"
    if apertura is None:
        raise ErrorNegocio(f"No se puede cerrar {codigo}: no existe la apertura del {fecha:%d/%m/%Y}.")
    if obtener_cierre(sesion, fecha, tienda_id, producto_id) is not None:
        raise ErrorNegocio(
            f"El cierre de {codigo} del {fecha:%d/%m/%Y} ya fue guardado. "
            "Solo el administrador puede anularlo."
        )
    vendido = total_vendido(sesion, fecha, tienda_id, producto_id)
    esperado = calcular_saldo_esperado(apertura.saldo_inicial, vendido)
    diferencia = calcular_diferencia(int(conteo_final), esperado)
    estado = clasificar_diferencia(diferencia, tolerancia)
    cierre = Cierre(
        fecha=fecha, tienda_id=tienda_id, producto_id=producto_id,
        saldo_inicial=apertura.saldo_inicial, total_vendido=vendido, saldo_esperado=esperado,
        conteo_ia=conteo_ia, conteo_final=int(conteo_final), diferencia=diferencia, estado=estado,
        foto_ruta=foto_ruta, confianza_ia=confianza_ia, observacion=observacion or "",
        alerta_atendida=estado == ESTADO_CORRECTO, usuario_id=usuario_id,
    )
    sesion.add(cierre)
    sesion.flush()
    return cierre


def anular_cierre(sesion: Session, cierre_id: int, usuario_id: int, motivo: str) -> AnulacionCierre:
    """Anula un cierre (solo administrador, con motivo) y deja constancia."""
    usuario = sesion.get(Usuario, usuario_id)
    if usuario is None or usuario.rol != ROL_ADMIN:
        raise ErrorNegocio("Solo el administrador puede anular un cierre.")
    if not motivo or not motivo.strip():
        raise ErrorNegocio("Indique el motivo de la anulación.")
    cierre = sesion.get(Cierre, cierre_id)
    if cierre is None:
        raise ErrorNegocio("El cierre indicado no existe.")
    anulacion = AnulacionCierre(
        fecha=cierre.fecha, tienda_id=cierre.tienda_id, producto_id=cierre.producto_id,
        conteo_final=cierre.conteo_final, diferencia=cierre.diferencia, estado=cierre.estado,
        motivo=motivo.strip(), usuario_id=usuario_id,
    )
    sesion.add(anulacion)
    sesion.delete(cierre)
    sesion.flush()
    return anulacion


def marcar_alerta_atendida(sesion: Session, cierre_id: int) -> None:
    """Quita una alerta de la lista de pendientes."""
    cierre = sesion.get(Cierre, cierre_id)
    if cierre is not None:
        cierre.alerta_atendida = True
        sesion.flush()


# --- Tablas para la interfaz -------------------------------------------------

def stock_disponible(sesion: Session, fecha: date, tienda_id: int) -> pd.DataFrame:
    """Stock en tiempo real por producto: saldo inicial − vendido."""
    vendidos = (
        select(Venta.producto_id, func.sum(Venta.cantidad).label("vendido"))
        .where(Venta.fecha == fecha, Venta.tienda_id == tienda_id)
        .group_by(Venta.producto_id).subquery()
    )
    filas = sesion.execute(
        select(Producto.codigo_modelo, Producto.nombre, Apertura.saldo_inicial,
               func.coalesce(vendidos.c.vendido, 0))
        .join(Apertura, Apertura.producto_id == Producto.id)
        .outerjoin(vendidos, vendidos.c.producto_id == Producto.id)
        .where(Apertura.fecha == fecha, Apertura.tienda_id == tienda_id)
        .order_by(Producto.codigo_modelo)
    ).all()
    df = pd.DataFrame(filas, columns=["Código", "Producto", "Saldo inicial", "Vendido"])
    df["Disponible"] = df["Saldo inicial"] - df["Vendido"]
    return df


def tabla_cierres(sesion: Session) -> pd.DataFrame:
    """Todos los cierres con nombres legibles, del más reciente al más antiguo."""
    filas = sesion.execute(
        select(Cierre, Tienda.nombre, Producto.codigo_modelo, Producto.nombre, Producto.categoria)
        .join(Tienda, Cierre.tienda_id == Tienda.id)
        .join(Producto, Cierre.producto_id == Producto.id)
        .order_by(Cierre.fecha.desc(), Tienda.nombre, Producto.codigo_modelo)
    ).all()
    registros = [{
        "id": c.id, "Fecha": c.fecha, "Tienda": tienda, "Código": codigo, "Producto": nombre,
        "Categoría": categoria, "Saldo inicial": c.saldo_inicial, "Vendido": c.total_vendido,
        "Esperado": c.saldo_esperado, "Conteo IA": c.conteo_ia, "Conteo final": c.conteo_final,
        "Diferencia": c.diferencia, "Estado": c.estado, "Confianza IA": c.confianza_ia,
        "Observación": c.observacion, "Foto": c.foto_ruta, "Atendida": c.alerta_atendida,
    } for c, tienda, codigo, nombre, categoria in filas]
    columnas = ["id", "Fecha", "Tienda", "Código", "Producto", "Categoría", "Saldo inicial",
                "Vendido", "Esperado", "Conteo IA", "Conteo final", "Diferencia", "Estado",
                "Confianza IA", "Observación", "Foto", "Atendida"]
    return pd.DataFrame(registros, columns=columnas)


@dataclass(frozen=True)
class IndicadoresDia:
    """KPI operativos de un día en todas las tiendas."""

    pares_apertura: int
    pares_vendidos: int
    ventas_bs: float
    cierres_hechos: int
    cierres_pendientes: int


def indicadores_dia(sesion: Session, fecha: date) -> IndicadoresDia:
    """Pares abiertos, vendidos, importe y avance de cierres de una fecha."""
    pares_apertura = sesion.scalar(
        select(func.coalesce(func.sum(Apertura.saldo_inicial), 0)).where(Apertura.fecha == fecha))
    n_aperturas = sesion.scalar(select(func.count(Apertura.id)).where(Apertura.fecha == fecha))
    vendidos, importe = sesion.execute(
        select(func.coalesce(func.sum(Venta.cantidad), 0),
               func.coalesce(func.sum(Venta.cantidad * Venta.precio_unitario_bs), 0.0))
        .where(Venta.fecha == fecha)
    ).one()
    hechos = sesion.scalar(select(func.count(Cierre.id)).where(Cierre.fecha == fecha))
    return IndicadoresDia(int(pares_apertura), int(vendidos), float(importe), int(hechos),
                          max(int(n_aperturas) - int(hechos), 0))


def tabla_ventas(sesion: Session, desde: date | None = None, hasta: date | None = None,
                 tienda_id: int | None = None) -> pd.DataFrame:
    """Ventas con nombres legibles, filtradas por rango de fechas y tienda."""
    consulta = (
        select(Venta, Tienda.nombre, Producto.codigo_modelo, Producto.nombre, Producto.categoria)
        .join(Tienda, Venta.tienda_id == Tienda.id).join(Producto, Venta.producto_id == Producto.id)
    )
    if desde:
        consulta = consulta.where(Venta.fecha >= desde)
    if hasta:
        consulta = consulta.where(Venta.fecha <= hasta)
    if tienda_id:
        consulta = consulta.where(Venta.tienda_id == tienda_id)
    filas = sesion.execute(consulta.order_by(Venta.fecha.desc(), Venta.hora.desc())).all()
    columnas = ["Fecha", "Hora", "Tienda", "Código", "Producto", "Categoría", "Cantidad",
                "Precio unitario", "Importe"]
    return pd.DataFrame([[
        v.fecha, v.hora, tienda, codigo, nombre, categoria, v.cantidad, v.precio_unitario_bs,
        v.cantidad * v.precio_unitario_bs,
    ] for v, tienda, codigo, nombre, categoria in filas], columns=columnas)


def tabla_aperturas(sesion: Session, fecha: date, tienda_id: int | None = None) -> pd.DataFrame:
    """Aperturas de una fecha con nombres legibles."""
    consulta = (
        select(Apertura, Tienda.nombre, Producto.codigo_modelo, Producto.nombre)
        .join(Tienda, Apertura.tienda_id == Tienda.id).join(Producto, Apertura.producto_id == Producto.id)
        .where(Apertura.fecha == fecha)
    )
    if tienda_id:
        consulta = consulta.where(Apertura.tienda_id == tienda_id)
    filas = sesion.execute(consulta.order_by(Tienda.nombre, Producto.codigo_modelo)).all()
    return pd.DataFrame(
        [[tienda, codigo, nombre, a.saldo_inicial, a.creado_en] for a, tienda, codigo, nombre in filas],
        columns=["Tienda", "Código", "Producto", "Saldo inicial", "Registrado"],
    )


def alertas_pendientes(sesion: Session) -> list[tuple[Cierre, str]]:
    """Cierres con diferencia que aún no fueron atendidos, con su mensaje."""
    cierres = sesion.scalars(
        select(Cierre).where(Cierre.estado != ESTADO_CORRECTO, Cierre.alerta_atendida.is_(False))
        .order_by(Cierre.fecha.desc())
    ).all()
    return [(c, mensaje_alerta_cierre(c)) for c in cierres]
