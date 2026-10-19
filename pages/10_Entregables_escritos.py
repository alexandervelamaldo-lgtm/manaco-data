"""Entregables escritos del caso: problemas priorizados, síntesis, ficha y recomendación."""

from __future__ import annotations

import streamlit as st

from src.auth import proteger_pagina
from src.ui.estilos import ICONOS, encabezado, nota, seccion, tarjeta

proteger_pagina("entregables")
encabezado(
    "Entregables escritos",
    "Los 4 textos que exige la rúbrica del caso, con las cifras que ya calcula el sistema.",
    ICONOS["entregables"],
)

tab1, tab2, tab3, tab4 = st.tabs([
    ":material/priority_high: 1. Problemas prioritarios",
    ":material/summarize: 2. Síntesis ejecutiva",
    ":material/description: 3. Ficha de una página",
    ":material/fact_check: 4. Recomendación ejecutiva",
])

with tab1:
    seccion("Problemas prioritarios", "5 problemas, con su justificación y los datos que ya usa el sistema")
    with tarjeta("problemas"):
        st.markdown(
            "| N.º | Problema | Justificación | Datos necesarios |\n"
            "| --- | --- | --- | --- |\n"
            "| 1 | **Inventario sin control diario en tienda** | El sistema ya detectó un caso real: "
            "*\"Faltan 2 pares de MAN-DEP-001 en Tienda Prado (esperado 38, contado 36)\"*. Sin alerta diaria, "
            "la merma solo se nota en el cierre contable mensual. | Saldo inicial, ventas del día, conteo de "
            "cierre, histórico de diferencias por tienda (Historial, `cierres`). |\n"
            "| 2 | **Datos de mercado externo y ventas internas desintegrados** | El cruce ya hecho muestra que "
            "Deportivo importa ~3 veces lo que exporta: una dependencia de oferta externa antes invisible. | "
            "Comercio exterior limpio (230 de 240 filas), catálogo con código SA6, ventas por categoría "
            "(Tablero de mercado). |\n"
            "| 3 | **Presión creciente del mercado informal / contrabando** | La escasez de dólares eleva el "
            "tipo de cambio paralelo y abarata el calzado informal frente al de Manaco. El pronóstico sin "
            "ajustar sobreestima la demanda real. | Ventas formales por línea, tipo de cambio paralelo, precio "
            "de competidores informales, sensibilidad por línea (Pronóstico de demanda). |\n"
            "| 4 | **Producción sin cobertura ni calidad garantizadas** | El Prototipo de escenario puede "
            "mostrar defectos sobre la meta (3%) y cobertura bajo el 100% de la demanda proyectada, sin "
            "seguimiento formal hoy. | Lotes de producción mensual, incidencias de calidad por lote, metas de "
            "producción (`fact_produccion`, `fact_calidad`). |\n"
            "| 5 | **Calidad de la ingesta de datos de sucursales** | El indicador \"rechazo en ingesta\" "
            "(meta ≤3%) existe porque los archivos de sucursal traen errores que distorsionan los reportes de "
            "gerencia si no se corrigen a tiempo. | Bitácora de ingesta por sucursal, reglas de validación, "
            "archivo fuente de cada carga (`log_ingesta`). |"
        )

with tab2:
    seccion("Diagnóstico de datos", "Síntesis ejecutiva: 3 hallazgos, 2 limitaciones y 1 pregunta estratégica")
    with tarjeta("hallazgos", "3 hallazgos", icono="lightbulb"):
        st.markdown(
            "1. **El control de inventario pasa de reactivo a preventivo.** El sistema compara lo contado "
            "contra lo esperado y genera una alerta inmediata (*\"Faltan 2 pares de MAN-DEP-001…\"*), algo que "
            "antes solo se descubría al cierre contable.\n"
            "2. **Deportivo es la línea más expuesta a la oferta externa.** Importa ~3 veces lo que exporta y "
            "tiene la mayor sensibilidad estimada al mercado informal (0,35 frente a 0,20 y 0,10 de las otras "
            "dos líneas): es donde una decisión de precio o producción pesa más.\n"
            "3. **Ajustar el pronóstico por presión informal reduce el error, no lo aumenta.** El backtest "
            "muestra un MAPE ajustado menor o igual al MAPE sin ajustar: ignorar la competencia informal "
            "sobreestima la demanda formal de forma sistemática."
        )
    with tarjeta("limitaciones", "2 limitaciones", icono="warning"):
        st.markdown(
            "1. **La referencia de mercado es española, no boliviana**, y el valor por par es un valor "
            "aduanero, no el precio al consumidor: sirve como referencia internacional, no como retrato del "
            "mercado boliviano.\n"
            "2. **El pronóstico y el prototipo de escenario corren sobre datos simulados** "
            "(`pronostico.py`, `seed_solucion.py`): el sistema real solo tiene ~30 días de ventas, "
            "insuficiente para estimar estacionalidad o fijar metas con rigor estadístico."
        )
    nota(
        "1 pregunta estratégica",
        "¿Qué mezcla de producción por línea debe planificar Manaco para los próximos 6 meses si la presión "
        "del mercado informal sigue la trayectoria actual del tipo de cambio paralelo, y qué tanto de la "
        "brecha de precio frente a ese mercado informal está dispuesta a absorber sin sacrificar margen?",
        icono="help",
    )

with tab3:
    seccion("Propuesta estratégica", "Ficha de una página")
    with tarjeta("ficha"):
        st.markdown(
            "**Problema:** Manaco pierde control del inventario diario en tienda y no integra sus datos "
            "internos con el mercado externo, lo que le impide anticipar la presión del mercado informal.\n\n"
            "**Solución — Manaco Data:** (1) control diario de apertura–venta–cierre con alerta automática de "
            "faltante/sobrante, apoyado en conteo por foto con IA; (2) tablero de mercado que cruza comercio "
            "exterior con ventas internas; (3) pronóstico de demanda ajustado por presión informal, con un "
            "prototipo de escenario para simular decisiones antes de tomarlas.\n\n"
            "**3 objetivos SMART / KPI:**\n"
            "- Reducir a menos del 5% los cierres con diferencia por tienda en 3 meses. *KPI:* % de cierres "
            "`Correcto` (Historial).\n"
            "- Que el 100% de las tiendas registren apertura, venta y cierre todos los días durante el primer "
            "mes. *KPI:* cierres hechos / aperturas del día (Inicio).\n"
            "- Mantener el MAPE ajustado por mercado informal por debajo del MAPE sin ajustar en cada línea, "
            "revisado cada mes. *KPI:* MAPE base vs. ajustado (Pronóstico de demanda).\n\n"
            "**Responsables:** Gerencia comercial (metas y alertas), Encargado de tienda (apertura, ventas, "
            "cierre), Administrador/TI (catálogo, usuarios, carga del Excel y migración a producción).\n\n"
            "**Riesgos:** falta de disciplina en el registro diario; fallos del conteo por foto con zapatos "
            "amontonados o poca luz; decisiones tomadas sobre datos **[Simulado]** sin validarlos antes contra "
            "ventas reales; límite de escala de un solo servidor SQLite sin HTTPS."
        )

with tab4:
    seccion("Decisión financiera / mercado", "Recomendación ejecutiva")
    with tarjeta("alternativas", "2 alternativas comparadas", icono="balance"):
        st.markdown(
            "| | Alternativa A — Competir por precio | Alternativa B — Diferenciar por calidad y "
            "disponibilidad |\n"
            "| --- | --- | --- |\n"
            "| Acción | Bajar el precio para cerrar la brecha frente al mercado informal. | Mantener el "
            "precio; bajar defectos y asegurar cobertura de producción. |\n"
            "| Palanca | Indicador \"Brecha vs. mercado informal\" (meta ≤20%). | Indicadores \"Tasa de "
            "defectos\" (≤3%) y \"Cobertura de producción\" (≥100%). |\n"
            "| Control | Baja: depende del tipo de cambio paralelo, fuera del control de Manaco. | Alta: son "
            "procesos internos de producción. |\n"
            "| Riesgo principal | Guerra de precios contra un competidor sin los costos formales de Manaco. | "
            "Que la diferenciación no se perciba si no se comunica junto con el esfuerzo de calidad. |"
        )
    nota(
        "Acción comercial recomendada: Alternativa B",
        "Cerrar la brecha de precio es una carrera que Manaco no gana con los datos que hoy tiene: la brecha "
        "se mueve con el tipo de cambio paralelo, que no controla, y el competidor informal no carga sus "
        "costos formales. La tasa de defectos y la cobertura de producción son palancas internas que el "
        "Prototipo de escenario ya mide mes a mes: invertir ahí protege la marca sin entrar en una guerra de "
        "precios que Manaco no puede sostener.",
        icono="check_circle",
    )
    with tarjeta("indicadores", "3 indicadores de seguimiento", icono="monitoring"):
        st.markdown(
            "1. **Cobertura de producción vs. demanda proyectada** (meta ≥100%) — Prototipo de escenario.\n"
            "2. **Tasa de defectos de producción** (meta ≤3%) — Prototipo de escenario.\n"
            "3. **% de cierres de inventario correctos por tienda** — Historial / Inicio."
        )

nota(
    "De dónde salen estos textos",
    "Las cifras de inventario y comercio exterior son reales y ya están limpias en el sistema. Las de "
    "producción, calidad y mercado local vienen del pronóstico y el prototipo de escenario, y están "
    "etiquetadas <b>[Simulado]</b> o <b>[Supuesto]</b> en el código: reemplácelas por historia real de Manaco "
    "antes de comprometer presupuesto con estos objetivos. Versión completa en "
    "<code>docs/ENTREGABLES_ESCRITOS.md</code>.",
    icono="science",
)
