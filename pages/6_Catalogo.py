"""Alta, edición y baja de productos y tiendas."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.auth import proteger_pagina
from src.config import CATEGORIAS_SA6, CIUDADES, TIPOS_TIENDA
from src.db import obtener_sesion
from src.models import Producto, Tienda
from src.ui.comunes import avisar_y_recargar, mostrar_aviso_pendiente
from src.ui.estilos import (
    ICONOS, aviso, chip, encabezado, estado_vacio, ficha_producto, grilla, ico, seccion, tarjeta,
)

proteger_pagina("catalogo")
encabezado("Catálogo", "Administre los productos y las tiendas. La baja desactiva sin borrar el historial.",
           ICONOS["catalogo"])
mostrar_aviso_pendiente()

tab_prod, tab_tiendas = st.tabs([":material/steps: Productos", ":material/storefront: Tiendas"])

# --- Productos ---------------------------------------------------------------
with tab_prod:
    with obtener_sesion() as s:
        productos = pd.DataFrame([{
            "id": p.id, "Código": p.codigo_modelo, "Nombre": p.nombre, "Categoría": p.categoria,
            "SA6": p.codigo_sa6, "Talla": p.talla, "Color": p.color, "Precio (Bs)": p.precio_venta_bs,
            "Costo (Bs)": p.costo_bs, "Activo": p.activo,
        } for p in s.scalars(select(Producto).order_by(Producto.codigo_modelo)).all()],
            columns=["id", "Código", "Nombre", "Categoría", "SA6", "Talla", "Color", "Precio (Bs)", "Costo (Bs)", "Activo"])

    if productos.empty:
        with tarjeta("prod-vacio"):
            estado_vacio("No hay productos. Agregue el primero abajo.", "steps")
    else:
        activos = int(productos["Activo"].sum())
        seccion(f"{len(productos)} productos", f"{activos} activos · {len(productos) - activos} dados de baja")
        grilla([ficha_producto(r["Código"], r["Nombre"], r["Categoría"], r["Talla"], r["Color"],
                               r["Precio (Bs)"], bool(r["Activo"])) for _, r in productos.iterrows()])
        with tarjeta("prod-tabla", "Editar productos", "Cambie los datos en la tabla y guarde. "
                     "Desmarque «Activo» para dar de baja.", "edit"):
            editado = st.data_editor(
                productos, hide_index=True, width="stretch", key="cat_prod_editor",
                disabled=["id", "Código", "SA6"],
                column_config={
                    "id": None,
                    "SA6": st.column_config.NumberColumn(format="%d"),
                    "Categoría": st.column_config.SelectboxColumn(options=list(CATEGORIAS_SA6), required=True),
                    "Precio (Bs)": st.column_config.NumberColumn(min_value=0, format="localized"),
                    "Costo (Bs)": st.column_config.NumberColumn(min_value=0, format="localized"),
                    "Activo": st.column_config.CheckboxColumn(help="Desmarque para dar de baja"),
                },
            )
            if st.button("Guardar cambios de productos", type="primary", icon=":material/save:"):
                with obtener_sesion() as s:
                    for _, fila in editado.iterrows():
                        p = s.get(Producto, int(fila["id"]))
                        p.nombre = str(fila["Nombre"]).strip() or p.nombre
                        p.categoria = fila["Categoría"]
                        p.codigo_sa6 = CATEGORIAS_SA6[fila["Categoría"]]
                        p.talla, p.color = str(fila["Talla"]), str(fila["Color"])
                        p.precio_venta_bs, p.costo_bs = float(fila["Precio (Bs)"]), float(fila["Costo (Bs)"])
                        p.activo = bool(fila["Activo"])
                avisar_y_recargar("Productos actualizados.")

    st.write("")
    with tarjeta("prod-nuevo", "Nuevo producto", icono="add_circle"), \
            st.form("nuevo_producto", clear_on_submit=True, border=False):
        a, b, c = st.columns(3)
        codigo = a.text_input("Código de modelo", placeholder="MAN-DEP-005")
        nombre = b.text_input("Nombre", placeholder="Zapatilla Urbana")
        categoria = c.selectbox("Categoría", list(CATEGORIAS_SA6))
        d, e, f, g = st.columns(4)
        talla = d.text_input("Talla", value="40")
        color = e.text_input("Color", value="Negro")
        precio = f.number_input("Precio de venta (Bs)", min_value=0.0, step=10.0, value=299.0)
        costo = g.number_input("Costo (Bs)", min_value=0.0, step=10.0, value=160.0)
        if st.form_submit_button("Agregar producto", type="primary", icon=":material/add:"):
            if not codigo.strip() or not nombre.strip():
                aviso("El código y el nombre son obligatorios.", "error")
            else:
                try:
                    with obtener_sesion() as s:
                        s.add(Producto(codigo_modelo=codigo.strip().upper(), nombre=nombre.strip(), categoria=categoria,
                                       codigo_sa6=CATEGORIAS_SA6[categoria], talla=talla.strip(), color=color.strip(),
                                       precio_venta_bs=precio, costo_bs=costo))
                    avisar_y_recargar(f"Producto {codigo.strip().upper()} agregado.")
                except IntegrityError:
                    aviso(f"Ya existe un producto con el código {codigo.strip().upper()}.", "error")

# --- Tiendas -----------------------------------------------------------------
with tab_tiendas:
    with obtener_sesion() as s:
        tiendas = pd.DataFrame([{
            "id": t.id, "Nombre": t.nombre, "Ciudad": t.ciudad, "Tipo": t.tipo, "Activo": t.activo,
        } for t in s.scalars(select(Tienda).order_by(Tienda.nombre)).all()],
            columns=["id", "Nombre", "Ciudad", "Tipo", "Activo"])

    if tiendas.empty:
        with tarjeta("tiendas-vacio"):
            estado_vacio("No hay tiendas. Agregue la primera abajo.", "storefront")
    else:
        seccion(f"{len(tiendas)} tiendas y almacenes")
        grilla([
            f'<div class="md-ficha{"" if r["Activo"] else " inactiva"}"><div class="cab">'
            f'<span class="cod">{ico("storefront")} {r["Nombre"]}</span>{chip(r["Tipo"], "azul")}</div>'
            f'<div class="det">{ico("location_on")} {r["Ciudad"]}{"" if r["Activo"] else " · dada de baja"}</div></div>'
            for _, r in tiendas.iterrows()
        ])
        with tarjeta("tiendas-tabla", "Editar tiendas", icono="edit"):
            editadas = st.data_editor(
                tiendas, hide_index=True, width="stretch", key="cat_tiendas_editor", disabled=["id"],
                column_config={
                    "id": None,
                    "Ciudad": st.column_config.SelectboxColumn(options=list(CIUDADES), required=True),
                    "Tipo": st.column_config.SelectboxColumn(options=list(TIPOS_TIENDA), required=True),
                    "Activo": st.column_config.CheckboxColumn(help="Desmarque para dar de baja"),
                },
            )
            if st.button("Guardar cambios de tiendas", type="primary", icon=":material/save:"):
                try:
                    with obtener_sesion() as s:
                        for _, fila in editadas.iterrows():
                            t = s.get(Tienda, int(fila["id"]))
                            t.nombre, t.ciudad, t.tipo = str(fila["Nombre"]).strip(), fila["Ciudad"], fila["Tipo"]
                            t.activo = bool(fila["Activo"])
                    avisar_y_recargar("Tiendas actualizadas.")
                except IntegrityError:
                    aviso("Dos tiendas no pueden tener el mismo nombre.", "error")

    st.write("")
    with tarjeta("tienda-nueva", "Nueva tienda", icono="add_business"), \
            st.form("nueva_tienda", clear_on_submit=True, border=False):
        a, b, c = st.columns(3)
        nombre_t = a.text_input("Nombre", placeholder="Tienda Prado")
        ciudad = b.selectbox("Ciudad", list(CIUDADES))
        tipo = c.selectbox("Tipo", list(TIPOS_TIENDA))
        if st.form_submit_button("Agregar tienda", type="primary", icon=":material/add:"):
            if not nombre_t.strip():
                aviso("El nombre es obligatorio.", "error")
            else:
                try:
                    with obtener_sesion() as s:
                        s.add(Tienda(nombre=nombre_t.strip(), ciudad=ciudad, tipo=tipo))
                    avisar_y_recargar(f"Tienda {nombre_t.strip()} agregada.")
                except IntegrityError:
                    aviso(f"Ya existe una tienda llamada {nombre_t.strip()}.", "error")
