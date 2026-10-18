"""Gráficos Plotly con la plantilla propia ``manaco``: títulos que concluyen y formato boliviano."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from src.ui.estilos import (
    ADVERTENCIA, COLOR_CATEGORIA, COLOR_ESTADO, ERROR, EXITO, INFO, PRIMARIO, TEXTO, TEXTO_2, num,
)

FUENTE = "Inter, Segoe UI, Helvetica, Arial, sans-serif"
FUENTE_TITULO = "Plus Jakarta Sans, Inter, sans-serif"
GRIS_BARRA = "#CBD5E1"

pio.templates["manaco"] = go.layout.Template(
    layout=go.Layout(
        font={"family": FUENTE, "size": 13, "color": TEXTO},
        title={"x": 0, "xanchor": "left", "font": {"family": FUENTE_TITULO, "size": 17, "color": TEXTO}},
        paper_bgcolor="#FFFFFF",  # las tarjetas son blancas; Streamlit cambia el transparente por el fondo de la app
        plot_bgcolor="#FFFFFF",
        colorway=[INFO, "#7C3AED", PRIMARIO, EXITO, ADVERTENCIA, TEXTO_2],
        xaxis={"showgrid": False, "zeroline": False, "showline": True, "linecolor": "#E5E7EB", "automargin": True,
               "ticks": "", "tickfont": {"color": TEXTO_2}, "title": {"font": {"color": TEXTO_2, "size": 12}}},
        yaxis={"showgrid": True, "gridcolor": "#EEF0F4", "zeroline": False, "showline": False, "automargin": True,
               "ticks": "", "tickfont": {"color": TEXTO_2}, "title": {"font": {"color": TEXTO_2, "size": 12}}},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1, "title": None,
                "font": {"color": TEXTO_2, "size": 12}},
        hoverlabel={"font_family": FUENTE, "bgcolor": "#111827", "font_color": "#FFFFFF", "bordercolor": "#111827"},
        separators=",.",
        margin={"l": 8, "r": 8, "t": 64, "b": 8},
        bargap=0.3,
    )
)
pio.templates.default = "manaco"

#: Nombre de métrica en la interfaz → (columna, etiqueta corta, decimales).
METRICAS: dict[str, tuple[str, str, int]] = {
    "Valor USD": ("valor_usd", "M USD", 1),
    "Cantidad de pares": ("cantidad_pares", "M pares", 1),
}


def _estilo(fig: go.Figure, titulo: str, alto: int = 400, subtitulo: str | None = None) -> go.Figure:
    """Aplica la plantilla, el título (la conclusión) y un subtítulo opcional."""
    texto = f"<b>{titulo}</b>"
    if subtitulo:
        texto += f"<br><span style='font-size:12px;color:{TEXTO_2};font-weight:400'>{subtitulo}</span>"
    fig.update_layout(template="manaco", title={"text": texto}, height=alto,
                      transition={"duration": 500, "easing": "cubic-in-out"})
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    return fig


def figura_vacia(mensaje: str = "No hay datos para mostrar con los filtros elegidos") -> go.Figure:
    """Figura en blanco con un mensaje centrado."""
    fig = go.Figure()
    fig.add_annotation(text=mensaje, showarrow=False, font={"size": 14, "color": TEXTO_2})
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return _estilo(fig, "Sin datos", alto=280)


# --- Inventario --------------------------------------------------------------

def grafico_diferencias(df: pd.DataFrame) -> go.Figure:
    """Pares faltantes y sobrantes por día (cierres con diferencia)."""
    if df.empty:
        return figura_vacia("Aún no hay cierres en los últimos 30 días")
    diario = df.assign(
        Faltantes=df["Diferencia"].clip(upper=0), Sobrantes=df["Diferencia"].clip(lower=0),
    ).groupby("Fecha", as_index=False)[["Faltantes", "Sobrantes"]].sum().sort_values("Fecha")
    # Plotly 7 envía los enteros como arreglos binarios; los negativos int64 no se dibujan bien.
    diario[["Faltantes", "Sobrantes"]] = diario[["Faltantes", "Sobrantes"]].astype(float)
    fig = go.Figure([
        go.Bar(x=diario["Fecha"], y=diario["Faltantes"], name="Faltantes", marker_color=ERROR,
               marker_cornerradius=5, hovertemplate="%{x|%d/%m/%Y}<br>%{y:.0f} pares<extra>Faltantes</extra>"),
        go.Bar(x=diario["Fecha"], y=diario["Sobrantes"], name="Sobrantes", marker_color=ADVERTENCIA,
               marker_cornerradius=5, hovertemplate="%{x|%d/%m/%Y}<br>+%{y:.0f} pares<extra>Sobrantes</extra>"),
    ])
    con_dif = int((df["Diferencia"] != 0).sum())
    neto = int(df["Diferencia"].sum())
    titulo = (
        f"{num(con_dif)} de {num(len(df))} cierres tuvieron diferencia; balance neto de {num(neto)} pares"
        if con_dif else f"Los {num(len(df))} cierres de los últimos 30 días cuadraron sin diferencias"
    )
    fig.update_layout(barmode="relative", bargap=0.25)
    fig.update_xaxes(tickformat="%d/%m", title=None)
    fig.update_yaxes(title="Pares", zeroline=True, zerolinecolor="#D1D5DB")
    return _estilo(fig, titulo, alto=340)


def grafico_estados(df: pd.DataFrame) -> go.Figure:
    """Dona con la cantidad de cierres por estado."""
    if df.empty:
        return figura_vacia("Aún no hay cierres")
    conteo = df["Estado"].value_counts().reindex(["Correcto", "Faltante", "Sobrante"]).fillna(0)
    total = int(conteo.sum())
    pct_ok = 100 * conteo["Correcto"] / total if total else 0
    fig = go.Figure(go.Pie(
        labels=conteo.index, values=conteo.values.astype(float), hole=0.68, sort=False, direction="clockwise",
        marker={"colors": [COLOR_ESTADO[e] for e in conteo.index], "line": {"color": "#FFFFFF", "width": 3}},
        textinfo="none", hovertemplate="%{label}<br>%{value:,.0f} cierres (%{percent})<extra></extra>",
    ))
    fig.add_annotation(text=f"<b>{num(pct_ok, 0)} %</b><br><span style='font-size:12px;color:{TEXTO_2}'>correctos</span>",
                       showarrow=False, font={"size": 26, "family": FUENTE_TITULO, "color": TEXTO})
    fig.update_layout(legend={"orientation": "h", "yanchor": "top", "y": -0.02, "xanchor": "center", "x": 0.5},
                      margin={"l": 8, "r": 8, "t": 56, "b": 8})
    return _estilo(fig, f"{num(pct_ok, 0)} % de los cierres cuadran", alto=330, subtitulo="Últimos 30 días")


def grafico_ventas_categoria(df: pd.DataFrame) -> go.Figure:
    """Ventas internas de Manaco en Bs por categoría."""
    if df.empty:
        return figura_vacia("Aún no hay ventas registradas")
    agg = df.groupby("Categoría", as_index=False).agg(Bs=("Importe", "sum"), Pares=("Cantidad", "sum"))
    agg = agg.sort_values("Bs")
    lider = agg.iloc[-1]
    pct = 100 * lider["Bs"] / agg["Bs"].sum()
    fig = go.Figure(go.Bar(
        x=agg["Bs"].astype(float), y=agg["Categoría"], orientation="h", marker_cornerradius=6,
        marker_color=[COLOR_CATEGORIA.get(c, GRIS_BARRA) for c in agg["Categoría"]],
        text=[f"Bs {num(v)}" for v in agg["Bs"]], textposition="outside", cliponaxis=False,
        customdata=agg["Pares"].astype(float),
        hovertemplate="%{y}<br>Bs %{x:,.0f}<br>%{customdata:,.0f} pares<extra></extra>",
    ))
    fig.update_xaxes(visible=False, range=[0, agg["Bs"].max() * 1.3])
    fig.update_yaxes(showgrid=False)
    return _estilo(fig, f"{lider['Categoría']} concentra el {num(pct, 0)} % de las ventas de Manaco", alto=300)


# --- Comercio exterior -------------------------------------------------------

def grafico_import_export(df: pd.DataFrame, metrica: str) -> go.Figure:
    """Barras agrupadas de importación frente a exportación por categoría, con la razón."""
    if df.empty:
        return figura_vacia()
    col, unidad, dec = METRICAS[metrica]
    tabla = df.pivot_table(index="categoria", columns="flujo_comercial", values=col, aggfunc="sum", fill_value=0)
    for flujo in ("Importación", "Exportación"):
        if flujo not in tabla.columns:
            tabla[flujo] = 0
    tabla = tabla[["Importación", "Exportación"]].astype(float) / 1e6
    tabla["razon"] = tabla["Importación"] / tabla["Exportación"].where(tabla["Exportación"] > 0)
    tabla = tabla.sort_values("Importación", ascending=False)
    colores = [COLOR_CATEGORIA.get(c, GRIS_BARRA) for c in tabla.index]
    fig = go.Figure([
        go.Bar(x=tabla.index, y=tabla["Importación"], name="Importación", marker_color=colores, marker_cornerradius=6,
               text=[num(v, dec) for v in tabla["Importación"]], textposition="outside", cliponaxis=False,
               hovertemplate=f"%{{x}}<br>%{{y:,.{dec}f}} {unidad}<extra>Importación</extra>"),
        go.Bar(x=tabla.index, y=tabla["Exportación"], name="Exportación", marker_cornerradius=6,
               marker={"color": [c + "55" for c in colores], "line": {"color": colores, "width": 1.5}},
               text=[num(v, dec) for v in tabla["Exportación"]], textposition="outside", cliponaxis=False,
               hovertemplate=f"%{{x}}<br>%{{y:,.{dec}f}} {unidad}<extra>Exportación</extra>"),
    ])
    for cat, fila in tabla.iterrows():
        texto = f"importa × {num(fila['razon'], 1)}" if pd.notna(fila["razon"]) else "sin export."
        fig.add_annotation(x=cat, y=max(fila["Importación"], fila["Exportación"]), text=f"<b>{texto}</b>",
                           showarrow=False, yshift=34, font={"color": TEXTO, "size": 12},
                           bgcolor="#F3F4F6", borderpad=4)
    razones = tabla["razon"].dropna()
    if razones.empty:
        titulo = "Importación frente a exportación por categoría"
    else:
        cat = razones.idxmax()
        importa = razones.max() >= 1
        veces = razones.max() if importa else 1 / razones.max()
        medida = "en valor" if col == "valor_usd" else "en pares"
        titulo = (f"En {cat.lower()} se {'importa' if importa else 'exporta'} {num(veces, 1)} veces "
                  f"lo que se {'exporta' if importa else 'importa'} ({medida})")
    fig.update_layout(barmode="group", bargap=0.28, bargroupgap=0.08, showlegend=False)
    fig.update_yaxes(title=unidad, rangemode="tozero", tickformat=",.0f",
                     range=[0, float(tabla[["Importación", "Exportación"]].max().max()) * 1.28])
    fig.update_xaxes(title=None)
    return _estilo(fig, titulo, alto=420, subtitulo="Barra llena: importación · barra clara: exportación")


def grafico_top_socios(df: pd.DataFrame, metrica: str, n: int = 6) -> go.Figure:
    """Dos paneles con los principales proveedores (import.) y destinos (export.)."""
    if df.empty:
        return figura_vacia()
    col, unidad, dec = METRICAS[metrica]
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Proveedores (importación)", "Destinos (exportación)"),
                        horizontal_spacing=0.2)
    lideres: list[str] = []
    for i, (flujo, color) in enumerate((("Importación", PRIMARIO), ("Exportación", INFO)), start=1):
        top = (df[df["flujo_comercial"] == flujo].groupby("socio_comercial")[col].sum()
               .nlargest(n).sort_values().astype(float) / 1e6)
        if top.empty:
            continue
        lideres.append(top.index[-1])
        colores = [color if s == top.index[-1] else GRIS_BARRA for s in top.index]
        fig.add_trace(go.Bar(
            x=top.values, y=top.index, orientation="h", marker_color=colores, marker_cornerradius=5, showlegend=False,
            text=[num(v, dec) for v in top.values], textposition="outside", cliponaxis=False,
            hovertemplate=f"%{{y}}<br>%{{x:,.{dec}f}} {unidad}<extra>{flujo}</extra>",
        ), row=1, col=i)
        fig.update_xaxes(range=[0, top.max() * 1.3], row=1, col=i)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(showgrid=False)
    titulo = (f"{lideres[0]} es el principal proveedor y {lideres[1]} el principal destino"
              if len(lideres) == 2 else f"Principales {n} socios comerciales")
    fig.update_annotations(font={"size": 13, "color": TEXTO_2}, yshift=6)
    _estilo(fig, titulo, alto=420, subtitulo=f"Top {n} por {metrica} ({unidad})")
    fig.update_layout(margin={"t": 110})
    return fig


def grafico_valor_por_par(df: pd.DataFrame) -> go.Figure:
    """Rango (mínimo–máximo) y mediana del valor por par en cada categoría."""
    if df.empty:
        return figura_vacia()
    est = df.groupby("categoria")["valor_usd_por_par"].agg(["min", "median", "max"]).astype(float).sort_values("median")
    fig = go.Figure()
    for cat, fila in est.iterrows():
        color = COLOR_CATEGORIA.get(cat, GRIS_BARRA)
        fig.add_trace(go.Scatter(x=[fila["min"], fila["max"]], y=[cat, cat], mode="lines+markers",
                                 line={"color": color + "66", "width": 6}, marker={"color": color + "99", "size": 10},
                                 showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=est["median"], y=est.index, mode="markers+text", name="Mediana",
        marker={"color": [COLOR_CATEGORIA.get(c, GRIS_BARRA) for c in est.index], "size": 18,
                "line": {"color": "white", "width": 3}},
        text=[f"US$ {num(v, 2)}" for v in est["median"]], textposition="top center",
        textfont={"family": FUENTE_TITULO, "size": 13, "color": TEXTO},
        customdata=est[["min", "max"]].values, showlegend=False,
        hovertemplate="%{y}<br>Mediana US$ %{x:,.2f}<br>Mín. US$ %{customdata[0]:,.2f} · "
                      "Máx. US$ %{customdata[1]:,.2f}<extra></extra>",
    ))
    cat_max = est["median"].idxmax()
    titulo = f"{cat_max} tiene el mayor valor por par (mediana US$ {num(est.loc[cat_max, 'median'], 2)})"
    fig.update_xaxes(title="US$ por par", rangemode="tozero", showgrid=True, gridcolor="#EEF0F4")
    fig.update_yaxes(title=None, showgrid=False, range=[-0.5, len(est) - 0.2])
    return _estilo(fig, titulo, alto=330, subtitulo="Punto: mediana · línea: del mínimo al máximo")
