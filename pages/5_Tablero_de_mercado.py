"""Tablero del mercado de calzado (Excel limpio) integrado con los datos internos."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.auth import proteger_pagina
from src.config import SA6_A_CATEGORIA
from src.db import obtener_sesion
from src.services import etl
from src.services import inventario as inv
from src.ui import graficos
from src.ui.estilos import (
    ICONOS, banner_kpis, bs, encabezado, estado_vacio, flujo_filas, linea_tiempo, nota, num, seccion, tarjeta,
    tarjeta_kpi,
)

proteger_pagina("tablero")
encabezado("Tablero de mercado", "Comercio exterior de calzado (Excel limpio) junto con las ventas de Manaco.",
           ICONOS["tablero"])

with obtener_sesion() as s:
    todos = etl.leer_comercio_db(s, solo_validos=False)
    bitacora = etl.leer_bitacora_db(s)
    ventas = inv.tabla_ventas(s)

if todos.empty:
    with tarjeta("vacio"):
        estado_vacio("No hay datos de comercio exterior. Ejecute python scripts/init_db.py para cargar el Excel.",
                     "dataset")
    st.stop()

todos["categoria"] = todos["codigo_sa6"].map(SA6_A_CATEGORIA).fillna(todos["categoria_calzado"])
validos = todos[todos["registro_valido"]].copy()
SIN_BARRA = {"displayModeBar": False}

tab_mercado, tab_internos, tab_limpieza = st.tabs(
    [":material/public: Mercado", ":material/storefront: Datos internos", ":material/cleaning_services: Limpieza de datos"])

# --- Mercado -----------------------------------------------------------------
with tab_mercado:
    with tarjeta("filtros", "Filtros", f"Base limpia: {num(len(validos))} registros válidos de {num(len(todos))}",
                 "tune"):
        f1, f2, f3, f4, f5 = st.columns([1, 1, 1.1, 1.1, 1.95])
        anios = f1.multiselect("Año", sorted(validos["anio"].unique()), placeholder="Todos")
        flujos = f2.multiselect("Flujo", sorted(validos["flujo_comercial"].unique()), placeholder="Todos")
        categorias = f3.multiselect("Categoría", sorted(validos["categoria"].unique()), placeholder="Todas")
        socios = f4.multiselect("Socio", sorted(validos["socio_comercial"].unique()), placeholder="Todos")
        metrica = f5.segmented_control("Métrica", list(graficos.METRICAS), default="Valor USD", key="tab_metrica",
                                       help="Compare: las conclusiones cambian según se mida valor o volumen.") \
            or "Valor USD"
    df = validos
    if anios:
        df = df[df["anio"].isin(anios)]
    if flujos:
        df = df[df["flujo_comercial"].isin(flujos)]
    if categorias:
        df = df[df["categoria"].isin(categorias)]
    if socios:
        df = df[df["socio_comercial"].isin(socios)]

    imp = df[df["flujo_comercial"] == "Importación"]
    exp = df[df["flujo_comercial"] == "Exportación"]
    v_imp, v_exp = imp["valor_usd"].sum() / 1e6, exp["valor_usd"].sum() / 1e6
    pares = df["cantidad_pares"].sum()
    por_par = df["valor_usd"].sum() / pares if pares else 0
    saldo = v_exp - v_imp

    st.write("")
    banner_kpis([
        ("Importado (M USD)", num(v_imp, 1), f"{num(len(imp))} registros", "rojo"),
        ("Exportado (M USD)", num(v_exp, 1), f"{num(len(exp))} registros", "azul"),
        ("Saldo comercial (M USD)", num(saldo, 1), "Déficit" if saldo < 0 else "Superávit",
         "naranja" if saldo < 0 else "verde"),
        ("Pares (millones)", num(pares / 1e6, 1), f"valor por par US$ {num(por_par, 2)}", "morado"),
    ])

    with tarjeta("g1"):
        st.plotly_chart(graficos.grafico_import_export(df, metrica), width="stretch", theme=None, config=SIN_BARRA)
    st.write("")
    with tarjeta("g2"):
        st.plotly_chart(graficos.grafico_top_socios(df, metrica), width="stretch", theme=None, config=SIN_BARRA)
    st.write("")
    with tarjeta("g3"):
        st.plotly_chart(graficos.grafico_valor_por_par(df), width="stretch", theme=None, config=SIN_BARRA)

    cobertura = validos.groupby("anio").size()
    nota(
        "Limitaciones de estos datos",
        "<ul>"
        "<li>El país reportante es <b>España</b>, no Bolivia: sirve como referencia del mercado internacional, "
        "no describe el mercado boliviano.</li>"
        "<li>El <b>valor por par</b> es un valor declarado en aduana, <b>no el precio al consumidor</b>.</li>"
        "<li>La <b>cobertura por año es desigual</b>: "
        + ", ".join(f"{a}: {n} registros" for a, n in cobertura.items())
        + ". Comparar años directamente puede engañar.</li>"
        "<li>Se cuentan solo los 30 socios incluidos en el archivo; no es el total mundial.</li></ul>",
        icono="report",
    )

# --- Datos internos ----------------------------------------------------------
with tab_internos:
    if ventas.empty:
        with tarjeta("internos-vacio"):
            estado_vacio("Aún no hay ventas internas registradas.", "receipt_long",
                         ("Ir a Ventas", "pages/2_Ventas.py", "point_of_sale"), clave="internos")
    else:
        i1, i2, i3 = st.columns(3)
        with i1:
            tarjeta_kpi("Ventas totales", bs(ventas["Importe"].sum(), 0), icono="payments", color="verde")
        with i2:
            tarjeta_kpi("Pares vendidos", num(int(ventas["Cantidad"].sum())), icono="shopping_bag", color="azul")
        with i3:
            tarjeta_kpi("Precio medio por par", bs(ventas["Importe"].sum() / ventas["Cantidad"].sum()),
                        icono="sell", color="morado")
        st.write("")
        with tarjeta("ventas-cat"):
            st.plotly_chart(graficos.grafico_ventas_categoria(ventas), width="stretch", theme=None, config=SIN_BARRA)

        internos = ventas.groupby("Categoría").agg(Pares=("Cantidad", "sum"), Ventas_Bs=("Importe", "sum"))
        internos["Precio medio (Bs/par)"] = internos["Ventas_Bs"] / internos["Pares"]
        externos = pd.DataFrame({
            "Import_MUSD": validos[validos["flujo_comercial"] == "Importación"]
            .groupby("categoria")["valor_usd"].sum() / 1e6,
            "Mediana_USD_par": validos.groupby("categoria")["valor_usd_por_par"].median(),
        })
        cruce = internos.join(externos, how="outer").rename_axis("Categoría").reset_index().rename(columns={
            "Ventas_Bs": "Ventas (Bs)", "Import_MUSD": "Importación España (M USD)",
            "Mediana_USD_par": "Mediana mercado (US$/par)",
        })
        seccion("Cruce: Manaco frente al mercado de referencia",
                "Las mismas categorías (código SA6) en las ventas internas y en el comercio exterior")
        with tarjeta("cruce"):
            st.dataframe(
                cruce, hide_index=True, width="stretch",
                column_config={
                    "Pares": st.column_config.NumberColumn(format="%d"),
                    "Ventas (Bs)": st.column_config.NumberColumn(format="localized"),
                    "Precio medio (Bs/par)": st.column_config.NumberColumn(format="localized"),
                    "Importación España (M USD)": st.column_config.NumberColumn(format="localized"),
                    "Mediana mercado (US$/par)": st.column_config.NumberColumn(format="localized"),
                },
            )

# --- Limpieza ----------------------------------------------------------------
with tab_limpieza:
    flujo_filas(len(todos), len(validos), len(todos) - len(validos))
    izq, der = st.columns([1.1, 1], gap="medium")
    with izq:
        seccion("Reglas aplicadas", "Cada regla queda registrada en la bitácora de limpieza")
        hitos = []
        for _, r in bitacora.iterrows():
            if r["Regla"] == "Resumen":
                tipo = "info"
            elif r["Regla"] == "Claves repetidas" and r["Filas afectadas"]:
                tipo = "alerta"
            else:
                tipo = "ok"
            hitos.append((f"{r['Regla']} · {num(int(r['Filas afectadas']))} filas", r["Detalle"], tipo))
        linea_tiempo(hitos)
    with der:
        seccion("Registros descartados", "Claves repetidas: se conserva la primera aparición")
        descartados = todos[~todos["registro_valido"]]
        with tarjeta("descartados"):
            if descartados.empty:
                estado_vacio("No se descartó ningún registro.", "verified")
            else:
                st.dataframe(
                    descartados[["flujo_comercial", "anio", "categoria", "socio_comercial", "valor_usd"]]
                    .rename(columns={"flujo_comercial": "Flujo", "anio": "Año", "categoria": "Categoría",
                                     "socio_comercial": "Socio", "valor_usd": "Valor USD"}),
                    hide_index=True, width="stretch",
                    column_config={"Año": st.column_config.NumberColumn(format="%d"),
                                   "Valor USD": st.column_config.NumberColumn(format="localized")},
                )
