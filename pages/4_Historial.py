"""Planilla histórica de cierres con filtros, colores, fotos y exportación a Excel."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from src.auth import proteger_pagina
from src.config import ESTADOS
from src.db import obtener_sesion
from src.services import inventario as inv
from src.services.reportes import exportar_cierres_excel
from src.ui.estilos import (
    ICONOS, encabezado, estado_vacio, estilo_estado, num, pastilla_estado, seccion, tarjeta, tarjeta_kpi,
)

proteger_pagina("historial")
encabezado("Historial de cierres", "Consulte, filtre y descargue todos los cierres de inventario.",
           ICONOS["historial"])

with obtener_sesion() as s:
    cierres = inv.tabla_cierres(s)
if cierres.empty:
    with tarjeta("vacio"):
        estado_vacio("Todavía no hay cierres registrados.", "history",
                     ("Ir a Cierre y conteo", "pages/3_Cierre_y_conteo.py", "photo_camera"), clave="historial")
    st.stop()

cierres["Fecha"] = pd.to_datetime(cierres["Fecha"]).dt.date
minimo, maximo = cierres["Fecha"].min(), cierres["Fecha"].max()

with tarjeta("filtros", "Filtros", icono="filter_alt"):
    f1, f2, f3, f4 = st.columns([1.3, 1, 1, 1])
    rango = f1.date_input("Rango de fechas", value=(max(minimo, maximo - timedelta(days=29)), maximo),
                          min_value=minimo, max_value=max(maximo, date.today()), format="DD/MM/YYYY")
    tiendas_sel = f2.multiselect("Tienda", sorted(cierres["Tienda"].unique()), placeholder="Todas")
    productos_sel = f3.multiselect("Producto", sorted(cierres["Código"].unique()), placeholder="Todos")
    estados_sel = f4.multiselect("Estado", list(ESTADOS), placeholder="Todos")

desde, hasta = (rango if isinstance(rango, tuple) and len(rango) == 2 else (minimo, maximo))
vista = cierres[(cierres["Fecha"] >= desde) & (cierres["Fecha"] <= hasta)]
if tiendas_sel:
    vista = vista[vista["Tienda"].isin(tiendas_sel)]
if productos_sel:
    vista = vista[vista["Código"].isin(productos_sel)]
if estados_sel:
    vista = vista[vista["Estado"].isin(estados_sel)]
vista = vista.reset_index(drop=True)

st.write("")
n_falt, n_sobr = int((vista["Estado"] == "Faltante").sum()), int((vista["Estado"] == "Sobrante").sum())
pct_ok = 100 * (vista["Estado"] == "Correcto").mean() if len(vista) else 0
k1, k2, k3, k4 = st.columns(4)
with k1:
    tarjeta_kpi("Cierres del período", num(len(vista)), f"{desde:%d/%m} – {hasta:%d/%m}", "fact_check", "azul",
                mini=True)
with k2:
    tarjeta_kpi("Correctos", f"{num(pct_ok, 0)} %", f"{num(int((vista['Estado'] == 'Correcto').sum()))} cierres",
                "check_circle", "verde", "sube" if pct_ok >= 90 else None, mini=True)
with k3:
    tarjeta_kpi("Pares faltantes", num(int(-vista.loc[vista["Diferencia"] < 0, "Diferencia"].sum())),
                f"{n_falt} cierres", "trending_down", "rojo", "baja" if n_falt else None, mini=True)
with k4:
    tarjeta_kpi("Pares sobrantes", num(int(vista.loc[vista["Diferencia"] > 0, "Diferencia"].sum())),
                f"{n_sobr} cierres", "trending_up", "naranja", mini=True)

seccion("Planilla de cierres", "Seleccione una fila para ver su foto de evidencia.")
with tarjeta("tabla"):
    if vista.empty:
        estado_vacio("Ningún cierre coincide con los filtros elegidos.", "search_off")
        st.stop()
    columnas = ["Fecha", "Tienda", "Código", "Producto", "Saldo inicial", "Vendido", "Esperado",
                "Conteo IA", "Conteo final", "Diferencia", "Estado", "Observación"]
    tabla = vista[columnas].copy()
    tabla["Conteo IA"] = tabla["Conteo IA"].map(lambda v: "—" if pd.isna(v) else str(int(v)))
    estilizada = (
        tabla.style
        .map(estilo_estado, subset=["Estado"])
        .map(lambda d: "color: #DC2626; font-weight: 700" if d < 0 else ("color: #B45309; font-weight: 700" if d > 0 else ""),
             subset=["Diferencia"])
        .format({"Fecha": lambda f: f.strftime("%d/%m/%Y"), "Diferencia": lambda d: f"{d:+d}" if d else "0"})
    )
    seleccion = st.dataframe(estilizada, hide_index=True, width="stretch", height=420,
                             on_select="rerun", selection_mode="single-row", key="hist_tabla")
    st.download_button(
        "Descargar Excel", data=exportar_cierres_excel(vista), icon=":material/download:",
        file_name=f"cierres_manaco_{desde:%Y%m%d}_{hasta:%Y%m%d}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary",
    )

filas = seleccion.selection.rows if seleccion and seleccion.selection else []
if filas:
    fila = vista.iloc[filas[0]]
    st.write("")
    with tarjeta("detalle", f"{fila['Fecha']:%d/%m/%Y} · {fila['Tienda']} · {fila['Código']}",
                 f"Esperado {fila['Esperado']}, contado {fila['Conteo final']}", "image"):
        st.markdown(pastilla_estado(fila["Estado"]), unsafe_allow_html=True)
        if fila["Foto"] and pd.notna(fila["Foto"]):
            c1, c2 = st.columns([1.3, 1], gap="medium")
            try:
                c1.image(fila["Foto"], caption="Foto de evidencia", width="stretch")
            except Exception:  # noqa: BLE001
                with c1:
                    estado_vacio("La foto de evidencia ya no está disponible en el disco.", "hide_image")
            with c2:
                if pd.notna(fila["Confianza IA"]):
                    tarjeta_kpi("Confianza IA", f"{num(fila['Confianza IA'] * 100, 0)} %",
                                f"conteo IA {int(fila['Conteo IA'])}" if pd.notna(fila["Conteo IA"]) else None,
                                "smart_toy", "azul", mini=True)
        else:
            estado_vacio("Este cierre se registró sin foto (conteo manual).", "no_photography")
