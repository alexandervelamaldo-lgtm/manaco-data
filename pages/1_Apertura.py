"""Apertura del día: saldo inicial por tienda y producto."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.auth import proteger_pagina
from src.db import obtener_sesion
from src.services import inventario as inv
from src.services.inventario import ErrorNegocio
from src.ui.comunes import (
    avisar_y_recargar, exigir_catalogo, mostrar_aviso_pendiente, selector_fecha, selector_producto,
    selector_tienda,
)
from src.ui.estilos import (
    ICONOS, aviso, encabezado, estado_vacio, fecha as ffecha, num, seccion, sugerencia, tarjeta,
)

usuario = proteger_pagina("apertura")
encabezado("Apertura del día", "Registre el saldo inicial de pares por producto al abrir la tienda.",
           ICONOS["apertura"])
mostrar_aviso_pendiente()
tiendas, productos = exigir_catalogo()

with tarjeta("filtros"):
    c1, c2 = st.columns(2)
    dia = selector_fecha("ap_fecha", c1)
    tienda_id, tienda_nombre = selector_tienda(tiendas, "ap_tienda", c2)

st.write("")
tab_uno, tab_todos = st.tabs([":material/counter_1: Un producto", ":material/storefront: Toda la tienda"])

with tab_uno, tarjeta("uno", "Apertura de un producto", icono="inventory_2"):
    producto = selector_producto(productos, "ap_producto")
    with obtener_sesion() as s:
        propuesto = inv.proponer_saldo_inicial(s, dia, tienda_id, int(producto["id"]))
        existente = inv.obtener_apertura(s, dia, tienda_id, int(producto["id"]))
    if existente:
        aviso(f"Este producto ya tiene apertura el {ffecha(dia)}: {existente.saldo_inicial} pares.", "info")
    else:
        if propuesto is not None:
            sugerencia(f"Se propone el conteo del cierre de ayer: <b>{propuesto} pares</b>.")
        with st.form("form_apertura", clear_on_submit=False, border=False):
            saldo = st.number_input("Saldo inicial (pares)", min_value=0, step=1, value=int(propuesto or 0))
            if st.form_submit_button("Registrar apertura", type="primary", icon=":material/check:"):
                try:
                    with obtener_sesion() as s:
                        inv.registrar_apertura(s, dia, tienda_id, int(producto["id"]), int(saldo), usuario.id)
                    avisar_y_recargar(f"Apertura registrada: {producto['codigo']} con {num(saldo)} pares en {tienda_nombre}.")
                except ErrorNegocio as exc:
                    aviso(str(exc), "error")

with tab_todos, tarjeta("todos", "Abrir toda la tienda",
                        "Se propone el cierre de ayer de cada producto; ajuste lo que haga falta.", "storefront"):
    with obtener_sesion() as s:
        filas = []
        for _, p in productos.iterrows():
            ya = inv.obtener_apertura(s, dia, tienda_id, int(p["id"]))
            prop = inv.proponer_saldo_inicial(s, dia, tienda_id, int(p["id"]))
            filas.append({"id": int(p["id"]), "Código": p["codigo"], "Producto": p["nombre"],
                          "Saldo inicial": int(ya.saldo_inicial if ya else (prop or 0)),
                          "Estado": "Ya abierto" if ya else "Pendiente"})
    plantilla = pd.DataFrame(filas)
    pendientes = plantilla[plantilla["Estado"] == "Pendiente"]
    if pendientes.empty:
        estado_vacio(f"Todos los productos de {tienda_nombre} ya están abiertos el {ffecha(dia)}.", "task_alt")
    else:
        editado = st.data_editor(
            pendientes, hide_index=True, width="stretch", key="ap_editor",
            column_config={
                "id": None,
                "Saldo inicial": st.column_config.NumberColumn(min_value=0, step=1, required=True),
            },
            disabled=["Código", "Producto", "Estado"],
        )
        if st.button(f"Abrir {len(pendientes)} productos de {tienda_nombre}", type="primary",
                     icon=":material/lock_open:"):
            try:
                saldos = {int(r["id"]): int(r["Saldo inicial"]) for _, r in editado.iterrows()}
                with obtener_sesion() as s:
                    creadas, omitidas = inv.abrir_tienda_completa(s, dia, tienda_id, usuario.id, saldos)
                avisar_y_recargar(f"Se abrieron {creadas} productos" + (f" ({omitidas} ya estaban abiertos)." if omitidas else "."))
            except ErrorNegocio as exc:
                aviso(str(exc), "error")

seccion(f"Aperturas del {ffecha(dia)}", tienda_nombre)
with obtener_sesion() as s:
    tabla = inv.tabla_aperturas(s, dia, tienda_id)
with tarjeta("tabla"):
    if tabla.empty:
        estado_vacio("Todavía no hay aperturas registradas para esta fecha y tienda.", "inventory_2")
    else:
        tabla["Registrado"] = pd.to_datetime(tabla["Registrado"]).dt.strftime("%d/%m/%Y %H:%M")
        st.dataframe(tabla.drop(columns="Tienda"), hide_index=True, width="stretch",
                     column_config={"Saldo inicial": st.column_config.NumberColumn(format="%d pares")})
        st.caption(f"Total: **{num(int(tabla['Saldo inicial'].sum()))} pares** en {len(tabla)} productos.")
