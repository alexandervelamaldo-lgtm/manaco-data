"""Genera docs/Solucion_Manaco_Data.docx con la explicación completa de la solución."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor, Cm

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_PATH = BASE_DIR / "docs" / "Solucion_Manaco_Data.docx"

ROJO = RGBColor(0xB3, 0x26, 0x1E)
GRIS = RGBColor(0x57, 0x53, 0x4E)


def set_cell_text(cell, text, bold=False, color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(10)
    if color:
        run.font.color.rgb = color


def tabla(doc, encabezados, filas):
    t = doc.add_table(rows=1, cols=len(encabezados))
    t.style = "Light Grid Accent 1"
    for i, h in enumerate(encabezados):
        set_cell_text(t.rows[0].cells[i], h, bold=True, color=RGBColor(0xFF, 0xFF, 0xFF))
    for fila in filas:
        row = t.add_row()
        for i, val in enumerate(fila):
            set_cell_text(row.cells[i], val)
    doc.add_paragraph()
    return t


def h1(doc, texto):
    p = doc.add_heading(texto, level=1)
    for run in p.runs:
        run.font.color.rgb = ROJO


def h2(doc, texto):
    p = doc.add_heading(texto, level=2)
    for run in p.runs:
        run.font.color.rgb = GRIS


def parrafo(doc, texto, bold=False, italic=False):
    p = doc.add_paragraph()
    run = p.add_run(texto)
    run.bold = bold
    run.italic = italic
    return p


def bullet(doc, texto):
    doc.add_paragraph(texto, style="List Bullet")


def numerado(doc, texto):
    doc.add_paragraph(texto, style="List Number")


def nota_caja(doc, titulo, texto):
    p = doc.add_paragraph()
    run = p.add_run(f"{titulo}: ")
    run.bold = True
    run.font.color.rgb = ROJO
    p.add_run(texto)


doc = Document()

estilo_normal = doc.styles["Normal"]
estilo_normal.font.name = "Calibri"
estilo_normal.font.size = Pt(11)

# --- Portada ------------------------------------------------------------
titulo = doc.add_heading("Manaco Data", level=0)
titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
for run in titulo.runs:
    run.font.color.rgb = ROJO

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = sub.add_run(
    "Sistema de control de inventario, mercado y pronóstico de demanda\npara Manaco (calzado, Bolivia)"
)
run.font.size = Pt(14)
run.font.color.rgb = GRIS

doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run("Documento de explicación de la solución — caso Manaco").italic = True

doc.add_page_break()

# --- 1. Resumen ejecutivo ------------------------------------------------
h1(doc, "1. Resumen ejecutivo")
parrafo(
    doc,
    "Manaco Data es la solución construida para el caso Manaco: una aplicación web (Streamlit) con "
    "base de datos propia que resuelve los 4 problemas centrales identificados en el caso — falta de "
    "control diario de inventario en tienda, desconexión entre datos de mercado externo y ventas "
    "internas, falta de ajuste del pronóstico de demanda por presión del mercado informal, y falta de "
    "seguimiento formal de producción y calidad frente a la demanda proyectada.",
)
parrafo(
    doc,
    "El sistema cubre el ciclo completo: carga y limpieza de datos (ETL), registro diario de "
    "inventario con alertas automáticas, conteo asistido por visión artificial (IA), cruce de datos de "
    "comercio exterior con ventas internas, pronóstico de demanda ajustado por mercado informal, un "
    "prototipo de escenario para simular decisiones antes de tomarlas, y los 4 entregables escritos que "
    "exige la rúbrica del caso, ya redactados dentro del propio sistema.",
)

# --- 2. Arquitectura ------------------------------------------------------
h1(doc, "2. Arquitectura del sistema")
tabla(
    doc,
    ["Capa", "Tecnología", "Función"],
    [
        ("Interfaz", "Streamlit (multipágina)", "Páginas por rol, navegación con st.navigation + st.Page"),
        ("Lógica de negocio", "Python (src/services/)", "Reglas de inventario, ETL, pronóstico, visión por computadora"),
        ("Datos", "SQLite (manaco.db) / PostgreSQL opcional", "Catálogo, tiendas, ventas, cierres, comercio exterior"),
        ("Autenticación", "src/auth.py", "Login y control de acceso por rol (proteger_pagina)"),
        ("IA", "YOLO-World (yolov8s-world.pt)", "Conteo de pares de zapatos por foto en el cierre de tienda"),
    ],
)
parrafo(
    doc,
    "La base de datos usa SQLite por defecto (cero configuración) y puede apuntar a PostgreSQL "
    "configurando la variable de entorno DATABASE_URL, siguiendo la arquitectura propuesta en el caso.",
)

h2(doc, "2.1 Roles y permisos")
tabla(
    doc,
    ["Rol", "Puede ver"],
    [
        ("administrador", "Todo: catálogo, usuarios, carga de Excel, y las páginas de encargado y gerencia"),
        ("encargado", "Apertura, Ventas, Cierre y conteo (operación diaria de tienda)"),
        ("gerencia", "Inicio, Historial, Tablero de mercado, Pronóstico, Prototipo de escenario, Entregables escritos"),
    ],
)

# --- 3. Módulos funcionales ------------------------------------------------
h1(doc, "3. Módulos funcionales")

h2(doc, "3.1 Control diario de inventario")
parrafo(
    doc,
    "Cada tienda registra apertura (saldo inicial), ventas del día y cierre (conteo físico, manual o "
    "por foto con IA). El sistema calcula el saldo esperado (saldo inicial − vendido) y lo compara "
    "contra el conteo real, clasificando el resultado como Correcto, Faltante o Sobrante.",
)
nota_caja(
    doc,
    "Caso real detectado por el sistema",
    "\"Faltan 2 pares de MAN-DEP-001 en Tienda Prado (esperado 38, contado 36)\" — una diferencia que "
    "antes solo se habría notado en el cierre contable mensual.",
)

h2(doc, "3.2 Comercio exterior y tablero de mercado")
parrafo(
    doc,
    "El módulo de ETL (src/services/etl.py) limpia el Excel de comercio exterior de calzado "
    "(240 filas originales → 230 válidas), documentando cada regla de limpieza en una bitácora. El "
    "Tablero de mercado cruza esos datos con las ventas internas por categoría, usando el código del "
    "Sistema Armonizado (SA6) para enlazar el catálogo interno con las categorías del comercio exterior.",
)
bullet(doc, "Importación vs. exportación por categoría de calzado")
bullet(doc, "Top socios comerciales")
bullet(doc, "Valor por par (comparable entre categorías)")
parrafo(
    doc,
    "Hallazgo clave: la categoría Deportivo importa aproximadamente 3 veces lo que exporta, una señal "
    "de dependencia de oferta externa que antes era invisible para Manaco.",
)

h2(doc, "3.3 Pronóstico de demanda ajustado por mercado informal")
parrafo(
    doc,
    "El pronóstico de demanda por línea de producto (Deportivo, Caucho y cuero, Cuero) se ajusta por "
    "la presión del mercado informal/contrabando, usando una sensibilidad distinta por línea:",
)
tabla(
    doc,
    ["Línea de producto", "Sensibilidad al mercado informal"],
    [("Deportivo", "0.35 (la más expuesta)"), ("Caucho y cuero", "0.20"), ("Cuero", "0.10")],
)
parrafo(
    doc,
    "Un backtest compara el error del pronóstico ajustado contra el no ajustado (MAPE): el pronóstico "
    "ajustado por mercado informal obtiene un MAPE menor o igual, confirmando que ignorar la "
    "competencia informal sobreestima sistemáticamente la demanda formal.",
)

h2(doc, "3.4 Prototipo de escenario")
parrafo(
    doc,
    "Permite simular, con controles deslizantes (tipo de cambio paralelo y presión informal), el "
    "impacto sobre 5 indicadores clave antes de tomar una decisión real:",
)
tabla(
    doc,
    ["Indicador", "Meta"],
    [
        ("Ventas proyectadas", "Referencia de planificación"),
        ("Cobertura de producción", "≥ 100% de la demanda proyectada"),
        ("Tasa de defectos de producción", "≤ 3%"),
        ("Brecha de precio vs. mercado informal", "≤ 20%"),
        ("Rechazo en ingesta de datos de sucursal", "≤ 3%"),
    ],
)

h2(doc, "3.5 Entregables escritos (dentro del propio sistema)")
parrafo(
    doc,
    "Los 4 textos que exige la rúbrica del caso están redactados y disponibles en vivo dentro de la "
    "aplicación, en la página \"Entregables escritos\" (solo administrador y gerencia), con 4 pestañas:",
)
numerado(doc, "Problemas prioritarios — tabla de 5 problemas con justificación y datos necesarios.")
numerado(doc, "Síntesis ejecutiva — 3 hallazgos, 2 limitaciones y 1 pregunta estratégica.")
numerado(doc, "Ficha de una página — problema, solución, 3 objetivos SMART/KPI, responsables, riesgos.")
numerado(doc, "Recomendación ejecutiva — comparación de 2 alternativas y 3 indicadores de seguimiento.")

# --- 4. Los 5 problemas priorizados --------------------------------------
h1(doc, "4. Problemas priorizados")
tabla(
    doc,
    ["N.º", "Problema", "Justificación"],
    [
        ("1", "Inventario sin control diario en tienda", "La merma solo se nota en el cierre contable mensual sin una alerta diaria."),
        ("2", "Datos de mercado externo y ventas internas desintegrados", "Deportivo importa ~3 veces lo que exporta: dependencia antes invisible."),
        ("3", "Presión creciente del mercado informal / contrabando", "El pronóstico sin ajustar sobreestima la demanda real."),
        ("4", "Producción sin cobertura ni calidad garantizadas", "El escenario puede mostrar defectos sobre meta y cobertura bajo el 100%."),
        ("5", "Calidad de la ingesta de datos de sucursales", "Errores en los archivos de sucursal distorsionan los reportes de gerencia."),
    ],
)

# --- 5. Síntesis ejecutiva -------------------------------------------------
h1(doc, "5. Síntesis ejecutiva del diagnóstico")
h2(doc, "3 hallazgos")
numerado(doc, "El control de inventario pasa de reactivo a preventivo: el sistema genera una alerta inmediata en vez de descubrir la merma en el cierre contable.")
numerado(doc, "Deportivo es la línea más expuesta a la oferta externa y a la sensibilidad del mercado informal (0.35 frente a 0.20 y 0.10).")
numerado(doc, "Ajustar el pronóstico por presión informal reduce el error (MAPE), no lo aumenta: ignorar la competencia informal sobreestima la demanda formal.")

h2(doc, "2 limitaciones")
numerado(doc, "La referencia de comercio exterior usada es española, no boliviana, y es un valor aduanero, no el precio al consumidor.")
numerado(doc, "El pronóstico y el prototipo de escenario corren sobre datos simulados; el sistema real solo tiene ~30 días de ventas, insuficiente para estimar estacionalidad con rigor estadístico.")

h2(doc, "1 pregunta estratégica")
parrafo(
    doc,
    "¿Qué mezcla de producción por línea debe planificar Manaco para los próximos 6 meses si la presión "
    "del mercado informal sigue la trayectoria actual del tipo de cambio paralelo, y qué tanto de la "
    "brecha de precio frente a ese mercado informal está dispuesta a absorber sin sacrificar margen?",
    italic=True,
)

# --- 6. Ficha de una página -------------------------------------------------
h1(doc, "6. Ficha de propuesta estratégica")
tabla(
    doc,
    ["Campo", "Contenido"],
    [
        ("Problema", "Manaco pierde control del inventario diario en tienda y no integra sus datos internos con el mercado externo."),
        ("Solución", "Manaco Data: control diario con alertas, tablero de mercado cruzado, y pronóstico ajustado con prototipo de escenario."),
        ("Objetivo 1 (SMART)", "Reducir a menos del 5% los cierres con diferencia por tienda en 3 meses."),
        ("Objetivo 2 (SMART)", "100% de las tiendas registrando apertura, venta y cierre a diario en el primer mes."),
        ("Objetivo 3 (SMART)", "Mantener el MAPE ajustado por mercado informal por debajo del MAPE sin ajustar, cada mes."),
        ("Responsables", "Gerencia comercial, Encargado de tienda, Administrador/TI."),
        ("Riesgos", "Falta de disciplina en el registro diario; fallos del conteo por foto; decisiones sobre datos simulados sin validar; límite de escala de SQLite."),
    ],
)

# --- 7. Recomendación ejecutiva --------------------------------------------
h1(doc, "7. Recomendación ejecutiva")
tabla(
    doc,
    ["", "Alternativa A — Competir por precio", "Alternativa B — Diferenciar por calidad y disponibilidad"],
    [
        ("Acción", "Bajar el precio para cerrar la brecha informal.", "Mantener precio; bajar defectos y asegurar cobertura."),
        ("Control", "Baja (depende del tipo de cambio paralelo).", "Alta (procesos internos de producción)."),
        ("Riesgo principal", "Guerra de precios sin los costos formales del competidor informal.", "Que la diferenciación no se perciba si no se comunica."),
    ],
)
nota_caja(
    doc,
    "Acción comercial recomendada",
    "Alternativa B — Diferenciar por calidad y disponibilidad. La brecha de precio depende del tipo de "
    "cambio paralelo, fuera del control de Manaco; la tasa de defectos y la cobertura de producción son "
    "palancas internas que ya se miden mes a mes en el Prototipo de escenario.",
)
h2(doc, "3 indicadores de seguimiento")
numerado(doc, "Cobertura de producción vs. demanda proyectada (meta ≥100%).")
numerado(doc, "Tasa de defectos de producción (meta ≤3%).")
numerado(doc, "% de cierres de inventario correctos por tienda.")

# --- 8. Limitaciones y próximos pasos --------------------------------------
h1(doc, "8. Limitaciones y próximos pasos")
parrafo(
    doc,
    "Los datos de inventario y comercio exterior son reales y ya están limpios en el sistema. Los datos "
    "de producción, calidad y mercado local provienen del pronóstico y el prototipo de escenario, y "
    "están explícitamente etiquetados [Simulado] o [Supuesto] en el código. Antes de comprometer "
    "presupuesto real con los objetivos de este documento, deben reemplazarse por historia real de "
    "Manaco.",
)
bullet(doc, "Migrar de SQLite a PostgreSQL para soportar toda la red de tiendas.")
bullet(doc, "Recolectar al menos 12 meses de ventas reales para calibrar estacionalidad.")
bullet(doc, "Validar la sensibilidad al mercado informal con datos reales de precios de la competencia informal.")

doc.save(OUT_PATH)
print(f"Documento generado: {OUT_PATH}")
