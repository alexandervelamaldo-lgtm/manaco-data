"""Carga, limpieza y validación del Excel de comercio exterior de calzado."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.config import (
    CLAVE_REGISTRO, COLUMNAS_EXCEL, EXCEL_PATH, TOLERANCIA_CONSISTENCIA,
)
from src.models import (
    BitacoraLimpieza, ComercioExterior, FactCalidad, FactProduccion, LogIngesta, Producto, RefMercadoLocal,
)

#: Nombre de columna del Excel → nombre de columna en la base de datos.
MAPA_COLUMNAS: dict[str, str] = {
    "País_reportante": "pais_reportante",
    "Flujo_comercial": "flujo_comercial",
    "Año": "anio",
    "Código_SA6": "codigo_sa6",
    "Categoría_calzado": "categoria_calzado",
    "Socio_comercial": "socio_comercial",
    "Valor_miles_USD": "valor_miles_usd",
    "Cantidad_pares": "cantidad_pares",
    "Valor_USD": "valor_usd",
    "Valor_USD_por_par": "valor_usd_por_par",
}

COLUMNAS_TEXTO = ("País_reportante", "Flujo_comercial", "Categoría_calzado", "Socio_comercial")
COLUMNAS_ENTERAS = ("Año", "Código_SA6", "Cantidad_pares")
COLUMNAS_DECIMALES = ("Valor_miles_USD", "Valor_USD", "Valor_USD_por_par")


class ErrorETL(Exception):
    """El archivo no tiene la estructura esperada."""


@dataclass
class ReglaAplicada:
    """Una regla de limpieza y su resultado."""

    regla: str
    filas_afectadas: int
    detalle: str


@dataclass
class ResultadoETL:
    """Resultado de la limpieza: datos marcados y bitácora."""

    datos: pd.DataFrame
    bitacora: list[ReglaAplicada] = field(default_factory=list)

    @property
    def filas_originales(self) -> int:
        return len(self.datos)

    @property
    def filas_validas(self) -> int:
        return int(self.datos["registro_valido"].sum())

    @property
    def filas_descartadas(self) -> int:
        return self.filas_originales - self.filas_validas

    @property
    def validos(self) -> pd.DataFrame:
        """Solo los registros válidos."""
        return self.datos[self.datos["registro_valido"]].copy()


def leer_excel(ruta: Path | str = EXCEL_PATH) -> pd.DataFrame:
    """Lee la primera hoja del Excel y verifica que tenga las 10 columnas."""
    df = pd.read_excel(ruta, sheet_name=0, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    faltantes = [c for c in COLUMNAS_EXCEL if c not in df.columns]
    if faltantes:
        raise ErrorETL(f"Al Excel le faltan las columnas: {', '.join(faltantes)}")
    return df[list(COLUMNAS_EXCEL)].copy()


def limpiar(df_original: pd.DataFrame) -> ResultadoETL:
    """Aplica las reglas de limpieza y devuelve los datos con ``registro_valido``."""
    df = df_original.copy().reset_index(drop=True)
    bitacora: list[ReglaAplicada] = []

    # Regla 1: tipos de datos y valores faltantes.
    for col in COLUMNAS_TEXTO:
        df[col] = df[col].astype("string").str.strip()
    for col in COLUMNAS_ENTERAS + COLUMNAS_DECIMALES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    faltantes = df.isna().sum()
    total_faltantes = int(faltantes.sum())
    detalle = (
        "Sin valores faltantes; tipos validados (texto, enteros y decimales)."
        if total_faltantes == 0
        else "Faltantes por columna: "
        + ", ".join(f"{c}={int(n)}" for c, n in faltantes.items() if n > 0)
    )
    bitacora.append(ReglaAplicada("Validación de tipos y faltantes", total_faltantes, detalle))
    df["registro_valido"] = ~df.isna().any(axis=1)
    for col in COLUMNAS_ENTERAS:
        df[col] = df[col].fillna(0).astype(int)

    # Regla 2: registros agregados "Mundo" (evita doble conteo).
    es_mundo = df["Socio_comercial"].str.casefold() == "mundo"
    n_mundo = int(es_mundo.sum())
    df.loc[es_mundo, "registro_valido"] = False
    bitacora.append(ReglaAplicada(
        "Separación de socio 'Mundo'", n_mundo,
        "No hay registros con socio 'Mundo'." if n_mundo == 0
        else f"{n_mundo} registros agregados 'Mundo' excluidos para no contar dos veces.",
    ))

    # Regla 3: claves repetidas. No se descartan: se conservan y se marcan,
    # igual que el diagnóstico de la Estación 2 (pueden ser registros parciales
    # de la fuente; se deben validar con la fuente original, no descartar a ciegas).
    repetidos = df.duplicated(subset=CLAVE_REGISTRO, keep=False)
    n_rep = int(repetidos.sum())
    bitacora.append(ReglaAplicada(
        "Claves repetidas", n_rep,
        f"Clave ({', '.join(CLAVE_REGISTRO)}): {n_rep} filas comparten clave con otra "
        "fila (valores distintos). Se conservan y se marcan; no se descartan.",
    ))

    # Regla 4: consistencia entre columnas calculadas.
    dif_valor = (df["Valor_USD"] - df["Valor_miles_USD"] * 1000).abs()
    inc_valor = dif_valor > TOLERANCIA_CONSISTENCIA * df["Valor_miles_USD"].abs().clip(lower=1)
    por_par_calc = df["Valor_USD"] / df["Cantidad_pares"].where(df["Cantidad_pares"] != 0)
    inc_por_par = (df["Valor_USD_por_par"] - por_par_calc).abs() > TOLERANCIA_CONSISTENCIA
    inc_por_par = inc_por_par.fillna(True)
    n_inc = int((inc_valor | inc_por_par).sum())
    bitacora.append(ReglaAplicada(
        "Consistencia de valores", n_inc,
        f"Valor_USD ≈ Valor_miles_USD × 1000: {int(inc_valor.sum())} inconsistencias. "
        f"Valor_USD_por_par ≈ Valor_USD / Cantidad_pares (tolerancia {TOLERANCIA_CONSISTENCIA}): "
        f"{int(inc_por_par.sum())} inconsistencias.",
    ))

    resultado = ResultadoETL(datos=df, bitacora=bitacora)
    bitacora.append(ReglaAplicada(
        "Resumen", resultado.filas_descartadas,
        f"{resultado.filas_originales} filas originales → {resultado.filas_validas} válidas, "
        f"{resultado.filas_descartadas} descartadas.",
    ))
    return resultado


def guardar_en_db(sesion: Session, resultado: ResultadoETL) -> None:
    """Reemplaza el contenido de ``comercio_exterior`` y ``bitacora_limpieza``."""
    sesion.execute(delete(ComercioExterior))
    sesion.execute(delete(BitacoraLimpieza))
    datos = resultado.datos.rename(columns=MAPA_COLUMNAS)
    registros = [
        ComercioExterior(**{k: (v.item() if hasattr(v, "item") else v) for k, v in fila.items()})
        for fila in datos.to_dict(orient="records")
    ]
    sesion.add_all(registros)
    sesion.add_all(
        BitacoraLimpieza(regla=r.regla, filas_afectadas=r.filas_afectadas, detalle=r.detalle)
        for r in resultado.bitacora
    )
    sesion.flush()


def cargar_excel_en_db(sesion: Session, ruta: Path | str = EXCEL_PATH) -> ResultadoETL:
    """Lee, limpia y guarda el Excel en la base de datos."""
    resultado = limpiar(leer_excel(ruta))
    guardar_en_db(sesion, resultado)
    return resultado


def leer_comercio_db(sesion: Session, solo_validos: bool = True) -> pd.DataFrame:
    """Devuelve la tabla ``comercio_exterior`` como DataFrame."""
    consulta = select(ComercioExterior)
    if solo_validos:
        consulta = consulta.where(ComercioExterior.registro_valido.is_(True))
    filas = sesion.scalars(consulta).all()
    columnas = list(MAPA_COLUMNAS.values()) + ["registro_valido"]
    return pd.DataFrame([{c: getattr(f, c) for c in columnas} for f in filas], columns=columnas)


def leer_bitacora_db(sesion: Session) -> pd.DataFrame:
    """Devuelve la bitácora de limpieza como DataFrame."""
    filas = sesion.scalars(select(BitacoraLimpieza).order_by(BitacoraLimpieza.id)).all()
    return pd.DataFrame(
        [{"Regla": f.regla, "Filas afectadas": f.filas_afectadas, "Detalle": f.detalle} for f in filas],
        columns=["Regla", "Filas afectadas", "Detalle"],
    )


def leer_mercado_local_db(sesion: Session) -> pd.DataFrame:
    """Devuelve la referencia de precios de la competencia y tipo de cambio paralelo. [Simulado]"""
    filas = sesion.scalars(select(RefMercadoLocal).order_by(RefMercadoLocal.fecha)).all()
    columnas = ["fecha", "ciudad", "mercado", "precio_competidor_bs", "tipo_cambio_paralelo"]
    return pd.DataFrame([{c: getattr(f, c) for c in columnas} for f in filas], columns=columnas)


def leer_produccion_db(sesion: Session) -> pd.DataFrame:
    """Devuelve ``fact_produccion`` con la línea (categoría) del producto de cada lote. [Simulado]"""
    consulta = select(FactProduccion, Producto.categoria).join(Producto, FactProduccion.producto_id == Producto.id)
    filas = sesion.execute(consulta).all()
    return pd.DataFrame(
        [{"fecha": f.fecha, "categoria": cat, "pares": f.pares,
          "costo_insumos_bs": f.costo_insumos_bs, "costo_mano_obra_bs": f.costo_mano_obra_bs} for f, cat in filas],
        columns=["fecha", "categoria", "pares", "costo_insumos_bs", "costo_mano_obra_bs"],
    )


def leer_calidad_db(sesion: Session) -> pd.DataFrame:
    """Devuelve ``fact_calidad`` con la línea (categoría) del producto de cada lote. [Simulado]"""
    consulta = select(FactCalidad, Producto.categoria).join(Producto, FactCalidad.producto_id == Producto.id)
    filas = sesion.execute(consulta).all()
    return pd.DataFrame(
        [{"fecha": f.fecha, "categoria": cat, "defectos": f.defectos, "devoluciones": f.devoluciones}
         for f, cat in filas],
        columns=["fecha", "categoria", "defectos", "devoluciones"],
    )


def leer_ingesta_db(sesion: Session) -> pd.DataFrame:
    """Devuelve el registro de cargas de datos por sucursal. [Simulado]"""
    filas = sesion.scalars(select(LogIngesta).order_by(LogIngesta.fecha.desc())).all()
    columnas = ["fecha", "sucursal", "archivo", "filas_leidas", "filas_corregidas", "filas_rechazadas"]
    return pd.DataFrame([{c: getattr(f, c) for c in columnas} for f in filas], columns=columnas)
