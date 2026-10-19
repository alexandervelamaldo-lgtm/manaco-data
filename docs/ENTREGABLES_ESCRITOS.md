# Entregables escritos del caso Manaco

Este documento reúne los **4 entregables de redacción** que exige la rúbrica de las
estaciones y que no están cubiertos por el código (el sistema resuelve el "qué
construir"; aquí se resuelve el "qué decir"). Cada estación cita la página o el
servicio del sistema **Manaco Data** que la respalda, para que las cifras sean
trazables y no inventadas.

---

## Estación 1 — Problemas prioritarios

Cinco problemas que cubren las seis áreas que pide el caso, ordenados por impacto.

| N.º | Problema y área | Justificación | Datos necesarios |
| --- | --- | --- | --- |
| 1 | **Inventario sin control diario en tienda** · *Producción, inventarios y logística* | Sin conteo diario, una diferencia de stock solo se nota en el cierre contable mensual, cuando ya no se puede rastrear su causa. Ejemplo de la demo: *"Faltan 2 pares de MAN-DEP-001 en Tienda Prado (esperado 38, contado 36)"*. | Saldo inicial, ventas del día y conteo de cierre por tienda y producto; histórico de diferencias (Historial, `cierres`). |
| 2 | **Presión de la oferta importada y del mercado informal** · *Competitividad y mercado* | **Dato:** Deportivo importa 2,97 veces lo que exporta (Excel, 240 filas válidas). **Hipótesis a validar:** el calzado informal entra sin pagar aranceles ni impuestos, compite por precio y le quita ventas a Manaco. | Ventas reales por línea y mes, precios de la competencia formal e informal, tipo de cambio paralelo (Pronóstico de demanda, `ref_mercado_local`). |
| 3 | **Rentabilidad por línea sin medir** · *Rentabilidad y estructura de costos* | En el mercado de referencia el Cuero vale casi el doble por par (~41–45 USD frente a ~25), pero Manaco no sabe qué línea le deja más utilidad: no integra costos de producción, defectos, devoluciones, almacenamiento ni distribución. | Costo real por lote, costo de defectos y devoluciones, gastos de almacenamiento y distribución, precio real con descuentos (`fact_produccion`, `fact_calidad`). |
| 4 | **Cliente desconocido** · *Clientes, segmentación y marketing* | El sistema registra qué se vende, dónde y cuándo, pero no quién compra. Sin eso no se puede segmentar ni medir el canal digital que menciona el caso. | Tipo de cliente (edad, ciudad, segmento), frecuencia y monto de compra, canal (tienda o digital), motivos de devolución. |
| 5 | **Datos dispersos y sin responsables claros** · *Gestión organizacional y calidad de datos* | Mercado, ventas, inventario y calidad están separados, y los archivos de las sucursales llegan con errores. Si nadie responde por corregirlos, cualquier reporte de gerencia queda distorsionado. | Bitácora de ingesta por sucursal (filas leídas, corregidas y rechazadas), reglas de validación y un responsable por fuente de datos (`log_ingesta`, `bitacora_limpieza`). |

**Por qué este orden:** el 1 afecta a diario y ya tiene solución en marcha; el 2 y
el 3 definen en qué línea competir; el 4 y el 5 son la condición para que las
decisiones siguientes tengan datos confiables.

**Qué responde cada fuente:** el Excel de comercio exterior responde comparaciones
de categorías, socios y valor por par en un mercado de referencia; **no** responde
costos, márgenes, clientes ni ventas de Manaco. Eso exige datos internos.

---

## Estación 2 — Diagnóstico de datos: síntesis ejecutiva

**Tabla depurada y diccionario de datos:** están en *Tablero de mercado → Limpieza de
datos*, que muestra el diccionario de las 10 columnas y permite descargar la tabla
depurada en Excel (240 filas, con la marca de clave repetida y la bitácora de limpieza).

### 3 hallazgos

Los tres salen de la base de comercio exterior limpia: 240 filas válidas, de las
cuales 20 comparten clave con otra fila y se marcan para validarlas con la fuente.

1. **Deportivo es la categoría más dependiente de la importación.** Importa
   **2,97 veces** lo que exporta en valor y **2,91 veces** en pares. Como la
   proporción casi no cambia con la métrica, la conclusión es sólida: en esta línea
   la oferta importada domina el mercado de referencia.
2. **El calzado de cuero es un nicho de mayor valor por par.** Su valor aduanero
   ronda los **41–45 USD por par**, frente a unos **25 USD** de Deportivo y de Caucho
   y cuero. En volumen es pequeño (7,7 millones de pares importados frente a 498
   millones de Caucho y cuero), pero cada par vale casi el doble: es la señal más
   clara de dónde diferenciarse por calidad y no por precio.
3. **Medir por valor o por cantidad cambia quiénes son los proveedores relevantes.**
   Por categoría, el orden es el mismo con ambas métricas. Por socio, en cambio,
   **República Checa entra al top 6 de proveedores por pares, pero no por valor**,
   porque su calzado es el más barato de la base (unos 9 USD por par). Si solo se
   mira el valor, se pierden de vista los proveedores que compiten por precio.

### 2 limitaciones

1. **La referencia es española y el valor es aduanero.** Sirve para comparar
   categorías y proporciones, pero no representa el mercado boliviano ni el precio
   al consumidor, que incluye aranceles, transporte y margen del comerciante.
2. **La cobertura por año es desigual.** Hay 28 registros en 2020 y 82 en
   2024, así que cualquier "crecimiento" entre años refleja la cantidad de
   registros, no el mercado. Por eso no se sacan tendencias temporales.

### 1 pregunta estratégica

> Si Deportivo es la línea con más presión importada y Cuero la de mayor valor por
> par, ¿debe Manaco defender volumen en Deportivo o concentrar su diferenciación en
> Cuero? ¿Qué margen real por línea necesitaría ver para decidirlo?

### Respuestas a las 5 preguntas del caso

| Pregunta del caso | Respuesta con los datos |
| --- | --- |
| ¿Qué datos internos debería recopilar Manaco? | Ventas por producto, tienda y día (ya las registra el sistema); costos reales por lote; defectos y devoluciones con su motivo; datos del cliente (segmento, ciudad y canal); fechas de entrega; inventario por almacén; y precios reales con descuentos. |
| ¿Qué hipótesis sobre competencia, abastecimiento o diferenciación podría investigar? | Competencia: Deportivo depende de la importación (importa 2,97 veces lo que exporta), así que es la línea más expuesta al calzado importado barato. Abastecimiento: hay proveedores muy baratos por par (República Checa, unos 9 USD) que sirven de referencia de costo. Diferenciación: el Cuero vale casi el doble por par, lo que sugiere un nicho de calidad. |
| ¿Cómo varía el valor por par y por qué no es el precio al consumidor? | Va de 8 a 119 USD por registro; la mediana es de unos 47 USD en Cuero y unos 27 USD en Deportivo y en Caucho y cuero. Es un valor aduanero: no incluye aranceles, impuestos, transporte ni el margen del comerciante, así que el precio en tienda es mayor. |
| ¿Qué países son proveedores y destinos relevantes? | Proveedores, por valor: Grecia, Países Bajos, Vietnam, Irlanda, Turquía y Rumanía. Destinos, por valor: Indonesia, Vietnam, Eslovenia, Irlanda, Grecia y Austria. Son relevantes dentro de los 30 socios del archivo, no del comercio mundial. |
| ¿Qué categorías tienen mayor valor? ¿Cambia al comparar con la cantidad? | Caucho y cuero lidera en ambos flujos (11.709,7 M USD importados y 8.514,2 M USD exportados), seguida de Deportivo; Cuero es muy pequeña. Por categoría el orden no cambia con la cantidad de pares; por socio sí: República Checa entra al top 6 de proveedores por pares, pero no por valor. |

---

## Estación 3 — Propuesta estratégica: ficha de una página

| Campo | Contenido |
| --- | --- |
| **Problema** | Manaco no controla a diario su inventario en tienda ni mide la rentabilidad real de cada línea, y no cruza esos datos con el mercado. Así no puede decidir en qué línea competir frente a la oferta importada e informal. |
| **Solución analítica** | **Manaco Data**: (1) control diario de apertura, venta y cierre con alerta automática de faltante o sobrante, apoyado en conteo por foto con IA; (2) tablero de mercado que cruza comercio exterior con ventas internas por código SA6; (3) pronóstico de demanda y prototipo de escenario, que hoy demuestran el método con datos **[Simulado]** y se recalibran con ventas reales. **Decisión que apoya:** qué línea priorizar y cuánto producir. |
| **Datos que necesita** | Aperturas, ventas y cierres diarios (ya los registra); comercio exterior (ya cargado y limpio); costos por lote, defectos y devoluciones (hoy simulados, por reemplazar). |
| **Objetivo 1 — Inventario (SMART, 3 años)** | Bajar los cierres con diferencia a menos del **10%** al cierre del año 1, del **5%** al año 2 y del **3%** al año 3, en todas las tiendas. **KPI:** % de cierres `Correcto` por tienda (Historial, Inicio). |
| **Objetivo 2 — Datos reales (SMART, 3 años)** | **100%** de las tiendas con registro diario completo desde el mes 3; al año 2, **24 meses** de historia real que reemplacen los datos [Simulado]; al año 3, pronóstico por línea con error (MAPE) **menor al 15%** sobre ventas reales. **KPI:** % de tiendas con registro completo, meses de historia real y MAPE. |
| **Objetivo 3 — Calidad (SMART, 3 años)** | Bajar la tasa de defectos a **3%** o menos en todos los lotes al año 1, **2,5%** al año 2 y **2%** al año 3, y reducir a la mitad las devoluciones por costura y pegado de suela. **KPI:** tasa de defectos y devoluciones por lote (`fact_calidad`). |
| **Línea base** | Se mide en el primer mes de uso; las metas se recalibran con ese dato real. |
| **Responsables y coordinación** | **Gerencia General:** patrocina y revisa los 3 KPI en un comité mensual. **Gerencia Comercial:** metas de venta y atención de alertas (rol `gerencia`). **Gerencia de Producción:** defectos y cobertura. **Encargados de tienda:** registro diario (rol `encargado`). **Administración/TI:** sistema, catálogo, carga de datos y migración a PostgreSQL (rol `administrador`). |
| **Riesgo 1 y mitigación** | *Registro diario incompleto.* El cierre de inventario pasa a ser parte del cierre de caja, Inicio muestra los cierres pendientes y gerencia recibe un reporte semanal por tienda. |
| **Riesgo 2 y mitigación** | *Decidir con datos simulados.* Todo dato simulado lleva la etiqueta [Simulado], no se compromete presupuesto hasta tener 12 meses reales y las metas se recalibran con la línea base real. |
| **Otros riesgos** | El conteo por foto falla con poca luz o zapatos amontonados (respaldo: conteo manual); SQLite no escala a toda la red (migración a PostgreSQL en el año 2). |
| **Viabilidad** | El sistema ya funciona en una computadora local. El costo principal es el tiempo del personal para registrar a diario y, en el año 2, la migración a un servidor con PostgreSQL. |

---

## Estación 4 — Decisión financiera/mercado: recomendación ejecutiva

### Lectura de los indicadores

- **Producción [Simulado]:** lotes mensuales calibrados con la demanda base de cada línea (±15%).
- **Defectos [Simulado]:** entre 1% y 5% por lote. El promedio queda cerca de la
  meta de 3%, así que cerca de la mitad de los lotes la supera. Motivos: costura,
  pegado de suela, talla y manchas.
- **Devoluciones [Simulado]:** entre el 20% y el 50% de los pares defectuosos
  llegan al cliente y vuelven. Son los defectos que más dañan la marca.
- **Entregas: no hay datos.** El sistema no registra fechas de despacho ni de
  entrega, así que no se puede medir cumplimiento ni quiebres de stock por demora.
- **Ventas [Simulado]:** 30 días de demo en 3 tiendas. Alcanzan para el control
  diario, no para ver tendencias.
- **Margen de catálogo [Supuesto, precios de la demo]:** cerca del 45% en las tres
  líneas, pero por par el Cuero deja unos 239 Bs, frente a unos 155 Bs de
  Deportivo y de Caucho y cuero.

### Qué falta para estimar costos y rentabilidad

Costos reales por lote (insumos, mano de obra, energía); costos fijos de planta y
tiendas; costo de cada devolución (flete, reproceso, reposición); gastos de
almacenamiento y distribución por ciudad; precio real de venta con descuentos; y
fechas de entrega prometidas frente a reales.

### Las 2 alternativas comparadas

| | **Alternativa A — Competir por precio** | **Alternativa B — Diferenciar por calidad en Cuero** |
| --- | --- | --- |
| Acción | Bajar el precio para cerrar la brecha frente al mercado informal. | Mantener el precio; control de calidad por lote y garantía en la línea Cuero. |
| Beneficio esperado | Recuperar volumen frente al calzado informal. | Menos devoluciones y reprocesos; marca más fuerte en la línea de mayor valor por par. |
| Costo | Con un margen cercano al 45%, bajar el precio 10% obliga a vender **~29% más pares** solo para mantener la utilidad bruta. | Inspección por lote, capacitación en costura y pegado, y stock de tallas centrales. Se cuantifica con costos reales. |
| Indicador | Brecha frente al mercado informal (meta ≤20%). | Tasa de defectos (≤3%) y devoluciones de Cuero. |
| Control | Bajo: la brecha depende del tipo de cambio paralelo. | Alto: son procesos internos. |
| Riesgo principal | Guerra de precios contra un competidor sin costos formales. | Que la garantía no se perciba si no se comunica. |

**Cálculo del costo de A:** con precio 100 y costo 55, el margen es 45. Con precio
90, el margen baja a 35. Para mantener la misma utilidad bruta hay que vender
45 ÷ 35 = 1,29 veces más pares.

### Recomendación: Alternativa B

Cerrar la brecha de precio es una carrera que Manaco no controla: depende del tipo
de cambio paralelo y el competidor informal no paga impuestos ni planilla. Además,
la aritmética es exigente: un 10% menos de precio exige casi un 30% más de volumen
solo para quedar igual. La calidad, en cambio, es una palanca interna, y el Cuero
es la línea donde el mercado paga más por par.

### Segmento y acción comercial

- **Segmento [Supuesto]:** adultos que trabajan en oficinas o servicios y compran
  calzado de cuero de vestir en las tiendas de La Paz, Cochabamba y Santa Cruz.
- **Por qué:** el Cuero tiene el mayor valor por par del mercado de referencia
  (~41–45 USD), la menor presión importada (importa 1,52 veces lo que exporta,
  frente a 2,97 veces de Deportivo) y el mayor margen por par del catálogo. Falta
  validarlo con datos de clientes.
- **Acción:** lanzar *Cuero garantizado*: garantía de 6 meses en costura y suela,
  control de calidad de cada lote antes de enviarlo a tienda y stock asegurado de
  tallas centrales en las 3 tiendas, comunicado en tienda y en canales digitales.

### 3 indicadores de seguimiento

1. **Tasa de defectos y devoluciones de la línea Cuero** (meta ≤3% de defectos) — `fact_calidad`.
2. **Ventas de la línea Cuero** en pares y Bs frente a los 3 meses previos — Ventas / Tablero.
3. **% de cierres de inventario correctos por tienda** — Historial / Inicio.

---

*Nota: las cifras de comercio exterior son reales y ya están limpias en el sistema.
Las de ventas e inventario vienen de la demo, y las de producción, calidad, mercado
local y precios de catálogo están explícitamente etiquetadas **[Simulado]** o
**[Supuesto]**. Antes de usar los objetivos y
recomendaciones de este documento para comprometer presupuesto real, reemplace esos
datos simulados por historia real de Manaco (ver "Próximos pasos" en el README).*
