"""Consultas de catálogo, selectores y avisos compartidos por las páginas."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy import select

from src.db import obtener_sesion
from src.models import Producto, Tienda
from src.ui.estilos import aviso, estado_vacio

#: Tipo de aviso → ícono Material de la notificación.
ICONO_TOAST: dict[str, str] = {
    "success": ":material/check_circle:", "error": ":material/error:",
    "warning": ":material/warning:", "info": ":material/info:",
}


def tiendas_activas() -> pd.DataFrame:
    """Tiendas activas (id, nombre, ciudad, tipo)."""
    with obtener_sesion() as s:
        filas = s.scalars(select(Tienda).where(Tienda.activo.is_(True)).order_by(Tienda.nombre)).all()
        return pd.DataFrame([{"id": t.id, "nombre": t.nombre, "ciudad": t.ciudad, "tipo": t.tipo} for t in filas],
                            columns=["id", "nombre", "ciudad", "tipo"])


def productos_activos() -> pd.DataFrame:
    """Productos activos con una etiqueta legible para los selectores."""
    with obtener_sesion() as s:
        filas = s.scalars(select(Producto).where(Producto.activo.is_(True)).order_by(Producto.codigo_modelo)).all()
        df = pd.DataFrame([{
            "id": p.id, "codigo": p.codigo_modelo, "nombre": p.nombre, "categoria": p.categoria,
            "talla": p.talla, "color": p.color, "precio": p.precio_venta_bs,
        } for p in filas], columns=["id", "codigo", "nombre", "categoria", "talla", "color", "precio"])
    df["etiqueta"] = df["codigo"] + " · " + df["nombre"] + " (T" + df["talla"].astype(str) + ", " + df["color"] + ")"
    return df


def exigir_catalogo() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve tiendas y productos, o detiene la página si el catálogo está vacío."""
    tiendas, productos = tiendas_activas(), productos_activos()
    if tiendas.empty or productos.empty:
        estado_vacio("Primero registre tiendas y productos en el Catálogo "
                     "(o cargue la demo con python scripts/seed_demo.py).", "category",
                     ("Ir al Catálogo", "pages/6_Catalogo.py", "category"), clave="catalogo")
        st.stop()
    return tiendas, productos


def selector_tienda(tiendas: pd.DataFrame, key: str, contenedor=st) -> tuple[int, str]:  # noqa: ANN001
    """Selector de tienda que recuerda la última elegida. Devuelve ``(id, nombre)``."""
    nombres = tiendas["nombre"].tolist()
    previa = st.session_state.get("tienda_preferida")
    indice = nombres.index(previa) if previa in nombres else 0
    nombre = contenedor.selectbox("Tienda", nombres, index=indice, key=key)
    st.session_state["tienda_preferida"] = nombre
    return int(tiendas.loc[tiendas["nombre"] == nombre, "id"].iloc[0]), nombre


def selector_producto(productos: pd.DataFrame, key: str, contenedor=st) -> pd.Series:  # noqa: ANN001
    """Selector de producto. Devuelve la fila del producto elegido."""
    etiqueta = contenedor.selectbox("Producto", productos["etiqueta"].tolist(), key=key)
    return productos.loc[productos["etiqueta"] == etiqueta].iloc[0]


def selector_fecha(key: str, contenedor=st, valor: date | None = None) -> date:  # noqa: ANN001
    """Selector de fecha en formato dd/mm/aaaa (por defecto, hoy)."""
    return contenedor.date_input("Fecha", value=valor or date.today(), format="DD/MM/YYYY", key=key)


def avisar_y_recargar(mensaje: str, tipo: str = "success") -> None:
    """Guarda un aviso para mostrarlo tras recargar la página y recarga."""
    st.session_state["aviso_pendiente"] = (tipo, mensaje)
    st.rerun()


def mostrar_aviso_pendiente() -> None:
    """Muestra (una sola vez) el aviso guardado por ``avisar_y_recargar``: notificación y aviso en la página."""
    pendiente = st.session_state.pop("aviso_pendiente", None)
    if pendiente:
        tipo, mensaje = pendiente
        st.toast(mensaje, icon=ICONO_TOAST.get(tipo, ICONO_TOAST["info"]))
        aviso(mensaje, tipo)
