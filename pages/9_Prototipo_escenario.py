"""Prototipo de escenario (sección 4 del caso): filtros, indicadores y sliders sobre
datos [Simulado], réplica del prototipo publicado por el equipo."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from sqlalchemy import select

from src.auth import proteger_pagina
from src.config import SA6_A_CATEGORIA
from src.db import obtener_sesion
from src.models import Producto
from src.services import etl
from src.services import pronostico as pr
from src.ui import graficos
from src.ui.estilos import ICONOS, encabezado, estado_vacio, nota, num, seccion, tarjeta, tarjeta_kpi

proteger_pagina("escenario")
encabezado(
    "Prototipo de escenario",
    "Réplica del prototipo publicado en el caso: filtros, indicadores y sliders sobre datos simulados.",
    ICONOS["escenario"],
)

SIN_BARRA = {"displayModeBar": False}

# Metas de referencia del escenario. [Supuesto]: no son metas oficiales de Manaco.
META_DEFECTOS_PCT = 3.0
META_RECHAZO_PCT = 3.0
META_BRECHA_PCT = 20.0
META_COBERTURA_PCT = 100.0

with obtener_sesion() as s:
    produccion = etl.leer_produccion_db(s)
    calidad = etl.leer_calidad_db(s)
    mercado_local = etl.leer_mercado_local_db(s)
    ingesta = etl.leer_ingesta_db(s)
    comercio = etl.leer_comercio_db(s)
    precios_manaco = pd.DataFrame(
        [{"categoria": p.categoria, "precio_venta_bs": p.precio_venta_bs}
         for p in s.scalars(select(Producto).where(Producto.activo.is_(True))).all()],
    )

if produccion.empty or mercado_local.empty:
    with tarjeta("vacio"):
        estado_vacio("No hay datos simulados del escenario. Ejecute python scripts/seed_solucion.py.", "dataset")
    st.stop()

with tarjeta("filtros", "Filtros y escenario", "Ajuste la presión informal y el tipo de cambio paralelo", "tune"):
    f1, f2, f3 = st.columns([1.2, 1, 1])
    linea = f1.segmented_control("Línea", pr.LINEAS, default=pr.LINEAS[0], key="esc_linea") or pr.LINEAS[0]

    historial = pr.generar_historial(linea, meses=24)
    tipo_cambio_actual = float(mercado_local["tipo_cambio_paralelo"].tail(12).mean())
    presion_actual = float(historial["Presion_informal"].iloc[-1])

    tipo_cambio = f2.slider("Tipo de cambio paralelo (Bs/USD)", 6.96, 15.0, round(tipo_cambio_actual, 2), 0.1,
                            key="esc_tc", help="Afecta la brecha de precio frente al mercado informal.")
    presion_informal = f3.slider("Presión del mercado informal (escenario)", 0.0, 0.95, round(presion_actual, 2),
                                 0.05, key="esc_presion", help="Afecta el pronóstico de demanda ajustado.")

futuro = pr.pronosticar(historial, linea, meses_adelante=6, presion_informal=presion_informal)
resultado = pr.backtest(historial, linea)

prod_linea = produccion[produccion["categoria"] == linea]
cal_linea = calidad[calidad["categoria"] == linea]
precio_manaco = float(precios_manaco.loc[precios_manaco["categoria"] == linea, "precio_venta_bs"].mean() or 0)

ventas_proyectadas = float(futuro["Pronostico_ajustado"].iloc[0])
meta_ventas = float(historial["Pares_vendidos"].tail(12).mean())

ultimo_mes_prod = prod_linea["fecha"].max() if not prod_linea.empty else None
produccion_ultimo_mes = prod_linea.loc[prod_linea["fecha"] == ultimo_mes_prod, "pares"].sum()
cobertura_pct = produccion_ultimo_mes / ventas_proyectadas * 100 if ventas_proyectadas else 0.0

meses_recientes = sorted(prod_linea["fecha"].unique())[-3:]
pares_recientes = prod_linea.loc[prod_linea["fecha"].isin(meses_recientes), "pares"].sum()
defectos_recientes = cal_linea.loc[cal_linea["fecha"].isin(meses_recientes), "defectos"].sum()
tasa_defectos_pct = defectos_recientes / pares_recientes * 100 if pares_recientes else 0.0

# [Supuesto]: el precio informal escala junto con el tipo de cambio paralelo elegido en el slider.
precio_competidor_base = float(mercado_local["precio_competidor_bs"].tail(12).mean())
precio_competidor_escenario = precio_competidor_base * (tipo_cambio / tipo_cambio_actual)
brecha_pct = ((precio_manaco - precio_competidor_escenario) / precio_competidor_escenario * 100
              if precio_competidor_escenario else 0.0)

ingesta_reciente = ingesta.sort_values("fecha").tail(18)
rechazo_pct = (ingesta_reciente["filas_rechazadas"].sum() / ingesta_reciente["filas_leidas"].sum() * 100
              if ingesta_reciente["filas_leidas"].sum() else 0.0)

st.write("")
seccion("Indicadores frente a metas de referencia", "[Supuesto]: metas ilustrativas del equipo, no oficiales")
i1, i2, i3, i4, i5 = st.columns(5)
with i1:
    tarjeta_kpi("Ventas proyectadas", num(ventas_proyectadas), f"meta: {num(meta_ventas)} pares/mes",
                icono="trending_up", color="rojo" if ventas_proyectadas < meta_ventas else "verde",
                tendencia="sube" if ventas_proyectadas >= meta_ventas else "baja",
                alerta=ventas_proyectadas < meta_ventas)
with i2:
    tarjeta_kpi("Cobertura de producción", f"{num(cobertura_pct, 0)}%", f"meta: ≥{num(META_COBERTURA_PCT, 0)}%",
                icono="precision_manufacturing", color="verde" if cobertura_pct >= META_COBERTURA_PCT else "rojo",
                tendencia="sube" if cobertura_pct >= META_COBERTURA_PCT else "baja",
                alerta=cobertura_pct < META_COBERTURA_PCT)
with i3:
    tarjeta_kpi("Tasa de defectos", f"{num(tasa_defectos_pct, 1)}%", f"meta: ≤{num(META_DEFECTOS_PCT, 0)}%",
                icono="rule", color="verde" if tasa_defectos_pct <= META_DEFECTOS_PCT else "rojo",
                tendencia="sube" if tasa_defectos_pct > META_DEFECTOS_PCT else "baja",
                alerta=tasa_defectos_pct > META_DEFECTOS_PCT)
with i4:
    tarjeta_kpi("Brecha vs. mercado informal", f"{num(brecha_pct, 0)}%", f"meta: ≤{num(META_BRECHA_PCT, 0)}%",
                icono="price_change", color="verde" if brecha_pct <= META_BRECHA_PCT else "rojo",
                tendencia="sube" if brecha_pct > META_BRECHA_PCT else "baja", alerta=brecha_pct > META_BRECHA_PCT)
with i5:
    tarjeta_kpi("Rechazo en ingesta de datos", f"{num(rechazo_pct, 1)}%", f"meta: ≤{num(META_RECHAZO_PCT, 0)}%",
                icono="fact_check", color="verde" if rechazo_pct <= META_RECHAZO_PCT else "rojo",
                tendencia="sube" if rechazo_pct > META_RECHAZO_PCT else "baja", alerta=rechazo_pct > META_RECHAZO_PCT)

st.write("")
with tarjeta("g-demanda", "Demanda proyectada", "Con el escenario de presión informal elegido arriba"):
    st.plotly_chart(graficos.grafico_pronostico(historial, futuro, linea), width="stretch", theme=None,
                     config=SIN_BARRA)

st.write("")
seccion("Resumen por línea", "Pronóstico a 6 meses con el escenario de presión informal elegido")
filas_tabla = []
for ln in pr.LINEAS:
    h = pr.generar_historial(ln, meses=24)
    f = pr.pronosticar(h, ln, meses_adelante=6, presion_informal=presion_informal)
    r = pr.backtest(h, ln)
    filas_tabla.append({
        "Línea": ln, "Sensibilidad informal": pr.SENSIBILIDAD_INFORMAL[ln],
        "Sin ajustar (6 meses)": int(f["Pronostico_base"].sum()),
        "Ajustado (6 meses)": int(f["Pronostico_ajustado"].sum()),
        "MAPE sin ajustar": round(r.mape_base, 1), "MAPE ajustado": round(r.mape_ajustado, 1),
    })
with tarjeta("tabla-lineas"):
    st.dataframe(
        pd.DataFrame(filas_tabla), hide_index=True, width="stretch",
        column_config={
            "Sensibilidad informal": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f"),
            "Sin ajustar (6 meses)": st.column_config.NumberColumn(format="%d"),
            "Ajustado (6 meses)": st.column_config.NumberColumn(format="%d"),
            "MAPE sin ajustar": st.column_config.NumberColumn(format="%.1f%%"),
            "MAPE ajustado": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )

if not comercio.empty:
    st.write("")
    comercio["categoria"] = comercio["codigo_sa6"].map(SA6_A_CATEGORIA).fillna(comercio["categoria_calzado"])
    with tarjeta("g-referencia", "Referencia externa", "Valor por par en el comercio exterior (España), por categoría"):
        st.plotly_chart(graficos.grafico_valor_por_par(comercio[comercio["registro_valido"]]), width="stretch",
                         theme=None, config=SIN_BARRA)

st.write("")
seccion("Estado de ingesta de datos por sucursal", "Últimas cargas registradas")
with tarjeta("tabla-ingesta"):
    if ingesta.empty:
        estado_vacio("No hay registros de ingesta.", "upload_file")
    else:
        tabla_ingesta = ingesta.head(12).rename(columns={
            "fecha": "Fecha", "sucursal": "Sucursal", "archivo": "Archivo", "filas_leidas": "Filas leídas",
            "filas_corregidas": "Corregidas", "filas_rechazadas": "Rechazadas",
        })
        st.dataframe(
            tabla_ingesta, hide_index=True, width="stretch",
            column_config={
                "Fecha": st.column_config.DateColumn(format="MMM YYYY"),
                "Filas leídas": st.column_config.NumberColumn(format="%d"),
                "Corregidas": st.column_config.NumberColumn(format="%d"),
                "Rechazadas": st.column_config.NumberColumn(format="%d"),
            },
        )

nota(
    "Datos simulados en este prototipo",
    "<ul>"
    "<li><b>[Simulado]</b> Esta página reconstruye el prototipo de la sección 4 del caso con datos simulados: "
    "no hay 24 meses de historia real de ventas, producción, calidad ni mercado local en el sistema.</li>"
    "<li><b>[Supuesto]</b> Las 5 metas de los indicadores y la relación entre el tipo de cambio paralelo y el "
    "precio del mercado informal son estimaciones del equipo, no cifras oficiales de Manaco.</li>"
    "<li>La sección <b>Referencia externa</b> usa el Excel de comercio exterior de España (datos reales de ese "
    "archivo), que sirve solo como referencia del mercado internacional.</li></ul>",
    icono="science",
)
