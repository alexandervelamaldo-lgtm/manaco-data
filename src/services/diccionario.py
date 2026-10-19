"""Diccionario de datos del Excel de comercio exterior y marcado de claves repetidas.

Responde a la Estación 2 del caso: "revisar el diccionario de datos, tipos de variables,
valores faltantes y registros agregados". Solo depende de pandas, así que se puede usar
tanto en el tablero como en la exportación a Excel.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

#: Columna del Excel → (tipo, descripción). El rango y los faltantes se calculan con los datos.
DICCIONARIO: dict[str, tuple[str, str]] = {
    "País_reportante": (
        "Texto (categórica)",
        "País que informa el comercio. En esta base es siempre España: sirve como referencia "
        "internacional, no describe el mercado boliviano.",
    ),
    "Flujo_comercial": (
        "Texto (categórica)",
        "Sentido del comercio visto desde el país reportante: Importación o Exportación.",
    ),
    "Año": (
        "Entero",
        "Año del registro. La cantidad de registros por año es desigual, así que no sirve para medir tendencias.",
    ),
    "Código_SA6": (
        "Entero (código)",
        "Partida del Sistema Armonizado a 6 dígitos. Enlaza el Excel con la categoría del catálogo de "
        "Manaco: 640411 Deportivo, 640399 Caucho y cuero, 640420 Cuero.",
    ),
    "Categoría_calzado": (
        "Texto (categórica)",
        "Descripción oficial de la partida SA6.",
    ),
    "Socio_comercial": (
        "Texto (categórica)",
        "País proveedor (en importación) o de destino (en exportación). Un socio 'Mundo' sería un total "
        "agregado y se excluiría para no contar dos veces.",
    ),
    "Valor_miles_USD": (
        "Decimal",
        "Valor comercial en miles de dólares (Valor_USD ÷ 1000).",
    ),
    "Cantidad_pares": (
        "Entero",
        "Número de pares comerciados.",
    ),
    "Valor_USD": (
        "Decimal",
        "Valor comercial en dólares. Es un valor aduanero: no incluye aranceles, transporte ni el margen "
        "del comerciante, así que no equivale al precio al consumidor.",
    ),
    "Valor_USD_por_par": (
        "Decimal (calculada)",
        "Valor_USD ÷ Cantidad_pares: valor aduanero aproximado de cada par.",
    ),
}


def _num(valor: float, decimales: int = 0) -> str:
    """Número con formato boliviano: punto de miles y coma decimal."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "_").replace(".", ",").replace("_", ".")


def _rango(serie: pd.Series, es_codigo: bool = False) -> str:
    """Resumen legible de los valores de una columna."""
    datos = serie.dropna()
    if datos.empty:
        return "Sin datos"
    if pd.api.types.is_numeric_dtype(datos) and not es_codigo:
        minimo, maximo = datos.min(), datos.max()
        if pd.api.types.is_integer_dtype(datos) or (datos % 1 == 0).all():
            if maximo < 10000:  # años: sin separador de miles
                return f"{int(minimo)} a {int(maximo)}"
            return f"{_num(minimo)} a {_num(maximo)}"
        return f"{_num(minimo, 2)} a {_num(maximo, 2)}"
    distintos = sorted(datos.astype(str).unique())
    if len(distintos) <= 3:
        return " · ".join(distintos)
    return f"{len(distintos)} valores distintos (p. ej. {', '.join(distintos[:3])})"


def construir_diccionario(datos: pd.DataFrame) -> pd.DataFrame:
    """Tabla del diccionario de datos a partir del Excel (con sus nombres de columna originales).

    Devuelve una fila por columna del Excel con su tipo, su significado, el rango de valores
    observado y la cantidad de valores faltantes.
    """
    filas = []
    for columna, (tipo, descripcion) in DICCIONARIO.items():
        serie = datos[columna] if columna in datos else pd.Series(dtype="object")
        filas.append({
            "Columna": columna,
            "Tipo": tipo,
            "Descripción": descripcion,
            "Valores observados": _rango(serie, es_codigo=columna.startswith("Código")),
            "Faltantes": int(serie.isna().sum()) if columna in datos else len(datos),
        })
    return pd.DataFrame(filas, columns=["Columna", "Tipo", "Descripción", "Valores observados", "Faltantes"])


def marcar_claves_repetidas(datos: pd.DataFrame, clave: Sequence[str]) -> pd.Series:
    """True en todas las filas cuya clave aparece más de una vez (no solo en las repetidas)."""
    return datos.duplicated(subset=list(clave), keep=False)
