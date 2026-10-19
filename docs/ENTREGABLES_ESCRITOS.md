# Entregables escritos del caso Manaco

Este documento reúne los **4 entregables de redacción** que exige la rúbrica de las
estaciones y que no están cubiertos por el código (el sistema resuelve el "qué
construir"; aquí se resuelve el "qué decir"). Cada estación cita la página o el
servicio del sistema **Manaco Data** que la respalda, para que las cifras sean
trazables y no inventadas.

---

## Estación 1 — Problemas prioritarios

| N.º | Problema | Justificación | Datos necesarios |
| --- | --- | --- | --- |
| 1 | **Inventario sin control diario en tienda** (diferencias entre lo esperado y lo contado) | El sistema ya detectó un caso real validado: *"Faltan 2 pares de MAN-DEP-001 en Tienda Prado (esperado 38, contado 36)"*. Sin una alerta diaria, esta merma solo se nota en el cierre contable mensual, cuando ya es tarde para investigar la causa. | Saldo inicial por tienda/producto, ventas del día, conteo físico de cierre (foto o manual), histórico de diferencias por tienda (página Historial, tabla `cierres`). |
| 2 | **Datos de mercado externo y ventas internas desintegrados** | Manaco no tenía forma de cruzar su desempeño comercial con el comportamiento del mercado de calzado. El cruce ya hecho muestra que la categoría **Deportivo importa ~3 veces lo que exporta**: una señal de dependencia estructural de oferta externa que antes era invisible. | Base de comercio exterior limpia (230 de 240 registros válidos), catálogo de productos con su código SA6, ventas internas por categoría (página Tablero de mercado, tabla `comercio_exterior`). |
| 3 | **Presión creciente del mercado informal / contrabando sobre la demanda formal** | La escasez de dólares eleva el tipo de cambio paralelo, lo que abarata el calzado informal frente al de Manaco (descuento típico del 5-20% sobre el precio formal). El pronóstico sin ajustar sobreestima la demanda real porque ignora esta fuga de clientes hacia el mercado informal. | Historial de ventas formales por línea, tipo de cambio paralelo, precio de competidores informales, sensibilidad de cada línea al mercado informal (página Pronóstico de demanda). |
| 4 | **Producción sin cobertura ni calidad garantizadas frente a la demanda proyectada** | El prototipo de escenario puede mostrar una tasa de defectos por encima de la meta (3%) y una cobertura de producción por debajo del 100% de la demanda proyectada, sin que exista hoy un proceso formal que lo vigile mes a mes. | Lotes de producción mensual por línea, incidencias de calidad por lote, metas oficiales de gerencia de producción (página Prototipo de escenario, tablas `fact_produccion` y `fact_calidad`). |
| 5 | **Calidad de la ingesta de datos que llega de las sucursales** | El indicador "rechazo en ingesta" (meta ≤3%) existe porque los archivos que suben las sucursales traen errores; si no se corrigen a tiempo, distorsionan cualquier reporte que gerencia use para decidir. | Bitácora de ingesta por sucursal (filas leídas, corregidas, rechazadas), reglas de validación aplicadas, archivo fuente de cada carga (página Prototipo de escenario, tabla `log_ingesta`). |

---

## Estación 2 — Diagnóstico de datos: síntesis ejecutiva

### 3 hallazgos

1. **El control de inventario pasa de reactivo a preventivo.** El sistema compara
   automáticamente lo contado contra lo esperado (saldo inicial − vendido) y genera
   una alerta inmediata y legible (*"Faltan 2 pares de MAN-DEP-001…"*), algo que antes
   solo se descubría al cierre contable, cuando ya no se puede rastrear el origen de
   la diferencia.
2. **La categoría Deportivo es la más expuesta a la oferta externa.** Al cruzar las
   230 filas válidas del Excel de comercio exterior con las ventas internas, Deportivo
   importa alrededor de **3 veces lo que exporta**, y es también la línea con mayor
   sensibilidad estimada al mercado informal (0,35 frente a 0,20 de Caucho y cuero y
   0,10 de Cuero). Es la línea donde una decisión de precio o de producción tiene más
   impacto.
3. **Ajustar el pronóstico por presión informal reduce el error, no lo aumenta.** El
   backtest del módulo de pronóstico muestra que el MAPE del pronóstico *ajustado*
   por mercado informal es menor o igual que el del pronóstico *sin ajustar*, lo que
   confirma que ignorar la competencia informal no es una simplificación inocente:
   sobreestima sistemáticamente la demanda formal esperada.

### 2 limitaciones

1. **La referencia de mercado es española, no boliviana.** La base de comercio
   exterior usada en el tablero reporta a España como país; sirve como referencia
   internacional de categorías y proporciones (import. vs. export.), pero el valor
   por par es un **valor aduanero**, no el precio al consumidor, y no debe leerse
   como "el precio del mercado boliviano".
2. **El pronóstico y el prototipo de escenario corren sobre datos simulados.** El
   sistema real solo tiene ~30 días de ventas registradas: insuficiente para medir
   estacionalidad, tendencia o fijar metas con rigor estadístico. El historial de 24
   meses, la producción, la calidad y el mercado local están explícitamente
   etiquetados **[Simulado]** o **[Supuesto]** en el código (`pronostico.py`,
   `seed_solucion.py`) y deben reemplazarse por datos reales antes de usarlos para
   comprometer presupuesto o producción.

### 1 pregunta estratégica

> ¿Qué mezcla de producción por línea debe planificar Manaco para los próximos 6
> meses si la presión del mercado informal sigue la trayectoria actual del tipo de
> cambio paralelo, y qué tanto de la brecha de precio frente a ese mercado informal
> está dispuesta a absorber sin sacrificar margen?

---

## Estación 3 — Propuesta estratégica: ficha de una página

| Campo | Contenido |
| --- | --- |
| **Problema** | Manaco pierde control del inventario diario en tienda y no integra sus datos internos con el comportamiento del mercado externo, lo que le impide anticipar y responder a la presión creciente del mercado informal sobre su demanda. |
| **Solución** | **Manaco Data**: (1) control diario de apertura–venta–cierre con alerta automática de faltante/sobrante, apoyado en conteo por foto con IA (YOLO-World); (2) tablero de mercado que cruza comercio exterior con ventas internas por categoría; (3) módulo de pronóstico de demanda ajustado por presión del mercado informal, con un prototipo de escenario para simular tipo de cambio y presión informal antes de decidir. |
| **Objetivo 1 (SMART)** | Reducir a **menos del 5%** la proporción de cierres con diferencia (faltante o sobrante) por tienda en los 3 meses siguientes a la puesta en marcha. **KPI:** % de cierres `Correcto` (página Historial / dona de Inicio). |
| **Objetivo 2 (SMART)** | Lograr que el **100% de las tiendas** registren apertura, venta y cierre todos los días durante el primer mes de uso (0 cierres sin apertura, 0 aperturas sin cierre al final del día). **KPI:** cierres hechos / aperturas del día (tarjeta KPI de Inicio). |
| **Objetivo 3 (SMART)** | Mantener el **MAPE del pronóstico ajustado por mercado informal por debajo del MAPE sin ajustar** en cada línea de producto, revisado mes a mes, para confirmar que el ajuste sigue mejorando la planificación de compras y producción. **KPI:** MAPE base vs. MAPE ajustado (página Pronóstico de demanda, backtest). |
| **Responsables** | **Gerencia comercial:** define metas de venta y revisa alertas pendientes (rol `gerencia`). **Encargado de tienda:** registra apertura, ventas y cierre diario (rol `encargado`). **Administrador / TI:** mantiene catálogo, usuarios, carga del Excel de comercio exterior y la migración futura del sistema a producción (rol `administrador`). |
| **Riesgos** | (1) Que el personal de tienda no registre apertura/cierre con disciplina diaria, ya que es el dato de entrada del que depende todo lo demás. (2) Que el conteo por foto falle con zapatos amontonados o poca luz, obligando a un respaldo manual constante. (3) Que se tomen decisiones de producción o precio con los datos **[Simulado]** del pronóstico/escenario sin antes validarlos contra ventas reales. (4) Que el sistema, al ser local con SQLite y un solo servidor, no escale a toda la red de tiendas sin una migración previa a PostgreSQL. |

---

## Estación 4 — Decisión financiera/mercado: recomendación ejecutiva

### Las 2 alternativas comparadas

| | **Alternativa A — Competir por precio** | **Alternativa B — Diferenciar por calidad y disponibilidad** |
| --- | --- | --- |
| Acción | Bajar el precio de venta para cerrar la brecha frente al mercado informal y recuperar volumen. | Mantener el precio; invertir en bajar la tasa de defectos y asegurar que la producción cubra el 100% de la demanda proyectada. |
| Palanca que usa | El indicador **"Brecha vs. mercado informal"** del Prototipo de escenario (meta ≤20%). | Los indicadores **"Tasa de defectos"** (meta ≤3%) y **"Cobertura de producción"** (meta ≥100%) del mismo prototipo. |
| Qué tan controlable es | Baja: la brecha depende del tipo de cambio paralelo, que Manaco no controla, y el mercado informal puede volver a abaratarse si el dólar sube más. | Alta: defectos y cobertura dependen de procesos internos de producción que Manaco sí puede gestionar directamente. |
| Riesgo principal | Guerra de precios con un competidor sin los costos formales (impuestos, planilla) de Manaco: el margen se erosiona más rápido de lo que se recupera volumen. | Que la diferenciación no sea percibida si no se comunica (empaque, garantía, puntos de venta) junto con el esfuerzo de calidad. |

### Acción comercial recomendada

**Alternativa B — Diferenciar por calidad y disponibilidad.** Cerrar la brecha de
precio frente al mercado informal es una carrera que Manaco no gana con los datos
que hoy tiene: la brecha se mueve con el tipo de cambio paralelo (fuera de su
control) y el competidor informal no carga los mismos costos formales, por lo que
una baja de precio sostenida comprime el margen sin garantizar que el mercado
informal no vuelva a abaratarse. En cambio, la tasa de defectos y la cobertura de
producción son palancas **internas** que el Prototipo de escenario ya mide mes a
mes: invertir ahí protege la marca (menos devoluciones, menos quiebres de stock)
sin entrar en una guerra de precios que Manaco no puede sostener.

### 3 indicadores de seguimiento

1. **Cobertura de producción vs. demanda proyectada** (meta ≥100%) — Prototipo de escenario.
2. **Tasa de defectos de producción** (meta ≤3%) — Prototipo de escenario.
3. **% de cierres de inventario correctos por tienda** (sin faltante ni sobrante) — Historial / Inicio.

---

*Nota: las cifras de este documento provienen de los datos reales ya limpios del
sistema (comercio exterior, inventario) o de los módulos de pronóstico y escenario,
cuyos datos de producción, calidad y mercado local están explícitamente etiquetados
**[Simulado]** o **[Supuesto]** en el código. Antes de usar los objetivos y
recomendaciones de este documento para comprometer presupuesto real, reemplace esos
datos simulados por historia real de Manaco (ver "Próximos pasos" en el README).*
